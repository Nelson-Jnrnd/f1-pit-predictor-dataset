# Decision Boundaries

## Human owner reserved decisions

The human Product Owner retains authority over material choices that determine what project is being built or what its predictions mean, including:

- the primary project/research objective;
- intended user-facing outcome;
- major scope inclusions and exclusions;
- prediction versus recommendation/optimization intent;
- historical-only, historical-replay, or live ambitions;
- material interpretation of the event/quantity the model should predict;
- acceptable prediction semantics and uncertainty representation;
- major realism/product trade-offs;
- intentional exclusions;
- governance exceptions.

Agents must not silently select among materially different choices in these areas. Escalate using `governance/USER_INTERACTION.md`.

## Agent-delegated decisions

Within approved semantics and task scope, agents may normally decide without escalation:

- documentation organization and naming;
- decomposition into bounded artifacts/slices where ownership remains consistent;
- terminology where no approved term exists and the choice is not semantically material;
- evidence organization and traceability;
- routine examples and diagrams;
- classification/routing of later-phase questions;
- local technical choices in later design/implementation when approved contracts remain unchanged.

Do not turn routine technical or documentation choices into Product Owner questions.

## Must escalate

Escalation is required when a task would otherwise:

- change the approved project objective or core scope;
- change what information is considered legitimately available at prediction time;
- change the semantic meaning of the target or prediction;
- change a durable approved semantic lock;
- introduce recommendation/optimization behavior into a prediction product;
- materially change historical/replay/live ambition;
- create a new cross-slice coupling that invalidates approved ownership;
- make a governance exception.

After approval, persist the decision in the affected canonical artifact and create/update a durable record under `decisions/` when it will be reused later.

## Process authority delegated to agents

Agents may classify unknowns, split oversized tasks, route dependencies, stop non-converging review loops, and prevent later-phase concerns from blocking an earlier artifact. This authority does not override human-reserved product/research decisions.
