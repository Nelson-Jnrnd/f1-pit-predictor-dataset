# Agent Instructions

This repository uses a specification-first workflow for V2. Substantial implementation must not begin until the relevant semantics, design, and verification baseline are approved.

Before working on a bounded task, read:

1. `governance/SPEC_PROCESS.md`
2. `governance/DECISION_BOUNDARIES.md`
3. `governance/REVIEW_POLICY.md`
4. `governance/USER_INTERACTION.md`
5. the issue/task that defines the bounded work package
6. every approved decision or upstream artifact referenced by that task

## Core rules

1. Stay inside the task's declared scope and abstraction level.
2. Classify every unresolved question as:
   - **Current-scope decision** — required to complete this artifact; resolve it or escalate if human-reserved.
   - **Cross-slice dependency** — another slice owns the answer; name the owner and required dependency without defining that slice internally.
   - **Later-phase decision** — route it to architecture/design, verification/experimentation, or implementation and continue.
3. Do not solve a later abstraction level merely because you can.
4. Specification agents must not make production-code changes unless the task explicitly reaches implementation.
5. One semantic concept has one canonical owner. Consumers reference the owning artifact rather than duplicating or redefining it.
6. Human-reserved decisions are defined in `governance/DECISION_BOUNDARIES.md`; do not escalate routine technical or documentation choices.
7. Authoring work receives one full independent review and, after rework, at most one bounded re-review before the task is split/rescoped/escalated.
8. Historical thesis work (`main`, `training_rf`, `training_svm`, `cleaning`, and legacy artifacts) is evidence and baseline material. Do not merge, rewrite, or delete it during specification work unless a later explicit task authorizes that action.
9. Normal V2 work uses short-lived task branches and reaches `main` through pull requests.
10. A chat decision is not durable. Persist approved material decisions in the canonical artifact and under `decisions/` when reusable.
11. Integration gates check cross-slice consistency; they do not reopen approved slices without a demonstrated contradiction.
12. Architecture/design, verification, and implementation may refine lower-level details but may not silently change approved product or prediction semantics.

Start with the smallest artifact set that satisfies the current task. Avoid speculative governance, architecture, schemas, APIs, libraries, or algorithms outside scope.
