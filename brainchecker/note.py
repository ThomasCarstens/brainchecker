"""The consequence note: one short paragraph per critical decision, written by Claude Code.

Runs `claude -p` headless with no tools, a JSON schema, and no saved session (so the
note runs never show up in the transcripts provenance reads). Every note is cached by a
hash of its inputs and logged with its reported cost in spend.jsonl.

Guardrails (protocol §4): the note never counts as an examination; it may add to the
reach but never remove from it; a claim without a citation from the provided context is
dropped; it lives in the ledger and on the site, never in a code comment.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

PROMPT_VERSION = "note-v1"

SCHEMA = {
    "type": "object",
    "properties": {
        "meaning": {"type": "string", "description": "What this decision does, physically or methodologically, in at most two sentences."},
        "could_move": {"type": "array", "items": {"type": "object", "properties": {
            "what": {"type": "string"}, "cite": {"type": "string", "description": "file:line or deck name from the context"}},
            "required": ["what", "cite"]}},
        "expectation": {"type": "string", "description": "Direction or size of the effect if it can be inferred; say 'unknown' otherwise."},
        "check": {"type": "object", "properties": {"command": {"type": "string"}, "why": {"type": "string"}},
                  "required": ["command", "why"]},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": ["meaning", "could_move", "expectation", "check", "confidence"],
    "additionalProperties": False,
}

SYSTEM = """You write one consequence note about one decision in a scientific modelling repository
(0D craniospinal models in Julia/ModelingToolkit, fitted to patient recordings).
A human will read your note next to the code. Rules:
- Use only the code context, reach trace and prompt given. Do not invent files, numbers or results.
- Every item in could_move must cite a file:line or deck name that appears in the context or reach.
- Never say a change is safe or harmless. If you cannot tell, say so and lower the confidence.
- The check must be a single shell command runnable from the repository root, cheaper than a full
  re-fit where possible (a replot, a verify script, a one-case solve).
- Plain, short sentences."""


def _key(decision: dict, model: str) -> str:
    blob = json.dumps({"v": PROMPT_VERSION, "m": model, "f": decision.get("file"), "t": decision.get("text"),
                       "ctx": decision.get("context"), "reach": decision.get("reach")}, sort_keys=True)
    return hashlib.sha1(blob.encode()).hexdigest()[:16]


def build_prompt(decision: dict) -> str:
    r = decision.get("reach") or {}
    prov = decision.get("provenance") or {}
    lines = [
        f"Decision {decision['id']} ({decision.get('pillar')}, {decision.get('kind')}) in {decision.get('file')}"
        + (f":{decision['line']}" if decision.get("line") else ""),
        f"Why brainchecker flagged it: {'; '.join(decision.get('reasons') or []) or 'no critical condition'}",
        "", "Code context (line numbers are real):", decision.get("context") or decision.get("text", ""),
        "", "Reach trace (static, approximate):",
        f"  references: {', '.join(r.get('refs', [])) or 'none found'} (total {r.get('refs_total', 0)})",
        f"  entry points: {', '.join(r.get('entry_points', [])) or 'none'}",
        f"  models: {', '.join(r.get('models', [])) or 'none'}",
        f"  decks: {', '.join(r.get('decks', [])) or 'none'} (total {r.get('decks_total', 0)})",
        f"  documents fed: {', '.join(r.get('documents', [])) or 'none'}",
    ]
    if decision.get("diff"):
        lines += ["", "The staged change:", decision["diff"]]
    t = prov.get("transcript")
    if t:
        lines += ["", f"The prompt that led Claude Code to write it ({t.get('when')}): {t.get('prompt')}"]
    lines += ["", "Write the note as JSON matching the schema."]
    return "\n".join(lines)


def spent_today(ledger_dir: Path) -> float:
    f = ledger_dir / "spend.jsonl"
    if not f.exists():
        return 0.0
    today = dt.date.today().isoformat()
    total = 0.0
    for line in f.read_text().splitlines():
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("when", "").startswith(today):
            total += float(d.get("cost_usd") or 0)
    return total


def write_note(target, decision: dict, force: bool = False) -> dict | None:
    cfg = target.notes
    model = cfg.get("model", "claude-opus-5")
    notes_dir = target.ledger_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    key = _key(decision, model)
    out = notes_dir / f"{key}.json"
    if out.exists() and not force:
        return json.loads(out.read_text())
    cap = float(cfg.get("daily_cap_usd") or 0)
    if cap and spent_today(target.ledger_dir) >= cap:
        return {"status": "skipped", "reason": f"daily cap ${cap:.2f} reached"}
    cmd = ["claude", "-p", "--output-format", "json", "--model", model, "--tools", "",
           "--no-session-persistence", "--setting-sources", "project,local",
           "--json-schema", json.dumps(SCHEMA), "--append-system-prompt", SYSTEM]
    if cfg.get("effort"):
        cmd += ["--effort", cfg["effort"]]
    if cfg.get("per_call_budget_usd"):
        cmd += ["--max-budget-usd", str(cfg["per_call_budget_usd"])]
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDECODE")}
    try:
        r = subprocess.run(cmd + [build_prompt(decision)], capture_output=True, text=True,
                           timeout=240, cwd=str(target.home), env=env)
    except subprocess.TimeoutExpired:
        return {"status": "error", "reason": "timed out after 240 s"}
    try:
        res = json.loads(r.stdout)
    except Exception:
        return {"status": "error", "reason": (r.stderr or r.stdout)[-300:]}
    text = res.get("result", "")
    if res.get("is_error"):
        reason = text or res.get("subtype", "error")
        limited = bool(re.search(r"limit|quota|usage", reason, re.I))
        return {"status": "limit" if limited else "error", "reason": reason[:300]}
    payload = res.get("structured_output")
    if payload is None:
        m = re.search(r"\{.*\}", text, re.S)
        try:
            payload = json.loads(m.group(0)) if m else None
        except Exception:
            payload = None
    if not isinstance(payload, dict):
        return {"status": "error", "reason": "no JSON in reply"}
    payload = _validate(payload, decision)
    note = {"status": "ok", "model": model, "when": dt.datetime.now().isoformat(timespec="seconds"),
            "cost_usd": res.get("total_cost_usd"), "prompt_version": PROMPT_VERSION, **payload}
    out.write_text(json.dumps(note, indent=1, ensure_ascii=False))
    with (target.ledger_dir / "spend.jsonl").open("a") as fh:
        fh.write(json.dumps({"when": note["when"], "decision": decision["id"], "model": model,
                             "cost_usd": note["cost_usd"], "key": key}) + "\n")
    return note


def _validate(p: dict, decision: dict) -> dict:
    """Drop could_move items whose citation is not in the material the note was given."""
    r = decision.get("reach") or {}
    known = set(r.get("refs", [])) | set(r.get("decks", [])) | set(r.get("entry_points", []))
    known |= {decision.get("file", "")}
    ctx = (decision.get("context") or "") + (decision.get("diff") or "")
    kept, dropped = [], 0
    for item in p.get("could_move", []):
        cite = (item.get("cite") or "").strip()
        base = cite.split(":")[0]
        if cite and (cite in known or base in known or any(base and k.startswith(base) for k in known) or cite in ctx):
            kept.append(item)
        else:
            dropped += 1
    p["could_move"] = kept
    if dropped:
        p["dropped_uncited"] = dropped
    return p
