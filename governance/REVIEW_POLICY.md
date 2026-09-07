# Review Policy

Independent review finds real defects without creating an unlimited specification loop.

Review an artifact against its declared scope, abstraction level, acceptance criteria, approved upstream decisions, and canonical dependencies.

## Review sequence

1. **Full scoped review** — inspect the complete declared artifact and report defects within scope.
2. **Rework** — address accepted findings or explicitly route findings that belong elsewhere.
3. **Bounded re-review** — verify prior findings, regressions caused by rework, and the original acceptance criteria.

The bounded re-review is not a fresh unlimited red-team pass.

## Finding severity

### Blocking

Use only when:

- a current-scope acceptance criterion cannot be satisfied;
- normative statements at the current abstraction level contradict each other;
- the slice invents semantics owned elsewhere;
- the slice contradicts an approved semantic lock;
- a required current-level semantic is genuinely missing and cannot be routed.

A later-phase question is not Blocking merely because it is unresolved.

### Major

A substantial current-scope defect that makes the artifact materially incomplete or misleading without invalidating the entire outcome.

### Minor

A localized clarity, naming, traceability, or presentation defect without material semantic ambiguity.

### Observation

A non-blocking suggestion or future improvement.

## Review boundary

A reviewer may reject a slice for being wrong at its declared abstraction level. A reviewer may not require architecture, implementation, arbitrary algorithms, exact schemas, or exhaustive empirical tuning merely to make an earlier semantic artifact feel more complete.

If proof requires later-phase work, route a verification/design requirement instead.

## Integration review

Integration review checks only cross-slice composition: ownership, terminology/identity, time semantics, target/output compatibility, censoring/evaluation, leakage guarantees, and dependency direction. It does not reopen approved internal semantics without a demonstrated contradiction.

## Non-convergence

If substantive blockers remain after the bounded re-review, stop the loop and split/rescope/escalate the work before any new review cycle.
