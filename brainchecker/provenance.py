"""Who wrote a line, and has anyone examined it.

Presumption (form §5): every line is AI-written and unexamined unless there is evidence
otherwise. Evidence, strongest first:

  declared   the author said so: a `# human:` mark, or the protocol form's "Mine" answer
  ai         a Claude Code transcript shows Claude writing this exact line (with the
             prompt that led to it), or the commit carries a Co-Authored-By: Claude trailer
  baseline   the line dates from the pre-AI baseline (on or before `pre_ai_until`), or sits
             in a folder imported untouched (Celia's models)

Examination is separate: an `# examined:` mark near the line, a DECISIONS.md entry, a
site comment of kind "examined", or the form answer. Nothing else counts (form §2).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import time
from pathlib import Path

from . import gitutil

RE_MARK = re.compile(r"#\s*(human|examined)\s*:\s*(.*)$", re.I)
MIN_LEN = 14                     # shorter lines match too many edits to mean anything


def _norm(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def _h(line: str) -> str:
    return hashlib.sha1(_norm(line).encode()).hexdigest()[:16]


class TranscriptIndex:
    """Lines Claude Code wrote into this project, keyed by line hash, with the prompt.

    Built from ~/.claude/projects/<project>/*.jsonl (Edit/Write/MultiEdit/NotebookEdit tool
    calls). Stored as SQLite in the ledger's cache; rebuilt incrementally by file mtime.
    """

    def __init__(self, transcripts: Path | None, cache: Path):
        self.dir = transcripts
        self.db_path = cache / "transcripts.sqlite"
        cache.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.db_path)
        self.db.executescript(
            "create table if not exists files(name text primary key, mtime real, size int);"
            "create table if not exists prompts(id integer primary key, session text, ts text, text text);"
            "create table if not exists lines(h text, base text, prompt int, tool text);"
            "create index if not exists lines_h on lines(h);")

    def refresh(self, verbose: bool = False) -> int:
        if not self.dir or not self.dir.is_dir():
            return 0
        done = {r[0]: (r[1], r[2]) for r in self.db.execute("select name, mtime, size from files")}
        n = 0
        for f in sorted(self.dir.rglob("*.jsonl")):          # subagents/ too
            st = f.stat()
            old = done.get(f.name)
            if old == (st.st_mtime, st.st_size):
                continue
            if old and st.st_size > old[1]:
                # transcripts are append-only: read only the new tail (the live session
                # grows by megabytes, and the pre-commit hook has to stay fast)
                n += self._ingest(f, offset=old[1])
            else:
                self.db.execute("delete from lines where prompt in (select id from prompts where session = ?)", (f.stem,))
                self.db.execute("delete from prompts where session = ?", (f.stem,))
                n += self._ingest(f)
            self.db.execute("insert or replace into files values (?,?,?)", (f.name, st.st_mtime, st.st_size))
            self.db.commit()
            if verbose:
                print(f"  indexed {f.name}")
        return n

    def _ingest(self, f: Path, offset: int = 0) -> int:
        prompt_id, n = None, 0
        if offset:
            prompt_id = self.db.execute("select max(id) from prompts where session = ?", (f.stem,)).fetchone()[0]
        with f.open("rb") as fh:
            fh.seek(offset)
            for rawb in fh:
                raw = rawb.decode("utf-8", errors="replace")
                try:
                    d = json.loads(raw)
                except Exception:
                    continue
                msg = d.get("message") if isinstance(d.get("message"), dict) else None
                if not msg:
                    continue
                if d.get("type") == "user":
                    text = _user_text(msg.get("content"))
                    if text:
                        cur = self.db.execute("insert into prompts(session, ts, text) values (?,?,?)",
                                              (f.stem, d.get("timestamp", ""), text[:600]))
                        prompt_id = cur.lastrowid
                    continue
                if d.get("type") != "assistant" or not isinstance(msg.get("content"), list):
                    continue
                for part in msg["content"]:
                    if not isinstance(part, dict) or part.get("type") != "tool_use":
                        continue
                    inp = part.get("input") or {}
                    name = part.get("name")
                    # (new text, old text): an Edit's new_string repeats unchanged context
                    # lines from old_string; only the lines it adds were written by Claude
                    pairs = []
                    if name == "Edit":
                        pairs = [(inp.get("new_string", ""), inp.get("old_string", ""))]
                    elif name == "Write":
                        pairs = [(inp.get("content", ""), "")]
                    elif name == "MultiEdit":
                        pairs = [(e.get("new_string", ""), e.get("old_string", "")) for e in inp.get("edits", [])]
                    elif name == "NotebookEdit":
                        pairs = [(inp.get("new_source", ""), "")]
                    if not pairs:
                        continue
                    base = os.path.basename(inp.get("file_path") or inp.get("notebook_path") or "")
                    rows = set()
                    for new, old in pairs:
                        before = {_norm(l) for l in (old or "").splitlines()}
                        rows |= {(_h(l), base, name) for l in (new or "").splitlines()
                                 if len(_norm(l)) >= MIN_LEN and _norm(l) not in before}
                    self.db.executemany("insert into lines values (?,?,?,?)", [(h, b, prompt_id, t) for h, b, t in rows])
                    n += len(rows)
        return n

    def lookup(self, line: str, base: str | None = None) -> dict | None:
        if len(_norm(line)) < MIN_LEN:
            return None
        rows = self.db.execute(
            "select l.base, p.session, p.ts, p.text, l.tool from lines l left join prompts p on p.id = l.prompt "
            "where l.h = ? order by (l.base = ?) desc, (l.tool = 'Write') asc, p.ts asc limit 1",
            (_h(line), base or "")).fetchall()
        if not rows:
            return None
        b, session, ts, text, tool = rows[0]
        return {"session": session, "when": (ts or "")[:16].replace("T", " "), "file": b, "tool": tool,
                "prompt": _clean_prompt(text or "")}


def _user_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
        return "\n".join(parts)
    return ""


def _clean_prompt(t: str) -> str:
    t = re.sub(r"<system-reminder>.*?</system-reminder>", "", t, flags=re.S)
    t = re.sub(r"<[^>]{1,60}>", "", t)
    return re.sub(r"\s+", " ", t).strip()[:300]


def marks_near(lines: list[str], idx: int, span: int = 4) -> dict:
    """`# human:` / `# examined:` marks within `span` lines of a 0-based index."""
    found = {}
    for j in range(max(0, idx - span), min(len(lines), idx + span + 1)):
        m = RE_MARK.search(lines[j])
        if m:
            found[m.group(1).lower()] = m.group(2).strip()
    return found


def provenance(target, tindex: TranscriptIndex | None, path: str, line_no: int | None,
               text: str, file_lines: list[str] | None = None, staged: bool = False) -> dict:
    out = {"who": "presumed-ai", "evidence": []}
    if file_lines is not None and line_no:
        mk = marks_near(file_lines, line_no - 1)
        if "human" in mk:
            out.update(who="human", evidence=[f"# human: {mk['human']}"])
            return out
    hit = tindex.lookup(text, os.path.basename(path)) if tindex else None
    if hit:
        out.update(who="ai", transcript=hit,
                   evidence=[(f"Claude Code added this line in an edit" if hit.get("tool") != "Write"
                              else f"Claude Code wrote the file this line is in")
                             + f" (session {hit['session'][:8]}, {hit['when']})"])
        return out
    if target.human_dir(path):
        out.update(who="human", evidence=["imported untouched from Celia's notebooks"])
        return out
    if not staged and line_no:
        b = gitutil.blame_line(target.root, path, line_no)
        if b:
            out["blame"] = b
            if b.get("claude_trailer"):
                out.update(who="ai", evidence=[f"commit {b['commit']} carries Co-Authored-By: Claude"])
            elif b.get("date", "9999") <= target.raw.get("pre_ai_until", "0000"):
                out.update(who="human", evidence=[f"pre-AI baseline (commit {b['commit']}, {b['date']})"])
            else:
                out["evidence"].append(f"last touched {b.get('date')} in {b['commit']} ({b.get('summary', '')[:50]}); no AI record either way")
    return out


def examination(file_lines: list[str] | None, line_no: int | None, decisions_md: str = "",
                symbol: str | None = None, path: str | None = None) -> dict | None:
    if file_lines is not None and line_no:
        mk = marks_near(file_lines, line_no - 1)
        if "examined" in mk:
            return {"by": "mark", "rationale": mk["examined"]}
    if decisions_md and symbol and path and re.search(re.escape(path) + r".*\b" + re.escape(symbol) + r"\b", decisions_md):
        return {"by": "DECISIONS.md", "rationale": "entry names this file and symbol"}
    return None
