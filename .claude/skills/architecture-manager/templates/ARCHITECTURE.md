# ARCHITECTURE.md

## Structure

```md
# {Context Name}

{One or two sentence description of what this context is and why it exists.}

## Layers

{Description of layer model.}

## Data Flow

1. User selects file via ImportPanel
2. App.tsx calls window.knowledgeBase.documents.import(filePath)
3. Preload bridge invokes ipcRenderer.invoke('documents:import', filePath)
```

## Rules

- **Be opinionated.** When multiple words exist for the same concept, pick the best one and list the others as aliases to avoid.
- **Flag conflicts explicitly.** If a term is used ambiguously, call it out in "Flagged ambiguities" with a clear resolution.
- **Show relationships.** Use bold term names and express cardinality where obvious.
- **Only include terms specific to this project's context.** General programming concepts (timeouts, error types, utility patterns) don't belong even if the project uses them extensively. Before adding a term, ask: is this a concept unique to this context, or a general programming concept? Only the former belongs.
- **Group terms under subheadings** when natural clusters emerge. If all terms belong to a single cohesive area, a flat list is fine.
- **Write an example dialogue.** A conversation between a dev and a domain expert that demonstrates how the terms interact naturally and clarifies boundaries between related concepts.

## Single vs multi-context repos

**Single context (most repos):** One `ARCHITECTURE.md` at the repo root.

**Multiple contexts:** A `ARCHITECTURE-MAP.md` at the repo root lists the contexts, where they live, and how they relate to each other:

```md
# ARCHITECTURE MAP

## System Shape
- Product: `[replace with product name]`
- Primary user workflow: `[replace with main workflow]`
- Runtime surfaces: `[desktop / web / cli / services / workers]`

## Domains

- [Ordering](./src/ordering/ARCHITECTURE.md) — receives and tracks customer orders
- [Billing](./src/billing/ARCHITECTURE.md) — generates invoices and processes payments
- [Fulfillment](./src/fulfillment/ARCHITECTURE.md) — manages warehouse picking and shipping

## Relationships

- **Ordering → Fulfillment**: Ordering emits `OrderPlaced` events; Fulfillment consumes them to start picking
- **Fulfillment → Billing**: Fulfillment emits `ShipmentDispatched` events; Billing consumes them to generate invoices
- **Ordering ↔ Billing**: Shared types for `CustomerId` and `Money`
```

The skill infers which structure applies:

- If `ARCHITECTURE-MAP.md` exists, read it to find contexts
- If only a root `ARCHITECTURE.md` exists, single context
- If neither exists, create a root `ARCHITECTURE.md` lazily when the first term is resolved

When multiple contexts exist, infer which one the current topic relates to. If unclear, ask.
