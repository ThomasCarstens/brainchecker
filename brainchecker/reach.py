"""Reach: what a decision feeds. Deterministic — names, includes, the registry, the store.

It is an approximation and says so: a symbol grep can over-reach (same name, different
thing) and an include graph under-reaches (a path built at run time). The AI note may
add to it but never remove from it (protocol §4).
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from functools import cached_property
from pathlib import Path

from . import gitutil
from .config import matches

RE_INCLUDE = re.compile(r"^\s*include\((.+)\)\s*$")
RE_STR = re.compile(r"\"([^\"]+)\"")
RE_OUTDIR = re.compile(r"(?:modelplots|output)/([A-Za-z0-9_<>{}$.*-]+)")


class Reach:
    def __init__(self, target):
        self.t = target
        self.root = target.root

    @cached_property
    def files(self) -> list[str]:
        return gitutil.tracked(self.root)

    @cached_property
    def by_base(self) -> dict[str, list[str]]:
        d = defaultdict(list)
        for f in self.files:
            d[Path(f).name].append(f)
        return d

    @cached_property
    def includers(self) -> dict[str, set[str]]:
        """file -> files that include() it (Julia)."""
        rev = defaultdict(set)
        for f in self.files:
            if not f.endswith(".jl"):
                continue
            try:
                text = (self.root / f).read_text(errors="replace")
            except OSError:
                continue
            for line in text.splitlines():
                m = RE_INCLUDE.match(line.split("#")[0])
                if not m:
                    continue
                parts = RE_STR.findall(m.group(1))
                if not parts:
                    continue
                target = self._resolve(f, parts)
                if target:
                    rev[target].add(f)
        return rev

    def _resolve(self, includer: str, parts: list[str]) -> str | None:
        rel = "/".join(p for p in parts if p not in ("", "."))
        # joinpath(@__DIR__, "..", "x", "y.jl") — resolve against the includer's folder
        base = Path(includer).parent
        cand = (base / rel)
        try:
            norm = str(Path(*[p for p in cand.parts])).replace("\\", "/")
            norm = str((self.root / norm).resolve().relative_to(self.root.resolve()))
            if norm in self.by_base.get(Path(norm).name, []):
                return norm
        except (ValueError, OSError):
            pass
        name = Path(parts[-1]).name
        options = self.by_base.get(name, [])
        if len(options) == 1:
            return options[0]
        same = [o for o in options if Path(o).parent == base]
        return same[0] if same else None

    def entry_points(self, f: str, limit: int = 40) -> set[str]:
        seen, stack, entries = {f}, [f], set()
        while stack:
            cur = stack.pop()
            ups = self.includers.get(cur, set())
            if not ups and cur != f:
                entries.add(cur)
            for u in ups:
                if u not in seen:
                    seen.add(u); stack.append(u)
            if len(seen) > 400:
                break
        if not self.includers.get(f):
            entries.add(f)
        return set(sorted(entries)[:limit])

    @cached_property
    def decks(self) -> dict[str, set[str]]:
        """deck name -> model ids it draws (from each deck.json)."""
        out = {}
        pd = self.t.plots_dir
        if not pd:
            return out
        for dj in sorted(pd.glob("*/deck.json")):
            try:
                d = json.loads(dj.read_text())
            except Exception:
                continue
            out[dj.parent.name] = {r.get("model") for r in d.get("runs", []) if r.get("model")}
        return out

    @cached_property
    def store(self) -> dict[str, list[str]]:
        base = self.root / self.t.raw.get("store_dir", "simulations")
        out = defaultdict(list)
        if base.is_dir():
            for m in base.iterdir():
                if m.is_dir():
                    for exp in m.iterdir():
                        if exp.is_dir():
                            for var in exp.iterdir():
                                if var.is_dir():
                                    out[m.name].append(f"{exp.name}/{var.name}")
        return out

    def documents_for(self, decks: list[str]) -> list[str]:
        docs = []
        for doc in self.t.documents:
            if any(matches(d, doc["decks"]) for d in decks):
                docs.append(doc["name"])
        return docs

    def trace(self, path: str, symbol: str | None = None, line: int | None = None) -> dict:
        r: dict = {"method": "static: names, include() graph, registry ids, deck manifests; approximate"}
        refs = []
        if symbol and symbol not in ("clamp",) and len(symbol) >= 3:
            for f, ln, txt in gitutil.grep_word(self.root, symbol):
                if f == path and ln == line:
                    continue
                refs.append(f"{f}:{ln}")
        r["refs"] = refs[:14]
        r["refs_total"] = len(refs)
        ref_files = sorted({x.rsplit(":", 1)[0] for x in refs})
        entries = set()
        for f in [path] + ref_files[:25]:
            if f.endswith(".jl"):
                entries |= self.entry_points(f)
        r["entry_points"] = sorted(entries)[:16]
        models = set()
        for f in [path] + ref_files + sorted(entries):
            mid = self.t.model_id(f)
            if mid:
                models.add(mid)
        r["models"] = sorted(models)
        if path.startswith("plotter/") or any(e.startswith("plotter/") for e in [path]):
            decks = sorted(self.decks)
            r["decks_note"] = "the plotter draws every deck"
        else:
            decks = sorted(d for d, ms in self.decks.items() if ms & models)
        # scripts that write their own output folders
        try:
            text = (self.root / path).read_text(errors="replace") if (self.root / path).is_file() else ""
        except OSError:
            text = ""
        outs = sorted({m.group(1) for m in RE_OUTDIR.finditer(text)} - {"<deck>", "$DECK"})
        r["writes"] = outs[:8]
        r["decks"] = decks[:24]
        r["decks_total"] = len(decks)
        r["store_families"] = {m: len(self.store.get(m, [])) for m in r["models"]}
        r["documents"] = self.documents_for(decks)
        return r
