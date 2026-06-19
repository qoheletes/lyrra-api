# Implementer subagent brief

Spawn one subagent with a brief built from this template. Fill every `<…>` from the meeting record and
the feature entry. The implementer writes the code; it does not open issues or PRs and does not update
feature_list.json — those are the lead's job.

```
You are implementing one planned feature in the lyrra-api codebase (Python 3.14 FastAPI, PostgreSQL).
The plan is already decided — implement it faithfully, don't redesign it.

Feature: <feature-id> — <title>
User-visible behavior (the definition of done for behavior):
<user_visible_behavior from feature_list.json>

Implementation plan (from .claude/meetings/<feature-id>.md — follow these steps):
<paste the Implementation plan section>

Verification plan (must pass before you report done):
<paste the Verification plan section>

Scope:
- In scope: <what the plan says to build>
- Out of scope: <what was explicitly deferred / not part of this feature>
  Do NOT touch files outside this feature. Staying in scope is a hard requirement.

Branch: you are on <branch-name>. Commit nothing yourself — leave the working tree with your changes
for the lead to review and commit.

How to work:
1. Read the real code in the area first (routers, schemas, storage, tests) and match existing patterns,
   naming, and idioms — your code should read like the surrounding code.
2. Consult the relevant docs/ file if the area has one (async routes, pydantic, migrations, etc.).
3. Implement the plan step by step.
4. Add the feature-specific test the verification plan calls for.
5. Run ./init.sh (uv sync + app boot + smoke, then `uv run pytest` and `uv run ruff check src tests`).
   Iterate until it is fully green. Don't claim done on red or skipped checks.

Report back:
- A short summary of what you built and any deviations from the plan (with the reason).
- The list of files changed.
- The ACTUAL verification output — paste the pytest + ruff results you saw, not a claim that they pass.
- Anything you couldn't do, or risks the reviewer should know about.
```

## Lead checklist when the implementer returns

- Did it follow the plan's steps, or improvise? Improvisation isn't automatically wrong, but it must be
  explained and still satisfy `user_visible_behavior`.
- Is the verification evidence real — pasted command output — or merely asserted? If asserted, send it
  back to actually run `./init.sh`.
- Did it stay in scope? Check `git status` / `git diff --stat` for files outside the feature.
- If anything's off, hand it back with specifics before going to review.
