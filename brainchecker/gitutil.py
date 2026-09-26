"""Thin wrappers around git. Read-only: brainchecker never writes to the target's history."""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


def git(root: Path, *args: str, check: bool = True) -> str:
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                       errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def head(root: Path) -> str:
    return git(root, "rev-parse", "--short", "HEAD").strip()


def branch(root: Path) -> str:
    return git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()


def tracked(root: Path) -> list[str]:
    return [p for p in git(root, "ls-files").splitlines() if p]


@dataclass
class Hunk:
    path: str
    old_start: int
    new_start: int
    removed: list[str] = field(default_factory=list)
    added: list[tuple[int, str]] = field(default_factory=list)     # (new line number, text)
    context: list[tuple[int, str]] = field(default_factory=list)
    new_file: bool = False
    deleted_file: bool = False
    header: str = ""                                               # the function git names


_HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@ ?(.*)$")


def parse_diff(text: str) -> list[Hunk]:
    hunks: list[Hunk] = []
    path, new_file, deleted = None, False, False
    cur: Hunk | None = None
    new_ln = 0
    for line in text.splitlines():
        if line.startswith("diff --git "):
            path, new_file, deleted, cur = None, False, False, None
            continue
        if line.startswith("new file mode"):
            new_file = True; continue
        if line.startswith("deleted file mode"):
            deleted = True; continue
        if line.startswith("+++ "):
            p = line[4:]
            path = p[2:] if p.startswith("b/") else (None if p == "/dev/null" else p)
            continue
        if line.startswith("--- "):
            if deleted:
                p = line[4:]
                path = p[2:] if p.startswith("a/") else p
            continue
        m = _HUNK.match(line)
        if m:
            if path is None:
                continue
            cur = Hunk(path=path, old_start=int(m.group(1)), new_start=int(m.group(2)),
                       new_file=new_file, deleted_file=deleted, header=m.group(3).strip())
            hunks.append(cur)
            new_ln = cur.new_start
            continue
        if cur is None:
            continue
        if line.startswith("+"):
            cur.added.append((new_ln, line[1:])); new_ln += 1
        elif line.startswith("-"):
            cur.removed.append(line[1:])
        elif line.startswith(" "):
            cur.context.append((new_ln, line[1:])); new_ln += 1
    return hunks


def staged_diff(root: Path) -> list[Hunk]:
    return parse_diff(git(root, "diff", "--cached", "-U3", "--no-color", "--no-ext-diff"))


def range_diff(root: Path, rev_range: str) -> list[Hunk]:
    return parse_diff(git(root, "diff", "-U3", "--no-color", "--no-ext-diff", rev_range))


@lru_cache(maxsize=4096)
def blame_line(root: Path, path: str, line: int, rev: str | None = None, depth: int = 0) -> dict | None:
    """Commit, date, author and Claude trailer of the commit that last *wrote* a line.

    Folder renames that also edit files (human_m123's c9d54e32 swapped Model_3 and Model_4)
    defeat git's own rename detection, so blame lands on the rename commit. When the exact
    line already existed somewhere in that commit's parent, blame again from there.
    """
    try:
        args = ["blame", "--line-porcelain", "-L", f"{line},{line}"] + ([rev] if rev else []) + ["--", path]
        out = git(root, *args)
    except RuntimeError:
        return None
    lines = out.splitlines()
    if not lines:
        return None
    sha = lines[0].split()[0]
    info = {"commit": sha[:8]}
    text = next((l[1:] for l in lines if l.startswith("\t")), "")
    for l in lines[1:]:
        if l.startswith("author "):
            info["author"] = l[7:]
        elif l.startswith("author-time "):
            import datetime as _dt
            info["date"] = _dt.datetime.fromtimestamp(int(l[12:])).strftime("%Y-%m-%d")
        elif l.startswith("summary "):
            info["summary"] = l[8:]
    if set(sha) == {"0"}:
        return info
    info["claude_trailer"] = _has_claude_trailer(root, sha)
    if depth < 3 and len(text.strip()) >= 14:
        hit = _find_in_parent(root, sha, text, path)
        if hit:
            older = blame_line(root, hit[0], hit[1], sha + "^", depth + 1)
            if older:
                older["moved_by"] = f"{sha[:8]} ({info.get('summary', '')[:40]})"
                return older
    return info


def _find_in_parent(root: Path, sha: str, text: str, path: str) -> tuple[str, int] | None:
    """The file:line holding this exact line in sha^ (same basename first)."""
    ext = path.rsplit(".", 1)[-1] if "." in path else ""
    cands = [path] + sorted(g for g in _gone_in(root, sha) if not ext or g.endswith("." + ext))
    out = git(root, "grep", "-n", "-I", "-F", "-e", text, f"{sha}^", "--", *cands[:400], check=False)
    hits = []
    for l in out.splitlines():
        parts = l.split(":", 3)                       # rev:path:line:text
        if len(parts) == 4 and parts[2].isdigit() and parts[3] == text:
            hits.append((parts[1], int(parts[2])))
    if not hits:
        return None
    base = path.rsplit("/", 1)[-1]
    same = [h for h in hits if h[0] == path] or [h for h in hits if h[0].rsplit("/", 1)[-1] == base]
    return (same or hits)[0]


@lru_cache(maxsize=256)
def _gone_in(root: Path, sha: str) -> frozenset:
    out = git(root, "show", "--format=", "--name-status", "-M", sha, check=False)
    gone = set()
    for l in out.splitlines():
        parts = l.split("\t")
        if parts and (parts[0] == "D" or parts[0].startswith("R")) and len(parts) >= 2:
            gone.add(parts[1])
    return frozenset(gone)


@lru_cache(maxsize=2048)
def _has_claude_trailer(root: Path, sha: str) -> bool:
    body = git(root, "log", "-1", "--format=%B", sha, check=False)
    return bool(re.search(r"Co-Authored-By:\s*Claude", body, re.I))


def grep_word(root: Path, word: str, max_hits: int = 400) -> list[tuple[str, int, str]]:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_!]*", word or ""):
        return []
    out = git(root, "grep", "-n", "-w", "-I", "-F", "--", word, check=False)
    hits = []
    for l in out.splitlines()[:max_hits]:
        parts = l.split(":", 2)
        if len(parts) == 3 and parts[1].isdigit():
            hits.append((parts[0], int(parts[1]), parts[2]))
    return hits
