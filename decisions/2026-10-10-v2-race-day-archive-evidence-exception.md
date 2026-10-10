# Decision: Evidence-standard exception for race-day-written live-timing archives

- **Status:** Approved
- **Date:** 2026-10-10
- **Owner:** Product Owner
- **Affected artifacts:** `verification/SUPPORT_MATRIX.md` (#35); `design/OBSERVATION_RECONSTRUCTION.md` (#18 availability-authority validation), consumed unchanged except for this documented exception

## Question

No historical race session has availability-authority evidence that meets #18's stated standard: provider documentation, contractual implementation, paired contemporaneous captures, or an equivalent independently reproducible fixture. How should V2 historical backtesting proceed?

## Decision

**Option B is approved.** The governance exception is documented here.

- **Scope covered.** F1 live-timing static archive files written on race day: race sessions whose archive files were last modified on the race date or the next UTC day. This was 2024 R10 onward at decision time.
- **Classification.** These scopes may be classified as **`VERIFIED_BOUNDED_TIME`** on the basis of reproducible internal-consistency evidence from the archive itself. Contemporaneous capture is **not** required, provided the verification artifact:
  1. states the residual assumptions explicitly;
  2. derives conservative availability bounds from a validated error model;
  3. excludes windows where clock integrity cannot be shown; and
  4. obtains independent review.

Under this decision, archive files rewritten long after the event (the June 2024 bulk rewrite) remain `UNVERIFIED_ARCHIVE`.

## Rationale

The Product Owner chose to proceed now on the race-day-written corpus (about 55 races at decision time). The alternatives were waiting for live captures, or gating final claims on them. The Product Owner accepted a weaker, assumption-based leakage guarantee in exchange for progress.

## Consequences / semantic locks

- This is a **governance exception to #18's evidence standard only**. The point-in-time semantics themselves do not change: availability time, not occurrence time; fail-closed handling; and the bounded-time admission rule.
- Results built on this scope must carry the residual assumptions in their provenance, and reports must state that the authority rests on this exception.
- Primary final claims are **not** gated on contemporaneous capture. Capture remains a recommended way to strengthen the evidence later.
- The exception does **not** extend to rewritten archives, unretrievable seasons, endpoints without evidence in the verification artifact, or windows the artifact marks clock-unhealthy.
- A later contemporaneous capture that contradicts the archive's timestamp meaning or revision fidelity voids this exception for the affected scope, until the matrix is re-verified.

## Alternatives considered

- **A:** capture the remaining 2026 races first and validate before any backtesting.
- **C:** approve B for development, but require capture validation before any primary final claim.

## Follow-up

- Rework `verification/SUPPORT_MATRIX.md` (PR #38) under this decision and address the full-review findings. Then run one bounded re-review.
