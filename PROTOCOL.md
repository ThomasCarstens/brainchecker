# The decision protocol

This protocol was agreed through the AI-slop protocol form (answered 26 September 2026, [targets/brainphysio/form_2026-09-26.json](targets/brainphysio/form_2026-09-26.json)). It covers how design decisions get made and owned in a modelling project that students will fork and extend.

## 1. What this protocol is about

AI slop is the irresponsible use of AI. It does the most damage at the design stage, where AI can drive key decisions. Those decisions still need to be examined and validated, even when no record of the validation exists.

The protocol is not about whether AI wrote a line. It is about whether a **decision** has an owner who examined it. There are four pillars where decisions matter:

| Pillar | Examples of decisions |
|---|---|
| Modelling | an equation, a parameter value, a constitutive law, a steady-state tolerance |
| Fitting | the free parameters and their bounds, the objective, the data window, which patients are fitted |
| Plotting | which runs are drawn, colours that carry a model's identity, what a panel compares |
| Model comparison | what is compared with what, the metric, the stimulus alignment |

Automation is fine. Here are two examples of the difference:

- An AI that rewrites a loop to run faster is automation.
- An AI that picks a tolerance so that a run converges is a decision, and that decision now needs an owner.

## 2. The four levels

Every decision sits at one of four levels:

|  | **critical** | **passable** |
|---|---|---|
| **unexamined** | the level that matters | noted, low priority |
| **examined** | recorded in the decision log | fine |

These three statuses sit outside the grid:

- **Mine**: the author made the decision themselves.
- **Human (evidence)**: the line predates AI use, or was imported untouched.
- **Not a decision**: the rules flagged a line that is not a decision. Dismissing it helps the rules learn.

### What counts as examined

Any one of these counts:

- You reproduced the result another way.
- You wrote your own rationale.
- A second person reviewed it.
- You checked the source (paper, datasheet, measurement).
- You wrote a walkthrough that someone else can follow.

These do **not** count:

- The tests pass.
- It looked right.
- The AI explained it.
- You specified the change and the AI implemented it. Specifying a change is not examining it.

Once a decision is examined and justified, it belongs to the author. An examined critical decision gets an entry in the decision log.

### Presumption

Every line is presumed AI-written and unexamined until there is evidence otherwise. Claude's own edits are included: they count as unexamined until the author marks them. The author can declare otherwise, but never has to.

## 3. How decisions are found

Rules find decisions. AI never does. A line or hunk is a decision when it carries one of these signatures:

| Signature | What it looks like |
|---|---|
| value | a literal given to a named setting: parameter, bound, tolerance, window, colour |
| equation | an MTK equation, a connection, a component, an ODE right-hand side |
| selection | a list of runs, models, patients or panels; a pin; a loop over literals |
| rule | a gate, an assert, an objective, a metric, a threshold comparison |
| claim | prose that states a number or a finding |
| new-file | a new file in a pillar folder |
| code | any other non-trivial change in a critical-by-default file |

A decision's default level comes from the path map in [targets/brainphysio/target.toml](targets/brainphysio/target.toml):

| Default | Where |
|---|---|
| **Critical** | model core files, protocols, the fitting code, data preparation, the plotting registry, READMEs and docs, `.protocols/` |
| **Passable** | generated fit parameters, the plotting stack, deck layouts, drivers |

These conditions raise a decision to critical wherever it is:

- a changed equation, parameter, bound or initial condition;
- a changed tolerance, `dtmax`, `maxiters` or clamp;
- a change to what is compared with what;
- a comment or docstring that states a number or a finding;
- a deleted gate;
- a different function sequence in the plotter.

The student decides the final criticality. The rules only propose it.

## 4. Per-change checks, not CI/CD

There is no CI/CD pipeline. Each change is checked on the author's machine, when it happens.

| When | What happens | Blocks? |
|---|---|---|
| `git commit` (pre-commit) | The staged change is cut into decisions and printed, grouped by level, with who wrote each one and what it reaches | **Never** |
| After the commit (post-commit) | The decisions go into the ledger. The instant checks run. Critical decisions get an AI note in the background. | Never |
| Any time | `bc review` samples the whole tree. The website shows every status and takes comments. | — |

Friction is 1: brainchecker never asks and never blocks. The commit message is left alone, and nothing about AI goes into the public history.

### Reach, note, check

Each decision gets three layers of consequence analysis:

1. **Reach** is deterministic. It lists which files reference the symbol, which entry points include the file, which models and plot decks sit downstream, and which report figures those decks feed. It is static and approximate, and it says so.
2. **Note** is written by Claude Code (`claude -p`, headless, no tools, a fixed JSON schema). It says what the decision means, what it could move (every item must cite a file or deck from the reach), the expected effect, and one cheap check. The guardrails:
   - A note is **never** an examination.
   - A note can add to the reach but never remove from it.
   - Uncited claims are dropped.
   - A command the note suggests is shown and never run.
   - Notes live in the ledger, never in the code.
3. **Check** runs registered commands only: copy drift, claim reuse, `verify_fit`, the M6/M7 gates, a replot. These commands are listed in the target file. Nothing else is ever executed.

## 5. Marking decisions

A decision can be marked in either of two places:

- **In the code**, with a comment on or next to the line:
  - `# examined: <how you checked it>`
  - `# human: <why>`
- **On the website**, by commenting on the decision and picking one of these:
  - **Examined**, with how you checked it
  - **Mine**
  - **Not a decision**
  - **Reopen**

Only the owner's marks change a status. Anyone else's "examined" stays a proposal in the thread until the owner agrees.

Report passages are shown as evidence to confirm. On their own they never mark a decision examined. For example, the Ursino validation, the fit-comparison CSVs and the h-sweep ratios are all written up in reports, yet the author still answered "Don't know" for them.

## 6. Scope and audit

The protocol covers these places:

- the `human_m123` branch of brainphysio_celia;
- the Seafile notebooks;
- `brainphysio-tutorials`, which includes the notebooks but not the data (the data stays in Seafile);
- `.protocols/`.

Audits start by sampling 30 decisions per pillar. The review uses a fixed seed, so the sample can be reproduced.

The ledger (`ledger/<target>/decisions.json`, `comments.jsonl`, `STATUS.md`) is tracked in this repository, which stays internal.

The acceptance test is the author's own code: `bc replay` runs the per-change analysis over past commits, and the review runs over the current tree.
