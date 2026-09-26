"""Checks: the only commands brainchecker ever runs are the ones registered in target.toml.

Two builtins run instantly on every change (copy drift, claim reuse). Registered commands
(verify_fit, gates, replots) are listed per decision with their exact command; the
background runner executes the cheap ones and records every result in the ledger.
Commands suggested by an AI note are shown, never run.
"""
from __future__ import annotations

import datetime as dt
import difflib
import json
import re
import subprocess
from pathlib import Path

from .config import matches


def applicable(target, path: str) -> list[dict]:
    return [c for c in target.checks if matches(path, c.get("applies", ["**"]))]


def copy_drift(target, paths: list[str] | None = None) -> list[dict]:
    """Hand-synced pairs that no longer agree once the allowed substitutions are applied."""
    out = []
    for pair in target.pairs:
        a, b = pair["a"], pair["b"]
        if paths is not None and a not in paths and b not in paths:
            continue
        fa, fb = target.root / a, target.root / b
        if not (fa.is_file() and fb.is_file()):
            continue
        ta, tb = fa.read_text(errors="replace"), fb.read_text(errors="replace")
        if pair.get("mode") == "shared-functions":
            out.append(_shared_functions(a, b, ta, tb))
            continue
        for x, y in pair.get("normalize", []):
            ta = ta.replace(x, y)
        la = [l.rstrip() for l in ta.splitlines() if l.strip() and not l.strip().startswith("#")]
        lb = [l.rstrip() for l in tb.splitlines() if l.strip() and not l.strip().startswith("#")]
        diff = [d for d in difflib.unified_diff(la, lb, lineterm="", n=0) if d[:1] in "+-" and d[:3] not in ("+++", "---")]
        out.append({"pair": f"{a} ↔ {b}", "differing_lines": len(diff), "sample": diff[:6]})
    return out


def _shared_functions(a: str, b: str, ta: str, tb: str) -> dict:
    def funcs(t):
        out, cur, buf = {}, None, []
        for line in t.splitlines():
            m = re.match(r"^function\s+([\w!.]+)", line)
            if m:
                if cur:
                    out[cur] = "\n".join(buf)
                cur, buf = m.group(1), [line]
            elif cur:
                buf.append(line)
                if line.startswith("end"):
                    out[cur] = "\n".join(buf); cur, buf = None, []
        return out
    fa, fb = funcs(ta), funcs(tb)
    shared = sorted(set(fa) & set(fb))
    differ = [f for f in shared if fa[f].strip() != fb[f].strip()]
    return {"pair": f"{a} ↔ {b}", "shared_functions": len(shared), "differing_functions": differ[:20],
            "differing_lines": len(differ)}


def run_command(target, check: dict, fill: dict, timeout: int = 3600) -> dict:
    cmd = check["command"].format(repo=target.root, **fill)
    started = dt.datetime.now()
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        status = "pass" if r.returncode == 0 else "fail"
        tail = (r.stdout + r.stderr)[-2000:]
    except subprocess.TimeoutExpired:
        status, tail = "timeout", ""
    res = {"check": check["id"], "command": cmd, "status": status,
           "started": started.isoformat(timespec="seconds"),
           "seconds": round((dt.datetime.now() - started).total_seconds(), 1), "tail": tail}
    d = target.ledger_dir / "checks"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{check['id']}-{started:%Y%m%d-%H%M%S}.json").write_text(json.dumps(res, indent=1))
    return res


def latest_results(target) -> dict[str, dict]:
    d = target.ledger_dir / "checks"
    out = {}
    if d.is_dir():
        for f in sorted(d.glob("*.json")):
            try:
                r = json.loads(f.read_text())
            except Exception:
                continue
            out[r["check"]] = r
    return out
