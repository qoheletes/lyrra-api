---
name: feature-build-orchestration
description: >-
  Drive an already-planned feature from plan to an open pull request. Pick up a feature that a
  planning meeting registered in feature_list.json (status not_started/in_progress), open a GitHub
  issue from its plan, cut a feature branch, implement it via an implementer subagent, audit the
  diff with a Critic reviewer subagent, verify with ./init.sh, update feature_list.json + PROGRESS.md
  with evidence, then commit, push, and open a PR for human review. Use this WHENEVER the user wants
  to build/implement/ship a planned feature, "take this to a PR," "build the next feature," "run the
  build," "orchestrate the implementation," or names a feature id to execute — even if they don't say
  "orchestrate." This is the BUILD half that runs AFTER feature-planning-meeting decides HOW; if no
  plan exists yet, send them there first rather than inventing one.
license: MIT
---

# Feature Build Orchestration

You are the build lead for one feature. A planning meeting already decided *how* to build it and left
a record; your job is to turn that decision into a reviewed pull request without losing the plan's
intent, blowing scope, or skipping verification. You coordinate two subagents — an **implementer** who
writes the code and a **Critic reviewer** who audits it — and you own the harness updates and the
GitHub handoff.

The end state is a **pushed branch with an open PR**, the feature marked `passing` in
`feature_list.json` with real evidence, and `PROGRESS.md` updated. You stop at the open PR — a human
merges. You don't merge.

## Why this skill exists

Planning is cheap to do well and easy to throw away the moment coding starts. Without a disciplined
build step, the implementation drifts from the agreed approach, touches files it shouldn't, gets
called "done" before verification actually ran, and lands as a PR no one can review because the
reasoning never made it out of the session. This skill keeps the build honest: it executes *the plan
that was decided* (not a fresh improvisation), separates writing code from judging it so problems get
caught, gates "done" on verification that genuinely ran, and produces an issue + PR that a reviewer
can follow back to the original decision.

## Before you build: get grounded and confirm the target

Read the harness quietly — don't narrate every file — so the build respects *this* project.

- **The target feature.** Identify which feature to build. If the user named one (an id like
  `storage-004` or a title), use it. Otherwise pick the highest-priority `not_started` feature in
  `feature_list.json` and confirm with the user before doing anything irreversible. Don't build a
  feature the user didn't ask for.
- **Its plan.** Read `.claude/meetings/<feature-id>.md` — the **Implementation plan** and
  **Verification plan** sections are your spec. Read the feature's object in `feature_list.json` for
  `user_visible_behavior`, `verification`, scope, and `area`.
- **The rules.** `feature_list.json` `rules` (especially `single_active_feature`) and `status_legend`;
  `CLAUDE.md` for the Definition of Done and working rules; `init.sh` for the exact verification path
  (`uv sync` + app boot + smoke, then `uv run pytest` and `uv run ruff check src tests`).
