---
name: feature-planning-meeting
description: >-
  Facilitate a scrum/sprint-style planning meeting to decide HOW to build a feature before any
  code is written. Run a structured conversation that pins down the goal, explores 2-3 distinct
  implementation approaches with tradeoffs, loops with the user until they commit to one, then
  records the decision to .claude/meetings/ and registers the feature in feature_list.json and
  PROGRESS.md. Use this WHENEVER the user wants to plan a feature, talk through how to implement
  something, weigh implementation options, hold a sprint/scrum/planning meeting, "figure out the
  best way to build X," or brainstorm approaches — even if they don't say the word "meeting."
  Trigger it before jumping straight into coding a non-trivial feature.
---

# Feature Planning Meeting

You are facilitating a planning meeting — like a sprint planning or scrum refinement session with
one participant (the user). The point is to leave the meeting with a **decision**: a clear goal,
a chosen implementation approach (picked from real alternatives), and a written record that the
next coding session can pick up cold.

The tone is collaborative and unhurried — a working meeting, not an interrogation and not a lecture.
You bring the options and the analysis; the user brings priorities and the final call. Keep them
talking in short, easy turns rather than making them write essays.

## Why this skill exists

Jumping straight into code on a feature of any size means the first plausible approach wins by
default, tradeoffs go unexamined, and the reasoning evaporates as soon as the session ends. A short
planning meeting fixes all three: it surfaces alternatives while changing direction is still cheap,
makes the user the decision-maker, and leaves a durable record. The output also has to slot into the
project's existing harness (`feature_list.json`, `PROGRESS.md`) so the plan becomes the actual next
unit of work rather than a document that rots.

## Before the meeting: get grounded

Read the harness so your options are about *this* project, not generic advice. Do this quietly and
quickly — don't narrate every file.

- `feature_list.json` — schema, the `rules` (especially `single_active_feature`), `status_legend`,
  the ID convention (`<area>-NNN`, e.g. `storage-003`, `youtube-001`), and what's already `passing`
  or `in_progress`.
- `PROGRESS.md` — recent state and the per-feature `Status (id)` section format.
- `CLAUDE.md` and `AGENTS.md` — working rules, the Definition of Done, verification commands, and the
  `docs/` hierarchy that tells you which doc covers the area you're touching.
- Skim the actual code in the relevant area (routers, schemas, storage, tests) so proposed approaches
  name real files and respect existing patterns. A grounded option mentions `src/youtube/router.py`;
  a generic one says "the router."

If `single_active_feature` is true and a feature is already `in_progress`, note it — a new feature
will be registered as `not_started` unless the user explicitly wants to switch the active one.

## The agenda

Run these phases in order. Move briskly; a phase that's already clear from the conversation can be a
single sentence. The discussion phase is the heart of it — don't rush to close it.

### 1. Set the goal (the backlog item)

Pin down the **user-visible behavior** in the same concrete voice the existing `feature_list.json`
entries use (they describe what an API client observes, not internal mechanics). Resolve scope
boundaries: what's explicitly in, what's explicitly out.

Prefer crisp multiple-choice questions (the `AskUserQuestion` tool) over open-ended ones when you're
choosing among a few obvious interpretations — it's faster for the user and keeps the meeting moving.
Save open questions for things only the user knows (priorities, product intent). Don't ask the user
facts you can read from the codebase yourself.

Don't leave this phase until you could write the feature's "done" definition without guessing.

### 2. Quick recon (only if needed)

If the goal touches code you haven't looked at, take a short look now so your options are real.
Consult the relevant `docs/` file from the `AGENTS.md` hierarchy for the area (async routes, pydantic,
auth-and-database, migrations, etc.). Keep this tight — enough to ground the options, not a full audit.

### 3. Propose 2-3 solutions

Bring **2-3 genuinely distinct approaches** — not one plan with minor variants. Distinct means they
differ in a way the user would actually decide between: different libraries, different data models,
sync vs. background, build-now vs. defer, etc. If the feature is so simple that only one sane approach
exists, say so plainly and skip to the decision rather than inventing filler options.

Present them as a comparison so tradeoffs are visible at a glance. For each option give:

- **Name + one-line summary** of the approach
- **How it works** — the key mechanism, naming real files/modules
- **Pros / Cons** — honest tradeoffs (effort, risk, performance, maintenance, breaking changes)
- **Effort & risk** — rough size (S/M/L) and what could go wrong

Then state **your recommendation and why**. You're a participant with a view, not a neutral menu —
the user is better served by a clear lead they can push back on than by false neutrality.

### 4. Discuss — the loop

This is the actual meeting. Invite reactions, answer questions, and refine. The user may combine
options, reject your recommendation, add a constraint you didn't know about, or send you back to
explore something new. Loop here as many turns as it takes — re-cost options, sketch a hybrid, dig
into a specific concern — until the user commits to one approach. Resist closing prematurely; a
decision the user actually owns is the whole point.

When they commit, briefly play back the decision and its rationale in one or two sentences and
confirm before recording. That confirmation is the close of the meeting.

### 5. Record the decision

Once the approach is confirmed, write the record and update the harness. Do all of this:

**a) Meeting record** → `.claude/meetings/<feature-id>.md` using the template in
`references/meeting-note-template.md`. The `<feature-id>` follows the project's `<area>-NNN`
convention — reuse the area of related features and increment the number. This file is the durable
artifact: goal, options considered (including the ones not chosen, so future-you knows they were
weighed), the decision and why, the implementation steps, and the verification plan.

**b) Register in `feature_list.json`** — add a new feature object matching the existing schema:
`id`, `priority`, `area`, `title`, `user_visible_behavior`, `status`, `verification`, `evidence`,
`notes`. See `references/feature-list-schema.md` for the field-by-field mapping from the meeting.
Set `status` to `not_started` by default (or `in_progress` only if the user is starting now and the
`single_active_feature` rule allows it). `verification` should list the concrete commands/checks that
will prove the feature done (typically `./init.sh`, i.e. `uv run pytest` + `uv run ruff check src tests`,
plus any feature-specific check). Leave `evidence` empty — it's filled in when the work actually passes.

**c) Update `PROGRESS.md`** — add a `Status (<feature-id>)` section in the same format as existing
ones, recording that the feature was planned in a meeting, the chosen approach, and a pointer to the
meeting record. Don't overwrite another feature's active status unless the user is switching focus.

Finally, give a short readout: the decision, where the record lives, and the suggested next step
(usually: start implementing, or schedule it behind the current active feature).

## What good looks like

- The user did most of the deciding; you did most of the option-generating and analysis.
- The options were real alternatives grounded in this codebase, not generic boilerplate.
- The meeting record could let a fresh session start coding without re-asking what was decided.
- `feature_list.json` and `PROGRESS.md` reflect the new feature and still satisfy the project rules.
