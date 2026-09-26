"""Review: the whole-tree audit the form asked for.

"Sample 30 decisions per pillar first, then decide" (form §3). The review inventories
every decision signature in the four pillars, keeps the 32 decisions Thomas classified,
adds a seeded random sample of 30 per pillar (stratified by kind so rare kinds such as
equations and gates are not drowned by plot widths), and fills each with provenance,
reach, report evidence and the applicable checks.
"""
from __future__ import annotations

import datetime as dt
import math
import random
import re
import tomllib
from collections import Counter, defaultdict

from . import checks, evidence, gitutil, ledger, provenance, rules
from .reach import Reach

PILLARS = ("modelling", "fitting", "plotting", "comparison")
CODE_EXT = (".jl", ".py", ".sh", ".md", ".toml")


def context_of(lines: list[str], ln: int, span: int = 6) -> str:
    lo, hi = max(1, ln - span), min(len(lines), ln + span)
    return "\n".join(f"{i:5d}  {lines[i - 1]}" for i in range(lo, hi + 1))


def number_index(target, files: list[str], reports) -> dict[str, set[str]]:
    idx = defaultdict(set)
    for f in files:
        if not f.endswith((".jl", ".py", ".md", ".sh", ".toml", ".typ", ".tex")):
            continue
        try:
            text = (target.root / f).read_text(errors="replace")
        except OSError:
            continue
        for tok in set(re.findall(r"(?<![\w.])(\d+\.\d+|\d{3,})(?![\w.])", text)):
            idx[tok].add(f)
    for doc, lines in reports.texts.items():
        for tok in set(re.findall(r"(?<![\w.])(\d+\.\d+|\d{3,})(?![\w.])", "\n".join(lines))):
            idx[tok].add(f"report: {doc}")
    return idx


def in_scope(target, f: str) -> bool:
    if not f.endswith(CODE_EXT):
        return False
    if rules.lang(f) == "other":
        return False
    if target.pillar(f) not in PILLARS:
        return False
    lvl, row = target.path_level(f)
    return "generated" not in row


