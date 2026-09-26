"""The ledger: the decision-status document, as data (decisions.json) and as text (STATUS.md).

Comments come from the website (synced by Claude from the artifact's database) or from
`bc comment`. A comment of kind "examined" or "mine" from Thomas changes a decision's
status; every other kind is discussion. The form answer is the starting point for the
32 decisions he classified.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import fcntl
import json
from collections import Counter, defaultdict
from pathlib import Path

FORM_STATUS = {
    "Mine — not slop": "mine",
    "Examined · critical": "examined-critical",
    "Examined · passable": "examined-passable",
    "Unexamined · critical": "unexamined-critical",
    "Unexamined · passable": "unexamined-passable",
    "Don't know": "dont-know",
}
STATUS_LABEL = {
    "unexamined-critical": "Unexamined · critical",
    "unexamined-passable": "Unexamined · passable",
    "examined-critical": "Examined · critical",
    "examined-passable": "Examined · passable",
    "dont-know": "Don't know",
    "mine": "Mine",
    "human": "Human (evidence)",
    "not-a-decision": "Not a decision",
}
STATUS_ORDER = list(STATUS_LABEL)


@contextlib.contextmanager
def locked(ledger_dir: Path):
    """Serialise read-modify-write of decisions.json (the background notes run alongside hooks)."""
    with open(ledger_dir / ".lock", "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def load(ledger_dir: Path) -> dict:
    f = ledger_dir / "decisions.json"
    return json.loads(f.read_text()) if f.exists() else {"decisions": []}


def save(ledger_dir: Path, doc: dict):
    tmp = ledger_dir / "decisions.json.tmp"
    tmp.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    tmp.replace(ledger_dir / "decisions.json")


def comments(ledger_dir: Path) -> list[dict]:
    f = ledger_dir / "comments.jsonl"
    if not f.exists():
        return []
    out = []
    for line in f.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def add_comment(ledger_dir: Path, decision_id: str, text: str, kind: str = "comment",
                author: str = "Thomas", source: str = "cli", when: str | None = None, cid: str | None = None,
                owner: bool = True):
    c = {"id": cid or f"c-{dt.datetime.now():%Y%m%d%H%M%S%f}", "decision": decision_id, "kind": kind,
         "author": author, "owner": owner, "text": text, "source": source,
         "when": when or dt.datetime.now().isoformat(timespec="seconds")}
    existing = {x.get("id") for x in comments(ledger_dir)}
    if c["id"] in existing:
        return None
    with (ledger_dir / "comments.jsonl").open("a") as fh:
        fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    return c


def derive_status(d: dict, cmts: list[dict]) -> tuple[str, str]:
    """(status, why)."""
    # only the owner's marks change a status (form: once examined and justified it is his
    # decision); anyone else's "examined" stays a proposal in the thread
    mine = [c for c in cmts if c["decision"] == d["id"] and c.get("owner", True)
            and c["kind"] in ("examined", "mine", "reopen", "not-a-decision")]
    if mine:
        last = sorted(mine, key=lambda c: c["when"])[-1]
        crit = "critical" if d.get("critical") else "passable"
        if last["kind"] == "mine":
            return "mine", f"marked yours ({last['when'][:10]}): {last['text'][:100]}"
        if last["kind"] == "examined":
            return f"examined-{crit}", f"examined ({last['when'][:10]}): {last['text'][:120]}"
        if last["kind"] == "not-a-decision":
            return "not-a-decision", f"dismissed ({last['when'][:10]}): {last['text'][:100]}"
    if d.get("form"):
        return FORM_STATUS.get(d["form"], "dont-know"), f"your form answer, 26 Sep: {d['form']}"
    prov = d.get("provenance") or {}
    crit = "critical" if d.get("critical") else "passable"
    if d.get("examined"):
        return f"examined-{crit}", f"examined ({d['examined'].get('by')}): {d['examined'].get('rationale', '')[:100]}"
    if prov.get("who") == "human":
        return "human", "; ".join(prov.get("evidence", []))[:160]
    return f"unexamined-{crit}", "presumed AI-written, no examination on record"


def refresh_statuses(doc: dict, cmts: list[dict]):
    for d in doc["decisions"]:
        d["status"], d["status_why"] = derive_status(d, cmts)
        d["comments"] = [c for c in cmts if c["decision"] == d["id"]]
    doc["summary"] = summary(doc["decisions"])


def summary(decisions: list[dict]) -> dict:
    by = defaultdict(Counter)
    for d in decisions:
        by[d.get("pillar", "other")][d.get("status", "?")] += 1
    return {p: dict(c) for p, c in by.items()}


def write_status_md(ledger_dir: Path, doc: dict):
    lines = [f"# Decision status — {doc.get('target')}",
             "",
             f"Generated {doc.get('generated')} from `{doc.get('branch')}` @ {doc.get('commit')}. "
             f"{len(doc['decisions'])} decisions: the {sum(1 for d in doc['decisions'] if d['source'] == 'form')} "
             "you classified in the protocol form, a seeded sample per pillar, and every decision "
             "met since in a commit.", ""]
    pillars = ["modelling", "fitting", "plotting", "comparison"]
    lines += ["| pillar | " + " | ".join(STATUS_LABEL[s] for s in STATUS_ORDER) + " |",
              "|---|" + "---|" * len(STATUS_ORDER)]
    for p in pillars + sorted(set(doc.get("summary", {})) - set(pillars)):
        row = doc.get("summary", {}).get(p, {})
        if row:
            lines.append(f"| {p} | " + " | ".join(str(row.get(s, "")) for s in STATUS_ORDER) + " |")
    for p in pillars:
        ds = [d for d in doc["decisions"] if d.get("pillar") == p]
        if not ds:
            continue
        lines += ["", f"## {p.capitalize()}", ""]
        for d in sorted(ds, key=lambda d: (STATUS_ORDER.index(d["status"]) if d["status"] in STATUS_ORDER else 99, d["id"])):
            where = d.get("where_label") or f"{d.get('file')}:{d.get('line')}"
            lines.append(f"- **{d['id']}** [{STATUS_LABEL.get(d['status'], d['status'])}] {d.get('title') or d.get('text', '')[:100]}  ")
            lines.append(f"  `{where}` · {d.get('kind')} · {d.get('status_why', '')}")
            if d.get("note", {}).get("status") == "ok":
                lines.append(f"  Note (AI, not an examination): {d['note'].get('meaning', '')}")
            for c in d.get("comments", [])[-2:]:
                lines.append(f"  > {c['author']} ({c['kind']}, {c['when'][:10]}): {c['text'][:200]}")
    (ledger_dir / "STATUS.md").write_text("\n".join(lines) + "\n")
