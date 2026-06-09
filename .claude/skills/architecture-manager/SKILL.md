---
name: architecture-manager
description: Create or update documents (ARCHITECTURE.md) based on existing domain models and improve terminology.
---

<supporting-info>

## Domain awareness

During codebase exploration, also look for existing documentation:

### File structure

Most repos have a single context:

```
/
├── ARCHITECTURE.md
├── docs/
└── src/
```

If a `ARCHITECTURE-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives:

```
/
├── ARCHITECTURE-MAP.md
├── docs/
├── src/
│   ├── ordering/
│   │   ├── ARCHITECTURE.md
│   │   └── ...                 
│   └── billing/
│       ├── ARCHITECTURE.md
│       └── ...
```

Create files lazily — only when you have something to write. If no `ARCHITECTURE.md` exists, create one when the first term is resolved.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `ARCHITECTURE.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

### Update CONTEXT.md inline

When a term is resolved, update `ARCHITECTURE.md` right there. Don't batch these up — capture them as they happen. Use the format in [ARCHITECTURE.md](./templates/ARCHITECTURE.md).

`ARCHITECTURE.md` should be totally devoid of implementation details. Do not treat `ARCHITECTURE.md` as a spec, a scratch pad, or a repository for implementation decisions. It is a glossary and nothing else.

</supporting-info>
