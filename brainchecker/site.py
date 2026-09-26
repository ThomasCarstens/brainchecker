"""The status website: the ledger rendered as one page, with a comment thread per decision.

The page embeds a snapshot of the ledger and keeps comments in the artifact's database
(`comments/<id>`), so they survive every republish. Nothing on the page subscribes live:
comments are read once on load and on Refresh, and written on Save. Claude folds them back
into the ledger with `bc sync-comments` (from an ArtifactData listing of `comments`).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import checks, ledger

TEMPLATE = Path(__file__).with_name("site_template.html")


def _missing_paths(target, cmd: str) -> list[str]:
    """Script paths in a suggested command that do not exist in the target repo."""
    dirs = [target.root] + [target.root / m for m in re.findall(r"\bcd\s+([\w./-]+)", cmd or "")]
    return [p for p in dict.fromkeys(re.findall(r"[\w./-]+\.(?:jl|py|sh)\b", cmd or ""))
            if not any((d / p.lstrip("./")).exists() for d in dirs)]


def _trim(d: dict, target=None) -> dict:
    r = d.get("reach") or {}
    prov = d.get("provenance") or {}
    t = prov.get("transcript") or {}
    out = {k: d.get(k) for k in ("id", "source", "pillar", "title", "text", "file", "line", "where_label",
                                 "kind", "critical", "reasons", "status", "status_why", "form", "examined",
                                 "context", "evidence", "checks", "detail", "outside", "commit", "history")}
    out["base_status"], out["base_why"] = ledger.derive_status(d, [])
    out["provenance"] = {"who": prov.get("who"), "evidence": prov.get("evidence", []),
                         "moved_by": (prov.get("blame") or {}).get("moved_by"),
                         "transcript": {"when": t.get("when"), "prompt": t.get("prompt")} if t else None}
    out["reach"] = {"models": r.get("models", []), "decks": r.get("decks", [])[:10],
                    "decks_total": r.get("decks_total", 0), "decks_note": r.get("decks_note"),
                    "documents": r.get("documents", []), "refs": r.get("refs", [])[:8],
                    "refs_total": r.get("refs_total", 0), "entry_points": r.get("entry_points", [])[:6],
                    "writes": r.get("writes", [])}
    n = d.get("note") or {}
    out["note"] = {k: n.get(k) for k in ("status", "model", "when", "meaning", "could_move", "expectation",
                                         "check", "confidence", "dropped_uncited")} if n.get("status") == "ok" else None
    if out["note"] and target is not None and out["note"].get("check"):
        out["note"]["check_missing"] = _missing_paths(target, out["note"]["check"].get("command"))
    out["comments"] = [{k: c.get(k) for k in ("id", "kind", "author", "owner", "text", "when")}
                       for c in d.get("comments", [])]
    return out


def build(target, out: str | None = None) -> Path:
    doc = ledger.load(target.ledger_dir)
    ledger.refresh_statuses(doc, ledger.comments(target.ledger_dir))
    notes = [d["note"] for d in doc["decisions"] if (d.get("note") or {}).get("status") == "ok"]
    data = {
        "meta": {"target": doc.get("target"), "generated": doc.get("generated"), "branch": doc.get("branch"),
                 "commit": doc.get("commit"), "seed": doc.get("seed"), "sample": doc.get("sample_per_pillar"),
                 "inventory": doc.get("inventory", {}),
                 "notes": {"count": len(notes), "cost": round(sum(float(n.get("cost_usd") or 0) for n in notes), 2),
                           "model": target.notes.get("model")},
                 "checks_latest": checks.latest_results(target)},
        "labels": ledger.STATUS_LABEL,
        "decisions": [_trim(d, target) for d in doc["decisions"]],
        "copy_drift": doc.get("copy_drift", []),
        "commits": doc.get("commits", [])[-40:],
    }
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text().replace("__BRAINCHECKER_DATA__", blob)
    path = Path(out) if out else target.home / "site" / "index.html"
    path.write_text(html)
    return path