def build(target, sample: int = 30, seed: int = 20260926, verbose: bool = True) -> dict:
    root = target.root
    files = gitutil.tracked(root)
    reports = evidence.Reports(target)
    if verbose:
        print("reports:", ", ".join(reports.refresh()) or "none")
    tindex = provenance.TranscriptIndex(target.transcripts, target.ledger_dir / "cache")
    if verbose:
        print("transcripts: indexing Claude Code sessions…")
    added = tindex.refresh(verbose=False)
    if verbose:
        print(f"transcripts: {added} new line records")
    reach = Reach(target)
    nums = number_index(target, files, reports)
    decisions_md = ""
    for cand in ("DECISIONS.md", "docs/DECISIONS.md"):
        if (root / cand).is_file():
            decisions_md += (root / cand).read_text(errors="replace")

    # ---- known decisions (form) --------------------------------------------------------
    known = tomllib.loads((target.home / "targets" / target.name / "known.toml").read_text())["decision"]
    known_locs = set()
    out = []
    for k in known:
        where = k.get("where", [])
        d = {"id": k["id"], "source": "form", "pillar": k["pillar"], "title": k["title"],
             "form": k["form"], "evidence": k.get("evidence", []), "outside": k.get("outside"),
             "where": where, "where_label": ", ".join(where) or (k.get("outside") or "")[:80]}
        if where:
            f, ln = where[0].rsplit(":", 1)
            ln = int(ln)
            for w in where:
                ff, ll = w.rsplit(":", 1)
                known_locs.add((ff, int(ll)))
            lines = (root / f).read_text(errors="replace").splitlines() if (root / f).is_file() else []
            text = lines[ln - 1].strip() if 0 < ln <= len(lines) else ""
            sigs = rules.scan_code_line(f, ln, lines[ln - 1], rules.lang(f)) if text else []
            if not sigs and text:
                sigs = [s for s in rules.scan_text(f, "\n" * (ln - 1) + lines[ln - 1]) if s.line == ln]
            crit, reasons, lvl, row = rules.criticality(target, f, sigs)
            sym = next((s.symbol for s in sigs if s.symbol), None)
            d.update(file=f, line=ln, text=text, kind=rules.primary_kind(sigs) if sigs else "code",
                     signatures=[s.kind for s in sigs], symbol=sym,
                     rules_critical=crit, reasons=reasons, path_level=lvl,
                     context=context_of(lines, ln) if lines else "",
                     provenance=provenance.provenance(target, tindex, f, ln, text, lines),
                     reach=reach.trace(f, sym, ln),
                     checks=[{"id": c["id"], "title": c["title"], "cost": c.get("cost")} for c in checks.applicable(target, f)])
        else:
            d.update(file=None, line=None, text="", kind="outside", signatures=[], rules_critical=None,
                     reasons=[], provenance={"who": "unknown", "evidence": [k.get("outside", "")]}, reach={}, checks=[])
        d["critical"] = "critical" in k["form"] if "·" in k["form"] else bool(d.get("rules_critical"))
        out.append(d)

    # ---- inventory ------------------------------------------------------------------------
    inventory = defaultdict(list)
    for f in files:
        if not in_scope(target, f):
            continue
        try:
            text = (root / f).read_text(errors="replace")
        except OSError:
            continue
        per_line = defaultdict(list)
        for s in rules.scan_text(f, text):
            if s.kind == "claim":
                reused = [n for n in s.numbers if len(nums.get(n, set()) - {f}) > 0]
                if not reused:
                    continue
                s.detail = "claim reused: " + ", ".join(reused[:3])
            per_line[s.line].append(s)
        for ln, sigs in per_line.items():
            if (f, ln) in known_locs:
                continue
            inventory[target.pillar(f)].append((f, ln, sigs))

    counts = {p: dict(Counter(rules.primary_kind(s) for _, _, s in inventory[p])) for p in PILLARS}
    if verbose:
        for p in PILLARS:
            print(f"inventory {p:11s} {len(inventory[p]):5d} candidate lines  {counts[p]}")

    # ---- stratified sample ------------------------------------------------------------------
    rng = random.Random(seed)
    for p in PILLARS:
        pool = inventory[p]
        by_kind = defaultdict(list)
        for item in pool:
            by_kind[rules.primary_kind(item[2])].append(item)
        weights = {k: math.sqrt(len(v)) for k, v in by_kind.items()}
        tot = sum(weights.values()) or 1
        alloc = {k: max(1, round(sample * w / tot)) for k, w in weights.items()}
        while sum(alloc.values()) > sample:
            kmax = max(alloc, key=lambda k: alloc[k]); alloc[kmax] -= 1
        picked = []
        for k, items in sorted(by_kind.items()):
            picked += rng.sample(items, min(alloc.get(k, 0), len(items)))
        for f, ln, sigs in sorted(picked):
            lines = (root / f).read_text(errors="replace").splitlines()
            text = lines[ln - 1].strip()
            kind = rules.primary_kind(sigs)
            sym = next((s.symbol for s in sigs if s.symbol), None)
            extra = []
            if kind == "claim":
                extra.append("flag: a comment or docstring that states a number or a finding (reused)")
            generated = "generated" in target.path_level(f)[1]
            crit, reasons, lvl, row = rules.criticality(target, f, sigs, extra, generated)
            did = rules.decision_id(f, kind, sym or text)
            prov = provenance.provenance(target, tindex, f, ln, text, lines)
            exam = provenance.examination(lines, ln, decisions_md, sym, f)
            d = {"id": did, "source": "sample", "pillar": p, "file": f, "line": ln, "text": text,
                 "kind": kind, "signatures": sorted({s.kind for s in sigs}),
                 "detail": "; ".join(dict.fromkeys(s.detail for s in sigs if s.detail)),
                 "symbol": sym, "critical": crit, "rules_critical": crit, "reasons": reasons,
                 "path_level": lvl, "context": context_of(lines, ln), "provenance": prov,
                 "examined": exam, "reach": reach.trace(f, sym, ln),
                 "checks": [{"id": c["id"], "title": c["title"], "cost": c.get("cost")} for c in checks.applicable(target, f)]}
            d["evidence"] = reports.search(evidence.search_terms(d))
            out.append(d)

    doc = {"target": target.name, "generated": dt.datetime.now().isoformat(timespec="seconds"),
           "commit": gitutil.head(root), "branch": gitutil.branch(root), "seed": seed,
           "sample_per_pillar": sample,
           "inventory": {p: {"lines": len(inventory[p]), "by_kind": counts[p]} for p in PILLARS},
           "copy_drift": checks.copy_drift(target),
           "decisions": out}
    with ledger.locked(target.ledger_dir):
        _merge_and_save(target, doc)
    return doc


def _merge_and_save(target, doc):
    # keep decisions met in commits since the last review
    old = ledger.load(target.ledger_dir)
    doc["commits"] = old.get("commits", [])
    ids = {d["id"]: i for i, d in enumerate(doc["decisions"])}
    for d in old.get("decisions", []):
        if str(d.get("source", "")).startswith("change:"):
            if d["id"] in ids:
                i = ids[d["id"]]
                doc["decisions"][i] = {**d, **doc["decisions"][i], "commit": d.get("commit"),
                                       "history": d.get("history", [])}
            else:
                doc["decisions"].append(d)
    cm = ledger.comments(target.ledger_dir)
    for d in doc["decisions"]:
        prev = next((o for o in old.get("decisions", []) if o["id"] == d["id"]), None)
        if prev and prev.get("note"):
            d["note"] = prev["note"]
    ledger.refresh_statuses(doc, cm)
    ledger.save(target.ledger_dir, doc)
    ledger.write_status_md(target.ledger_dir, doc)
