"""Report evidence: where the internship documents mention a decision.

For the 32 decisions Thomas classified, the evidence is curated by hand
(targets/<name>/known.toml). For everything else this module searches the documents
for the decision's symbol or its numbers and returns passages as *possible* mentions.
A passage is evidence to confirm, not an examination (protocol §2).
"""
from __future__ import annotations

import re
import subprocess
import urllib.request
from functools import cached_property
from pathlib import Path


class Reports:
    def __init__(self, target):
        self.t = target
        self.cache = target.ledger_dir / "cache" / "reports"
        self.cache.mkdir(parents=True, exist_ok=True)

    def refresh(self) -> list[str]:
        """Extract each document to text (pdftotext, or the Google Doc's link export)."""
        done = []
        for r in self.t.raw.get("reports", []):
            out = self.cache / (re.sub(r"\W+", "_", r["name"]).strip("_") + ".txt")
            try:
                if "pdf" in r:
                    src = self.t.expand(r["pdf"])
                    if src.is_file() and (not out.exists() or out.stat().st_mtime < src.stat().st_mtime):
                        subprocess.run(["pdftotext", "-layout", str(src), str(out)],
                                       capture_output=True, check=False)
                elif "gdoc" in r:
                    url = f"https://docs.google.com/document/d/{r['gdoc']}/export?format=txt"
                    with urllib.request.urlopen(url, timeout=30) as resp:
                        out.write_bytes(resp.read())
                if out.exists():
                    done.append(r["name"])
            except Exception as e:                       # a missing report is not fatal
                print(f"  report {r['name']}: {e}")
        self.__dict__.pop("texts", None)
        return done

    @cached_property
    def texts(self) -> dict[str, list[str]]:
        out = {}
        for r in self.t.raw.get("reports", []):
            f = self.cache / (re.sub(r"\W+", "_", r["name"]).strip("_") + ".txt")
            if f.exists():
                out[r["name"]] = f.read_text(errors="replace").splitlines()
        return out

    def search(self, terms: list[str], limit: int = 3) -> list[dict]:
        hits = []
        terms = [t for t in dict.fromkeys(terms) if t and len(t) >= 4]
        if not terms:
            return hits
        pats = [re.compile(r"(?<![\w.])" + re.escape(t) + r"(?![\w])") for t in terms]
        for doc, lines in self.texts.items():
            for i, line in enumerate(lines):
                for t, p in zip(terms, pats):
                    if p.search(line):
                        ctx = " ".join(x.strip() for x in lines[max(0, i - 1):i + 2])
                        hits.append({"doc": doc, "at": f"line {i + 1}", "kind": "possible mention",
                                     "term": t, "quote": re.sub(r"\s+", " ", ctx)[:320]})
                        break
                if len(hits) >= limit * 3:
                    break
        # one hit per document first, then fill
        seen, out = set(), []
        for h in hits:
            if h["doc"] not in seen:
                out.append(h); seen.add(h["doc"])
        for h in hits:
            if len(out) >= limit:
                break
            if h not in out:
                out.append(h)
        return out[:limit]


def search_terms(decision: dict) -> list[str]:
    terms = []
    sym = decision.get("symbol")
    if sym and len(sym) >= 4 and not sym.islower() or (sym and "_" in (sym or "")):
        terms.append(sym)
    terms += re.findall(r"(?<![\w.])(\d+\.\d+(?:e-?\d+)?|\d+e-?\d+)(?![\w.])", decision.get("text", ""))
    return terms[:6]
