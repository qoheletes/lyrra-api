# Mapping a meeting decision into feature_list.json

When registering the planned feature, append a new object to the `features` array that matches the
existing entries exactly. Field-by-field:

| Field | What to put |
|---|---|
| `id` | `<area>-NNN`. Reuse the area of related features and increment the highest existing number in that area (e.g. if `storage-003` exists, the next storage feature is `storage-004`). |
| `priority` | Integer. Default to one past the current max unless the user wants it ranked higher. |
| `area` | The subsystem (`storage`, `youtube`, `auth`, …), consistent with the `id` prefix. |
| `title` | Short imperative summary — what the feature does. |
| `user_visible_behavior` | The Goal section from the meeting, in the concrete client-observable voice the existing entries use. |
| `status` | `not_started` by default. Use `in_progress` only if the user is starting now AND `rules.single_active_feature` permits it (no other feature already `in_progress`). |
| `verification` | Array of concrete checks that will prove it done — typically `"Run ./init.sh (pytest + ruff) — all checks pass."` plus a feature-specific check (a named test, a grep, an observed response). Pull these from the meeting's Verification plan. |
| `evidence` | Empty array `[]`. Evidence is recorded only when the work actually passes, not at planning time. |
| `notes` | Key decision rationale and a pointer to the meeting record, e.g. `"Approach chosen in planning meeting; see .claude/meetings/<id>.md. <one-line why>."` |

Also update the top-level `last_updated` field to today's date.

## Rules to respect

- `single_active_feature: true` — at most one feature should be `in_progress`. Registering a plan
  normally leaves the new feature `not_started`; the user starts it later.
- `passing_requires_evidence: true` — never set `status: passing` here. Planning produces a plan, not
  passing verification.
- Keep the JSON valid: match indentation, quote style, and trailing-comma conventions of the file.
  Edit precisely rather than rewriting the whole file.

## Example skeleton

```json
{
  "id": "youtube-002",
  "priority": 4,
  "area": "youtube",
  "title": "<short title>",
  "user_visible_behavior": "<client-observable behavior>",
  "status": "not_started",
  "verification": [
    "Run ./init.sh (pytest + ruff) — all checks pass.",
    "<feature-specific check>"
  ],
  "evidence": [],
  "notes": "Approach chosen in planning meeting; see .claude/meetings/youtube-002.md. <why>."
}
```
