"""Target configuration: which repo, which paths are critical, which checks exist.

A target is one repository under brainchecker's care, described by
targets/<name>/target.toml. Nothing about brainphysio is hard-coded outside that file.
"""
from __future__ import annotations

import fnmatch
import os
import re
import tomllib
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent          # the brainchecker repo


def glob_to_re(glob: str) -> re.Pattern:
    """`**` crosses folders, `*` and `?` stay inside one path segment."""
    out, i = [], 0
    while i < len(glob):
        c = glob[i]
        if glob.startswith("**/", i):
            out.append("(?:.*/)?"); i += 3; continue
        if glob.startswith("**", i):
            out.append(".*"); i += 2; continue
        if c == "*":
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        elif c == "{":
            j = glob.index("}", i)
            out.append("(?:" + "|".join(re.escape(x) for x in glob[i + 1:j].split(",")) + ")")
            i = j
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")


@lru_cache(maxsize=None)
def _compiled(glob: str) -> re.Pattern:
    return glob_to_re(glob)


def matches(path: str, globs) -> bool:
    return any(_compiled(g).match(path) for g in globs)


@dataclass
class Target:
    name: str
    raw: dict
    root: Path                       # the target repository
    home: Path = HOME                # the brainchecker repository
    ledger_dir: Path = field(init=False)

    def __post_init__(self):
        self.ledger_dir = self.home / "ledger" / self.name
        self.ledger_dir.mkdir(parents=True, exist_ok=True)

    # ---- paths -----------------------------------------------------------------
    def expand(self, p: str) -> Path:
        return Path(os.path.expanduser(p))

    @property
    def transcripts(self) -> Path | None:
        t = self.raw.get("transcripts")
        return self.expand(t) if t else None

    @property
    def claim_dirs(self) -> list[Path]:
        return [self.expand(p) for p in self.raw.get("claim_dirs", [])]

    @property
    def plots_dir(self) -> Path | None:
        for d in self.raw.get("plots_dirs", []):
            if (self.root / d).is_dir():
                return self.root / d
        return None

    # ---- classification ---------------------------------------------------------
    def pillar(self, path: str) -> str:
        for p in self.raw.get("pillars", []):
            if matches(path, p["globs"]):
                return p["name"]
        return "other"

    def path_level(self, path: str) -> tuple[str, str]:
        """(level, form row) from the path map; ('unlisted', '') when no row matches."""
        for p in self.raw.get("paths", []):
            if matches(path, p["globs"]):
                return p["level"], p.get("row", "")
        return "unlisted", ""

    def model_id(self, path: str) -> str | None:
        best = None
        for folder, mid in self.raw.get("models", {}).items():
            if path == folder or path.startswith(folder + "/"):
                if best is None or len(folder) > len(best[0]):
                    best = (folder, mid)
        return best[1] if best else None

    def human_dir(self, path: str) -> bool:
        return any(path.startswith(d) for d in self.raw.get("human_dirs", []))

    @property
    def notes(self) -> dict:
        return self.raw.get("notes", {})

    @property
    def checks(self) -> list[dict]:
        return self.raw.get("checks", [])

    @property
    def pairs(self) -> list[dict]:
        return self.raw.get("pairs", [])

    @property
    def documents(self) -> list[dict]:
        return self.raw.get("documents", [])


def load(name: str = "brainphysio", repo: str | None = None) -> Target:
    path = HOME / "targets" / name / "target.toml"
    raw = tomllib.loads(path.read_text())
    root = Path(repo or raw["repo"]).expanduser().resolve()
    return Target(name=name, raw=raw, root=root)


def fnmatch_any(name: str, patterns) -> bool:
    return any(fnmatch.fnmatch(name, p) for p in patterns)