- **State.** `PROGRESS.md` recent sections, `git log --oneline -5`, and whether a feature is already
  `in_progress` (with `single_active_feature` true, finishing or explicitly switching off the active
  one comes first — flag it, don't silently start a second).

**No meeting record?** This skill consumes a plan; it doesn't write one. If there's no
`.claude/meetings/<feature-id>.md` and no usable plan in the feature entry, stop and tell the user to
run the **feature-planning-meeting** skill first (or paste a plan). Building unplanned is exactly the
drift this skill exists to prevent.

Once you know the target and have its plan in hand, mark it `in_progress` in `feature_list.json` (if it
isn't already) so the harness reflects the active work, and confirm the plan-of-record with the user in
one or two sentences before opening anything outward-facing.

## The build pipeline

Run these phases in order. Each outward-facing or hard-to-reverse step (opening the issue, pushing,
opening the PR) should be visibly happening with the user's awareness — the skill invocation authorizes
the workflow, but surface what you're about to do rather than doing it silently.

### 1. Open the GitHub issue

Create a tracking issue from the plan with `gh` (it's authenticated; remote is the project's GitHub
repo). Title is the feature title; body carries the goal, the chosen approach, the implementation
steps, and the verification plan so the issue stands alone. Use the template in
`references/github-templates.md`. Capture the issue number/URL — it threads through the branch, the
feature evidence, and the PR.

```bash
gh issue create --title "<title>" --body "<body>"
```

### 2. Cut the feature branch

Never build on `main`. Branch with the project's convention — `feature/<slug>` derived from the
feature (e.g. `feature/r2-only-storage`, `feature/clarify-transcript-route`). Match the style of recent
branches in `git log`. Branch off the up-to-date main.

### 3. Implement — hand off to the implementer subagent

Spawn one implementer subagent and give it the brief in `references/implementer-brief.md`, filled in
with: the feature id + `user_visible_behavior`, the meeting record's implementation + verification
plan, the explicit scope boundaries (what's in, what's out), the branch name, and the verification
command (`./init.sh`). Its contract: implement the plan on the branch, follow existing code patterns,
add the feature-specific test the verification plan calls for, run `./init.sh` until it's green, and
report back a summary, the files changed, and the actual verification output.

You are the lead, not a bystander: when the implementer returns, sanity-check that it did what the plan
asked and that the verification evidence is real (it ran the commands and pasted output), not asserted.
If it went out of scope or skipped verification, send it back with specifics before moving on.

### 4. Review — hand off to the Critic reviewer subagent

Spawn a separate reviewer subagent (a Critic) with `references/reviewer-brief.md`. Separating who writes
from who judges is the point — a fresh reviewer catches what the author rationalizes. Give it the diff
(`git diff main...HEAD`), the plan, and the Definition of Done. It checks: does the diff implement the
agreed approach; does it stay in scope (no unrelated files); did verification genuinely pass; are there
correctness, security, or maintainability problems; is anything from the plan missing.

It returns a verdict — **approve** or **changes requested** with specific, actionable items. If changes
are requested, loop back to the implementer (Phase 3) with the Critic's list, then re-review. Iterate
until the Critic approves or the user calls it. Don't rubber-stamp; don't loop forever — if you're
stuck after a couple rounds, surface it to the user.

### 5. Update the harness with evidence

Only once verification truly passed and the Critic approved, record it — this is what makes the feature
legitimately `passing` rather than just "code exists":

- **`feature_list.json`** — set the feature `status` to `passing` and fill `evidence` with dated, real
  proof: the verification commands and their results (e.g. `uv run pytest — N passed; ruff — all checks
  passed`), and the issue URL. Keep `verification` as the checks that prove it. Don't mark `passing`
  on a feature whose tests you didn't see pass.
- **`PROGRESS.md`** — add/update the `Status (<feature-id>)` section in the existing format: what was
  done, verification evidence, notes/risks, the branch name, and the issue link.

### 6. Commit, push, open the PR

Commit the work with a descriptive message, ending with the project's trailer:

```
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

Push the branch and open the PR with `gh`, linking the issue (`Closes #<n>`) so the merge auto-closes
it. Use the PR template in `references/github-templates.md`; end the PR body with:

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

Then **stop**. Give a short readout: the issue link, the PR link, the verification result, the Critic's
verdict, and that it's ready for human review and merge. You don't merge — that's the human's call.

## What good looks like

- The PR implements the *planned* approach; a reviewer can trace it from issue → plan → diff.
- The implementer wrote the code and a separate Critic judged it — real problems got caught before the PR.
- The feature is `passing` only because verification actually ran, with the output recorded as evidence.
- Scope held: the diff touches the feature's files and nothing unrelated.
- `feature_list.json` and `PROGRESS.md` are updated and the repo still starts clean from `./init.sh`.
- You stopped at an open PR and left the merge to the human.
