"""Per-change checks: what a staged change (or a commit) decides, and at which level.

Friction 1 (form §6): this never asks and never blocks. The pre-commit hook prints the
report and exits 0; the post-commit hook records the commit's decisions in the ledger and
starts the automatic notes and the instant checks in the background.

A change is cut into decisions by the same rules as the review (rules.py), plus the three
patterns the form says to flag wherever they appear:
  - a comment or docstring that states a number or a finding,
  - a deleted gate (assert / error / threshold removed and not put back),
  - a different function sequence in the plotter ("marks existence of new slop").
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

from . import checks, gitutil, ledger, provenance, rules
from .reach import Reach

CODE_LANGS = ("julia", "python", "shell", "config", "prose")
LEVELS = [("unexamined", True), ("unexamined", False), ("examined", True), ("examined", False)]
LEVEL_TITLE = {("unexamined", True): "UNEXAMINED · CRITICAL", ("unexamined", False): "unexamined · passable",
               ("examined", True): "examined · critical", ("examined", False): "examined · passable"}


def _file_lines(root: Path, path: str, rev: str | None) -> list[str]:
    try:
        if rev is None:                         # the index (what is about to be committed)
            return gitutil.git(root, "show", f":{path}", check=False).splitlines()
        return gitutil.git(root, "show", f"{rev}:{path}", check=False).splitlines()
    except Exception:
        return []


def analyse(target, hunks: list[gitutil.Hunk], rev: str | None = None,
            tindex: provenance.TranscriptIndex | None = None, with_reach: bool = True) -> list[dict]:
    """Decisions in a list of hunks. rev=None reads the index; otherwise the commit."""
    root = target.root
    reach = Reach(target) if with_reach else None
    out: dict[str, dict] = {}
    file_cache: dict[str, list[str]] = {}
    trailer = bool(rev) and gitutil._has_claude_trailer(root, gitutil.git(root, "rev-parse", rev).strip())

    def lines_of(path):
        if path not in file_cache:
            file_cache[path] = _file_lines(root, path, rev)
        return file_cache[path]

    def add(path, ln, text, kind, sigs, extra, hunk):
        fl = lines_of(path)
        generated = "generated" in target.path_level(path)[1]
        crit, reasons, lvl, row = rules.criticality(target, path, sigs, extra, generated)
        sym = next((s.symbol for s in sigs if s.symbol), None)
        did = rules.decision_id(path, kind, sym or text)
        if did in out:
            return
        prov = provenance.provenance(target, tindex, path, ln, text, fl, staged=True)
        if rev and prov["who"] == "presumed-ai" and trailer:
            prov.update(who="ai", evidence=[f"commit {rev[:8]} carries Co-Authored-By: Claude"])
        exam = provenance.examination(fl, ln, "", sym, path)
        d = {"id": did, "file": path, "line": ln, "text": text.strip()[:240], "kind": kind,
             "pillar": target.pillar(path), "signatures": sorted({s.kind for s in sigs}) or [kind],
             "detail": "; ".join(dict.fromkeys(s.detail for s in sigs if s.detail)),
             "symbol": sym, "critical": crit, "rules_critical": crit, "reasons": reasons,
             "path_level": lvl, "provenance": prov, "examined": exam,
             "context": "\n".join(f"{i:5d}  {fl[i - 1]}" for i in range(max(1, (ln or 1) - 5), min(len(fl), (ln or 1) + 5) + 1)),
             "diff": _hunk_text(hunk)[:1600],
             "checks": [{"id": c["id"], "title": c["title"], "cost": c.get("cost")} for c in checks.applicable(target, path)]}
        if reach:
            d["reach"] = reach.trace(path, sym, ln)
        out[did] = d

    for h in hunks:
        path = h.path
        language = rules.lang(path)
        if language not in CODE_LANGS or h.deleted_file:
            continue
        pillar = target.pillar(path)
        level, _ = target.path_level(path)
        if h.new_file and (pillar in ("modelling", "fitting", "plotting", "comparison") or level == "critical"):
            add(path, 1, f"new file {path} ({len(h.added)} lines)", "new-file",
                [rules.Sig("new-file", 1, path)], [], h)
        added_code = set()
        matched_lines = set()
        for ln, raw in h.added:
            sigs = []
            if language == "prose":
                rules._prose(sigs, ln, raw.strip())
            else:
                sigs = rules.scan_code_line(path, ln, raw, language)
                c = rules.comment_part(raw, language)
                if c:
                    rules._prose(sigs, ln, c)
            added_code.add(rules.strip_strings(rules.code_part(raw, language)).strip())
            if not sigs:
                continue
            matched_lines.add(ln)
            kind = rules.primary_kind(sigs)
            extra = []
            if any(s.kind == "claim" for s in sigs):
                extra.append("flag: a comment or docstring that states a number or a finding")
            add(path, ln, raw, kind, sigs, extra, h)
        # deleted gates
        for raw in h.removed:
            if language == "prose":
                continue
            code = rules.strip_strings(rules.code_part(raw, language)).strip()
            if code and code not in added_code and (rules.RE_GATE.search(code) or rules.RE_COND.search(code)):
                ln = h.new_start
                add(path, ln, f"removed: {raw.strip()}", "rule",
                    [rules.Sig("rule", ln, raw.strip(), detail="deleted gate", gate=True)],
                    ["flag: a deleted gate or check"], h)
        # a different function sequence in the plotter
        if path.startswith("plotter/") and language == "julia":
            before = rules.call_sequence(h.removed)
            after = rules.call_sequence([t for _, t in h.added])
            if before != after and (before or after) and set(before) != set(after):
                new = [c for c in after if c not in before]
                gone = [c for c in before if c not in after]
                ln = h.added[0][0] if h.added else h.new_start
                desc = "call sequence " + ", ".join([f"+{c}" for c in dict.fromkeys(new)][:4] + [f"-{c}" for c in dict.fromkeys(gone)][:4])
                add(path, ln, desc, "code", [rules.Sig("code", ln, desc, detail="plotter call sequence")],
                    ["flag: a different function sequence in the plotter"], h)
        # safety net: other non-trivial code in a critical-by-default file
        if level == "critical" and language != "prose":
            rest = [(ln, t) for ln, t in h.added if ln not in matched_lines and not rules.trivial(t)
                    and rules.code_part(t, language).strip()]
            if rest and not h.new_file:
                ln, t = rest[0]
                add(path, ln, t if len(rest) == 1 else f"{t.strip()}  (+{len(rest) - 1} more lines in this hunk)",
                    "code", [rules.Sig("code", ln, t)], [], h)
    return list(out.values())


def _hunk_text(h: gitutil.Hunk) -> str:
    return "\n".join([h.header] + [f"-{t}" for t in h.removed] + [f"+{t}" for _, t in h.added])


def level_of(d: dict) -> tuple[str, bool]:
    return ("examined" if d.get("examined") else "unexamined", bool(d.get("critical")))


def report(target, decisions: list[dict], title: str, cached_notes: bool = True) -> str:
    if not decisions:
        return f"brainchecker · {title}: no decisions in this change (nothing to record).\n"
    by = {lv: [d for d in decisions if level_of(d) == lv] for lv in LEVELS}
    counts = " · ".join(f"{len(by[lv])} {LEVEL_TITLE[lv].lower()}" for lv in LEVELS if by[lv])
    out = [f"brainchecker · {title}: {len(decisions)} decisions — {counts}",
           "  (this report never blocks; Claude-written lines count as unexamined until you mark them)"]
    for lv in LEVELS:
        if not by[lv]:
            continue
        out.append(f"\n{LEVEL_TITLE[lv]}")
        for d in sorted(by[lv], key=lambda d: (d["file"], d["line"] or 0))[:25]:
            who = d["provenance"].get("who")
            who_s = {"ai": "Claude", "human": "you", "presumed-ai": "presumed AI"}.get(who, who)
            out.append(f"  {d['file']}:{d['line']}  [{d['kind']}] {d['text'][:90]}")
            bits = [f"by {who_s}"]
            if d.get("reasons"):
                bits.append(d["reasons"][0])
            r = d.get("reach") or {}
            if r.get("models") or r.get("decks_total"):
                bits.append(f"reaches {','.join(r.get('models', [])) or '-'}; {r.get('decks_total', 0)} decks"
                            + (f"; {', '.join(r['documents'])}" if r.get("documents") else ""))
            out.append("      " + " · ".join(bits))
            if d.get("examined"):
                out.append(f"      examined: {d['examined'].get('rationale', '')[:100]}")
        if len(by[lv]) > 25:
            out.append(f"  … and {len(by[lv]) - 25} more (bc status)")
    drift = [x for x in checks.copy_drift(target, [d["file"] for d in decisions]) if x.get("differing_lines")]
    for x in drift:
        out.append(f"\ncopy drift: {x['pair']} differ on {x['differing_lines']} "
                   f"{'functions' if 'shared_functions' in x else 'lines'}")
    out.append("\nTo mark one: put `# examined: <how you checked it>` or `# human: <why>` on or next to the line,"
               "\nor comment on it on the site. Notes for critical decisions are written after the commit.")
    return "\n".join(out) + "\n"


# ---- hooks -------------------------------------------------------------------------------------
def pre_commit(target) -> int:
    try:
        hunks = gitutil.staged_diff(target.root)
        tindex = provenance.TranscriptIndex(target.transcripts, target.ledger_dir / "cache")
        tindex.refresh()
        ds = analyse(target, hunks, rev=None, tindex=tindex)
        text = report(target, ds, "staged change")
        (target.ledger_dir / "staged.md").write_text(text)
        sys.stderr.write(text)
    except Exception as e:                                   # never block a commit
        sys.stderr.write(f"brainchecker: pre-commit report failed ({e}); commit goes ahead\n")
    return 0


def record_commit(target, sha: str = "HEAD") -> list[dict]:
    root = target.root
    full = gitutil.git(root, "rev-parse", sha).strip()
    parents = gitutil.git(root, "rev-list", "--parents", "-n", "1", full).split()[1:]
    rng = f"{parents[0]}..{full}" if parents else full
    hunks = gitutil.range_diff(root, rng) if parents else gitutil.parse_diff(
        gitutil.git(root, "show", "-U3", "--no-color", "--format=", full))
    tindex = provenance.TranscriptIndex(target.transcripts, target.ledger_dir / "cache")
    tindex.refresh()
    ds = analyse(target, hunks, rev=full, tindex=tindex)
    meta = gitutil.git(root, "log", "-1", "--format=%an%x09%aI%x09%s", full).strip().split("\t")
    with ledger.locked(target.ledger_dir):
        _merge_commit(target, ds, full, meta)
    (target.ledger_dir / "last_commit.md").write_text(report(target, ds, f"commit {full[:8]}"))
    return ds


def _merge_commit(target, ds, full, meta):
    doc = ledger.load(target.ledger_dir)
    doc.setdefault("decisions", [])
    ids = {d["id"]: i for i, d in enumerate(doc["decisions"])}
    for d in ds:
        d["source"] = f"change:{full[:8]}"
        d["commit"] = {"sha": full[:8], "author": meta[0], "when": meta[1], "subject": meta[2] if len(meta) > 2 else ""}
        d.pop("diff", None) if len(d.get("diff", "")) > 4000 else None
        if d["id"] in ids:
            old = doc["decisions"][ids[d["id"]]]
            d["history"] = old.get("history", []) + [old.get("commit") or {"source": old.get("source")}]
            if old.get("note"):
                d["prior_note"] = old["note"]
            doc["decisions"][ids[d["id"]]] = {**old, **d, "source": old.get("source") if old.get("source") == "form" else d["source"]}
        else:
            doc["decisions"].append(d)
    doc.setdefault("commits", []).append({"sha": full[:8], "when": meta[1], "author": meta[0],
                                          "subject": meta[2] if len(meta) > 2 else "", "decisions": [d["id"] for d in ds]})
    ledger.refresh_statuses(doc, ledger.comments(target.ledger_dir))
    ledger.save(target.ledger_dir, doc)
    ledger.write_status_md(target.ledger_dir, doc)


def post_commit(target) -> int:
    """Record the commit, then detach the slow part (notes, instant checks)."""
    try:
        ds = record_commit(target)
        crit = [d["id"] for d in ds if d.get("critical")]
        if crit and target.notes.get("automatic"):
            log = target.ledger_dir / "background.log"
            with log.open("a") as fh:
                fh.write(f"\n== {dt.datetime.now():%Y-%m-%d %H:%M:%S} notes for {len(crit)} decisions\n")
            subprocess.Popen([sys.executable, "-m", "brainchecker", "--target", target.name, "notes", "--ids", *crit],
                             cwd=str(target.home), stdout=log.open("a"), stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL, start_new_session=True,
                             env={**os.environ, "PYTHONPATH": str(target.home)})
        sys.stderr.write(f"brainchecker: recorded {len(ds)} decisions ({len(crit)} critical)"
                         + ("; notes are being written in the background" if crit and target.notes.get("automatic") else "")
                         + "\n")
    except Exception as e:
        sys.stderr.write(f"brainchecker: post-commit record failed ({e})\n")
    return 0
