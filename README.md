# brainchecker

brainchecker runs per-change decision checks on a modelling repository. It works without CI/CD: everything runs on the author's machine, when a change happens, and it never blocks. The rules it enforces are in [PROTOCOL.md](PROTOCOL.md).

```
git commit ─▶ pre-commit: the staged change, cut into decisions, grouped by level (prints, never blocks)
          └▶ post-commit: decisions into the ledger; AI notes for critical ones in the background
bc review ─▶ the whole tree: your 32 form decisions + 30 sampled per pillar, provenance, reach, reports
bc site   ─▶ one page with every status and a comment thread per decision
```

## Commands

Run these from this folder, with `./bc`. In the target repo, `git bc` does the same after `./bc install`.

| Command | What it does |
|---|---|
| `./bc review` | Audits the whole tree, then writes notes for the critical rows (automatic, see `[notes]`) |
| `./bc stage` | Reports on what is staged now (the pre-commit hook prints the same report) |
| `./bc record [SHA]` | Records one commit in the ledger (this is what the post-commit hook runs) |
| `./bc replay A..B` | Runs the per-change analysis over past commits; `--record` also writes them to the ledger |
| `./bc notes [--ids …]` | Writes consequence notes with Claude Code (`claude -p`, headless, no tools) |
| `./bc check ID` | Runs one registered check (`copy-drift`, `verify-fit-m5`, `m7-gate`, …) |
| `./bc comment ID "text" --kind examined` | Marks or comments on a decision from the terminal |
| `./bc sync-comments FILE` | Imports the website's comments (Claude exports them from the page's database) |
| `./bc site` | Builds `site/index.html` from the ledger |
| `./bc install` / `./bc uninstall` | Adds or removes the two hooks and the `git bc` alias in the target repo |

## Layout

```
brainchecker/        the package: rules, provenance, reach, evidence, note, checks, stage, review, ledger, site
targets/<name>/      target.toml (paths, path map, pairs, checks, reports), known.toml (the 32 form decisions),
                     the form answers
ledger/<name>/       decisions.json, comments.jsonl, STATUS.md, notes/, spend.jsonl, checks/   (tracked)
                     cache/ (transcript index, report text)                                    (ignored)
site/                the generated page (ignored); the template is brainchecker/site_template.html
tests/               python3 -m unittest discover tests
```

## Where the facts come from

- **Decisions** come from rules only ([rules.py](brainchecker/rules.py)). AI never decides what counts as a decision.
- **Who wrote a line** is worked out from three sources, in order:
  1. A `# human:` mark in the code.
  2. The Claude Code transcripts in `~/.claude/projects/<project>/`. A line counts as Claude's when an Edit added it or a Write created the file that holds it.
  3. `git blame`. Blame looks through commits that only moved a line. A `Co-Authored-By: Claude` trailer counts as AI, and a date on or before `pre_ai_until` counts as the pre-AI baseline.
  
  Anything else is **presumed AI**.
- **Examination** comes only from an `# examined:` mark, a DECISIONS.md entry, the owner's comment on the site, or the form answer.
- **Report evidence** comes from pdftotext of the internship reports, plus the "Performing the Analysis" Google Doc, read through its export link. It is shown as evidence to confirm and never counts as an examination.
- **Notes** come from Claude Code (`claude-opus-5`, low effort), with a JSON schema. Every "could move" item must cite a file or deck from the reach, or it is dropped. Each note is cached by a hash of its inputs, and its cost is logged in `spend.jsonl`. The costs are API-equivalent: on a claude.ai plan the calls draw on the plan's allowance. If a run hits the usage limit, the batch stops cleanly.

## Cost control

Everything is in `[notes]` in `targets/<name>/target.toml`:

| Setting | What it controls |
|---|---|
| `automatic` | Whether notes are written without being asked |
| `levels` | Which decisions get notes |
| `daily_cap_usd` | A daily spending cap; 0 means no cap |
| `per_call_budget_usd` | Passed to `claude --max-budget-usd` |
| `concurrency` | How many notes run at the same time |
