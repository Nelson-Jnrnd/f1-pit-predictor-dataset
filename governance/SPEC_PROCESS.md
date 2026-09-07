# Specification Process

## Purpose

The V2 process is designed to keep product/research semantics explicit before technical implementation while remaining lightweight enough for a small ML/data project.

The goal is not to decide every implementation detail early. The goal is to prevent later agents from inventing the meaning of observations, targets, predictions, evaluation, or user-facing behavior.

## Phase-relative completeness

An artifact is complete when:

- decisions belonging to its declared abstraction level are resolved;
- dependencies on other slices have a named canonical owner;
- later-phase questions are explicitly routed;
- it is coherent with approved upstream artifacts;
- its acceptance criteria are satisfied.

A later-phase unknown is not a defect merely because it remains undecided.

## Unknown classification

Every unresolved question is classified immediately.

### Current-scope decision

The answer changes semantics owned by the current artifact and is required for completion. Resolve it within delegated authority or escalate if it is human-reserved.

### Cross-slice dependency

Another bounded slice owns the answer. Record:

- what input/semantic guarantee is required;
- the canonical owning slice/artifact;
- any assumption the current slice needs;
- whether the dependency is already satisfied.

Do not define the provider slice internally.

### Later-phase decision

The question belongs to a later abstraction level such as architecture, data/feature design, model design, verification/experimentation, or implementation. Record the intended owner/phase and continue.

## Work sequence

### Wave 0 — Project/research skeleton

Establish only the shared direction needed to assign later semantic ownership:

- project vision and thesis continuity;
- primary prediction/research problem at product level;
- core scope, future extensions, and non-goals;
- information philosophy;
- conceptual use flow;
- initial context/slice map.

Do not define exact observation timing, target construction, model formulation, schemas, architecture, or implementation.

### Bounded analysis waves

Each task owns one coherent semantic area, for example:

- thesis legacy evidence;
- race observation/state semantics;
- pit-event/target/censoring semantics;
- prediction-output/replay semantics;
- evaluation/backtesting semantics.

Slices may proceed in parallel only when their ownership boundaries are distinct and upstream dependencies are explicit.

### Integration gate

After the relevant slices are independently approved, run a bounded cross-slice consistency review covering shared time semantics, identities, target/output compatibility, censoring/evaluation compatibility, leakage constraints, and ownership.

The gate does not perform a fresh internal review of every slice.

### Architecture and detailed design

Only after semantic integration is approved may work decide technical structure such as packages, interfaces, data representations, runtime boundaries, storage, APIs, feature/data pipelines, and detailed algorithms.

### Verification baseline

Define reference scenarios, backtest checks, leakage tests, acceptance fixtures, statistical checks, and other evidence needed to prove the approved semantics/design before or alongside implementation as appropriate.

### Implementation

Implementation tasks build against approved semantic/design artifacts. Local engineering choices are delegated, but approved prediction meaning, information availability, target semantics, evaluation guarantees, and other material contracts may not change silently.

## Branch model

Use short-lived branches from `main`, for example:

- `spec/<bounded-slice>`
- `integrate/<wave>`
- `design/<bounded-slice>`
- `verify/<bounded-slice>`
- `impl/<bounded-slice>`

Merge through pull requests. Do not use the thesis branches as V2 integration branches.

## Historical thesis branches

`main`, `training_rf`, `training_svm`, and `cleaning` are historical evidence/source material for the thesis-era work. During specification work:

- inspect them as evidence when a task requires it;
- cite or summarize relevant findings in `legacy/` or the owning specification;
- do not merge them together;
- do not rewrite/delete historical code or notebooks;
- do not treat legacy behavior as authoritative V2 semantics.

## Semantic locks

Once an artifact/decision is approved, later work may consume it but must not redefine it implicitly. A material change requires a bounded reconciliation/decision task identifying the affected artifacts and consequences.

## Stop rule

A normal slice receives one full independent review and one bounded re-review after rework. If substantive blockers remain, split/rescope the slice, move lower-level concerns to the correct later phase, change acceptance criteria explicitly, or escalate a human-reserved decision. Do not begin an unlimited review loop.
