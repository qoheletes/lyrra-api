# Meeting note template

Write the meeting record to `.claude/meetings/<feature-id>.md` using this structure. Keep it tight and
factual — it exists so a future session can start cold. Fill every section; if a section is genuinely
empty (e.g. no open questions), write "None" rather than deleting it.

```markdown
# Planning Meeting: <feature-id> — <short title>

- **Date:** <YYYY-MM-DD>
- **Area:** <area, matching feature_list.json>
- **Status:** decided
- **Participants:** user, Claude

## Goal (user-visible behavior)

<What an API client / user observes once this is done. Same concrete voice as feature_list.json
user_visible_behavior entries. State scope: what's in, what's explicitly out.>

## Options considered

### Option A — <name>  ✅ chosen / ❌ not chosen
- How it works: <key mechanism, real files/modules>
- Pros: <…>
- Cons: <…>
- Effort / risk: <S/M/L, what could go wrong>

### Option B — <name>  ✅/❌
- How it works: <…>
- Pros: <…>
- Cons: <…>
- Effort / risk: <…>

### Option C — <name>  ✅/❌   (omit if only two real options)
- …

## Decision

<Chosen option and the reasoning — why it beat the alternatives, including any constraint the user
added during discussion. This is the most important section.>

## Implementation plan

1. <step — name real files, e.g. add route in src/youtube/router.py>
2. <step>
3. <step>

## Verification plan

- <e.g. ./init.sh — pytest + ruff pass>
- <feature-specific check that proves the behavior, e.g. a new test in tests/…>

## Open questions / risks

<Anything unresolved, deferred, or risky. "None" if clean.>
```
