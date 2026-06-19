# GitHub issue & PR templates

Use `gh` (authenticated; remote is the project repo). `gh` interactive flags aren't available in this
environment, so pass `--title`/`--body` explicitly (a `--body-file` or heredoc is fine for long bodies).

## Issue (Phase 1)

Created from the plan so the issue stands alone. Title = the feature title.

```markdown
## Feature: <feature-id> — <title>

### Goal (user-visible behavior)
<user_visible_behavior — what an API client observes once done. State what's in and out of scope.>

### Approach
<the chosen option from the meeting record, one short paragraph — why this approach.>

### Implementation plan
1. <step — real files>
2. <step>
3. <step>

### Verification
- ./init.sh — uv run pytest + uv run ruff check src tests pass
- <feature-specific check, e.g. a new test in tests/… proving the behavior>
```

```bash
gh issue create --title "<title>" --body-file <(printf '%s' "$ISSUE_BODY")
```

## Pull request (Phase 6)

Open after verification passed, the Critic approved, and the harness is updated. Link the issue so merge
closes it.

```markdown
## Summary
<1-3 sentences: what changed and the user-visible effect.>

Closes #<issue-number>

## Approach
<the implemented approach, matching the plan; note any deviation and why.>

## Verification
- `uv run pytest` — <N> passed
- `uv run ruff check src tests` — all checks passed
- <feature-specific check result>

## Review
Critic verdict: approved. <one line on what was checked / notable risks, if any.>

## Notes / risks
<scope deferred, breaking changes, follow-ups — or "None".>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

```bash
git push -u origin <branch-name>
gh pr create --title "<title>" --body-file <(printf '%s' "$PR_BODY")
```

Commit message trailer (Phase 6 commit):

```
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```
