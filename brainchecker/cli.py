"""bc — the brainchecker command line.

    bc review                  audit the whole tree (form decisions + 30 per pillar), then notes
    bc stage                   report on what is staged now (the pre-commit hook prints the same)
    bc record [SHA]            record a commit's decisions in the ledger (the post-commit hook)
    bc replay A..B             run the per-change analysis over past commits (acceptance test)
    bc notes [--ids ..]        write consequence notes (Claude Code, headless) for critical decisions
    bc check ID [--patient P]  run one registered check
    bc comment ID TEXT         add a comment; --kind examined|mine|question|comment
    bc sync-comments FILE      import comments exported from the site's database
    bc site                    build the status website (site/index.html)
    bc status                  print the summary table
    bc install / uninstall     add or remove the git hooks in the target repo
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import sys
from pathlib import Path

from . import checks, config, gitutil, ledger, note, review, stage

HOOK_MARK = "# brainchecker hook"


def _notes(target, ids: list[str] | None, force: bool, limit: int | None, verbose: bool = True) -> dict:
    doc = ledger.load(target.ledger_dir)
    pool = [d for d in doc["decisions"] if d.get("file")]
    if ids:
        pool = [d for d in pool if d["id"] in set(ids)]
    else:
        pool = [d for d in pool if d.get("critical") and (force or (d.get("note") or {}).get("status") != "ok")]
    if limit:
        pool = pool[:limit]
    stats = {"ok": 0, "cached": 0, "error": 0, "limit": 0, "skipped": 0, "cost": 0.0}
    if not pool:
        return stats
    stop = False
    workers = int(target.notes.get("concurrency", 3))
    if verbose:
        print(f"notes: {len(pool)} decisions, model {target.notes.get('model')}, {workers} at a time")

    def attach(did, n):
        with ledger.locked(target.ledger_dir):
            doc2 = ledger.load(target.ledger_dir)
            for d in doc2["decisions"]:
                if d["id"] == did:
                    d["note"] = n
            ledger.save(target.ledger_dir, doc2)

    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {}
        it = iter(pool)
        for d in it:
            futs[ex.submit(note.write_note, target, d, force)] = d
            if len(futs) >= workers:
                break
        while futs:
            done, _ = cf.wait(futs, return_when=cf.FIRST_COMPLETED)
            for f in done:
                d = futs.pop(f)
                n = f.result() or {"status": "error", "reason": "no result"}
                st = n.get("status")
                if st == "ok":
                    stats["ok"] += 1
                    stats["cost"] += float(n.get("cost_usd") or 0)
                    attach(d["id"], n)
                else:
                    stats[st if st in stats else "error"] += 1
                if verbose:
                    print(f"  {d['id']} {d['file']}:{d['line']}  {st}"
                          + (f"  ${float(n.get('cost_usd') or 0):.3f}" if st == "ok" else f"  {n.get('reason', '')[:120]}"))
                if st == "limit":
                    stop = True
            if not stop:
                for d in it:
                    futs[ex.submit(note.write_note, target, d, force)] = d
                    break
    with ledger.locked(target.ledger_dir):
        doc = ledger.load(target.ledger_dir)
        ledger.refresh_statuses(doc, ledger.comments(target.ledger_dir))
        ledger.save(target.ledger_dir, doc)
        ledger.write_status_md(target.ledger_dir, doc)
    if verbose:
        print(f"notes: {stats['ok']} written (${stats['cost']:.2f} API-equivalent), "
              f"{stats['error']} errors, {stats['limit']} hit the usage limit")
    return stats


def _install(target):
    hooks = Path(gitutil.git(target.root, "rev-parse", "--git-path", "hooks").strip())
    if not hooks.is_absolute():
        hooks = target.root / hooks
    hooks.mkdir(parents=True, exist_ok=True)
    py = sys.executable
    for name, cmd in (("pre-commit", "pre-commit"), ("post-commit", "post-commit")):
        f = hooks / name
        line = (f'{HOOK_MARK}\nPYTHONPATH="{target.home}" "{py}" -m brainchecker --target {target.name} '
                f'{cmd} || true\n')
        if f.exists():
            text = f.read_text()
            if HOOK_MARK in text:
                print(f"{name}: already installed")
                continue
            f.write_text(text.rstrip("\n") + "\n\n" + line)       # chain after the existing hook
        else:
            f.write_text("#!/bin/sh\n" + line)
        f.chmod(0o755)
        print(f"{name}: installed in {f}")
    gitutil.git(target.root, "config", "alias.bc", f'!PYTHONPATH="{target.home}" "{py}" -m brainchecker --target {target.name}')
    print("git bc …: alias added (git bc stage, git bc status)")


def _uninstall(target):
    hooks = Path(gitutil.git(target.root, "rev-parse", "--git-path", "hooks").strip())
    if not hooks.is_absolute():
        hooks = target.root / hooks
    for name in ("pre-commit", "post-commit"):
        f = hooks / name
        if not f.exists():
            continue
        text = f.read_text()
        if HOOK_MARK not in text:
            continue
        kept = [l for l in text.split("\n\n") if HOOK_MARK not in l]
        rest = "\n\n".join(kept).strip()
        if rest in ("", "#!/bin/sh"):
            f.unlink()
        else:
            f.write_text(rest + "\n")
        print(f"{name}: removed")
    gitutil.git(target.root, "config", "--unset", "alias.bc", check=False)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="bc", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", default="brainphysio")
    ap.add_argument("--repo", default=None, help="override the target repo path")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("review"); r.add_argument("--sample", type=int, default=30); r.add_argument("--seed", type=int, default=20260926)
    r.add_argument("--no-notes", action="store_true")
    sub.add_parser("stage")
    sub.add_parser("pre-commit"); sub.add_parser("post-commit")
    rc = sub.add_parser("record"); rc.add_argument("sha", nargs="?", default="HEAD")
    rp = sub.add_parser("replay"); rp.add_argument("range"); rp.add_argument("--record", action="store_true")
    rp.add_argument("--quiet", action="store_true")
    n = sub.add_parser("notes"); n.add_argument("--ids", nargs="*"); n.add_argument("--force", action="store_true")
    n.add_argument("--limit", type=int)
    c = sub.add_parser("check"); c.add_argument("id"); c.add_argument("--patient", default="137")
    c.add_argument("--deck", default=""); c.add_argument("--replot-driver", default="plotter/replot_deck.jl")
    cm = sub.add_parser("comment"); cm.add_argument("id"); cm.add_argument("text")
    cm.add_argument("--kind", default="comment", choices=["comment", "question", "examined", "mine", "reopen", "not-a-decision"])
    cm.add_argument("--author", default="Thomas")
    sc = sub.add_parser("sync-comments"); sc.add_argument("file")
    s = sub.add_parser("site"); s.add_argument("--out", default=None)
    sub.add_parser("status"); sub.add_parser("install"); sub.add_parser("uninstall")
    a = ap.parse_args(argv)
    t = config.load(a.target, a.repo)

    if a.cmd == "pre-commit":
        return stage.pre_commit(t)
    if a.cmd == "post-commit":
        return stage.post_commit(t)
    if a.cmd == "stage":
        from . import provenance
        ti = provenance.TranscriptIndex(t.transcripts, t.ledger_dir / "cache"); ti.refresh()
        print(stage.report(t, stage.analyse(t, gitutil.staged_diff(t.root), None, ti), "staged change"))
        return 0
    if a.cmd == "record":
        ds = stage.record_commit(t, a.sha)
        print((t.ledger_dir / "last_commit.md").read_text())
        return 0
    if a.cmd == "replay":
        from . import provenance
        ti = provenance.TranscriptIndex(t.transcripts, t.ledger_dir / "cache"); ti.refresh()
        shas = gitutil.git(t.root, "rev-list", "--reverse", "--no-merges", a.range).split()
        rows = []
        for sha in shas:
            if a.record:
                ds = stage.record_commit(t, sha)
            else:
                parent = gitutil.git(t.root, "rev-list", "--parents", "-n", "1", sha).split()[1:]
                if not parent:
                    continue
                ds = stage.analyse(t, gitutil.range_diff(t.root, f"{parent[0]}..{sha}"), sha, ti, with_reach=False)
            subj = gitutil.git(t.root, "log", "-1", "--format=%s", sha).strip()
            lv = {k: sum(1 for d in ds if stage.level_of(d) == k) for k in stage.LEVELS}
            rows.append((sha[:8], subj, len(ds), lv))
            if not a.quiet:
                print(stage.report(t, ds, f"{sha[:8]} {subj[:60]}"))
        print(f"\n{'commit':9s} {'UC':>4s} {'UP':>4s} {'EC':>4s} {'EP':>4s}  subject")
        for sha, subj, nd, lv in rows:
            print(f"{sha:9s} " + " ".join(f"{lv[k]:4d}" for k in stage.LEVELS) + f"  {subj[:70]}")
        return 0
    if a.cmd == "review":
        doc = review.build(t, a.sample, a.seed)
        print(f"review: {len(doc['decisions'])} decisions → {t.ledger_dir / 'decisions.json'}")
        if t.notes.get("automatic") and not a.no_notes:
            _notes(t, None, False, None)
        return 0
    if a.cmd == "notes":
        _notes(t, a.ids, a.force, a.limit)
        return 0
    if a.cmd == "check":
        chk = next((c for c in t.checks if c["id"] == a.id), None)
        if not chk:
            print("unknown check; registered:", ", ".join(c["id"] for c in t.checks)); return 2
        if chk.get("builtin") == "copy_drift":
            print(json.dumps(checks.copy_drift(t), indent=1)); return 0
        res = checks.run_command(t, chk, {"patient": a.patient, "deck": a.deck, "replot_driver": a.replot_driver})
        print(res["status"], res["seconds"], "s\n", res["tail"][-800:]); return 0
    if a.cmd == "comment":
        ledger.add_comment(t.ledger_dir, a.id, a.text, a.kind, a.author)
        with ledger.locked(t.ledger_dir):
            doc = ledger.load(t.ledger_dir)
            ledger.refresh_statuses(doc, ledger.comments(t.ledger_dir))
            ledger.save(t.ledger_dir, doc); ledger.write_status_md(t.ledger_dir, doc)
        print("comment added")
        return 0
    if a.cmd == "sync-comments":
        rows = json.loads(Path(a.file).read_text())
        n = 0
        for c in rows:
            owner = bool(c.get("by_owner"))
            if ledger.add_comment(t.ledger_dir, c["decision"], c["text"], c.get("kind", "comment"),
                                  "Thomas" if owner else "reviewer",
                                  "site", c.get("when"), c.get("id"), owner=owner):
                n += 1
        with ledger.locked(t.ledger_dir):
            doc = ledger.load(t.ledger_dir)
            ledger.refresh_statuses(doc, ledger.comments(t.ledger_dir))
            ledger.save(t.ledger_dir, doc); ledger.write_status_md(t.ledger_dir, doc)
        print(f"{n} new comments imported")
        return 0
    if a.cmd == "site":
        from . import site
        out = site.build(t, a.out)
        print(out)
        return 0
    if a.cmd == "status":
        print((t.ledger_dir / "STATUS.md").read_text().split("\n## ")[0])
        return 0
    if a.cmd == "install":
        _install(t); return 0
    if a.cmd == "uninstall":
        _uninstall(t); return 0


if __name__ == "__main__":
    sys.exit(main())
