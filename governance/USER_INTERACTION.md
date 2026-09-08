# Product Owner Interaction Policy

## Purpose

Product Owner communication should surface consequential project/research decisions without requiring the owner to read agent scratch work.

Routine exploration and delegated decisions stay in repository artifacts. Material uncertainty and trade-offs must not be hidden.

## No-decision status

When no Product Owner decision is required, report:

**Outcome**  
1–3 sentences stating what was established, changed, reviewed, or completed.

**Important note**  
Only when a material caveat, unresolved dependency, risk, or next gate exists.

Include the relevant issue/branch/PR reference when repository work was completed.

## Product Owner decision card

Use only for a human-reserved, genuinely blocking current-scope decision.

**PRODUCT OWNER DECISION**

**Question**  
One sentence.

**Why this matters**  
1–2 sentences.

**A — <option>**  
+ Main advantage  
− Main consequence/trade-off

**B — <option>**  
+ Main advantage  
− Main consequence/trade-off

**C — <option>**  
Only when genuinely distinct and useful.

**Recommendation**  
`A`, `B`, or `C` with a short rationale. A recommendation is not approval.

**Decision requested**  
`A / B / C`

## Single-proposal approval card

When one responsible proposal is clearly preferred and alternatives would be artificial:

**RECOMMENDED DECISION**

**Proposal**  
One concise statement.

**Reason**  
Why this direction is preferred.

**Material downside**  
The principal cost, limitation, or uncertainty.

**Decision requested**  
`Approve / Reject`

## Decision batching

Batch at most three small, independent decisions. Dependent/high-impact decisions should be presented sequentially.

Do not escalate questions already delegated to agents, questions that belong to later phases, or routine technical choices.

## Persistence

A chat answer is not the source of truth. After a material decision:

1. update the affected canonical artifact;
2. create/update a record under `decisions/` when the choice is durable/reusable;
3. reference the durable decision from related tasks/PRs where useful;
4. continue without asking for the same decision again.
