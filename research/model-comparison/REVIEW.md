# Independent review of issue 53 execution

Reviewer: /root/review_model_comparison.

## Full scoped review: FAIL

Initial substantive head: 0e193e3ada7683e349d49508f42fd768020701b3.
Twenty comparison tests passed, but additional independent reproductions found
five Major defects. No Blocking or Minor findings.

1. Complete/quasi separation could pass logistic fitting.
2. Shared missing resolvable forecasts could still select a winner; pair labels
   did not enforce complete cohorts and whole-run validity.
3. Labels and joins lacked initialization and resolution-run lineage checks.
4. Resume identity omitted transitive helpers and actual numerical versions.
5. Registered PIT and protocol truncation diagnostics were incomplete.

B0 fitting, percentage integration, floor/open-tail treatment, chronology,
causal forecast inputs, source checks and bounded retries passed inspection.
The reviewer read no protected source, target or evidence file.

## Rework

Separation is checked by a bounded feasibility optimization. Full resolvable
cohort coverage and valid runs gate selection/primary pairs. Additive projection
fields preserve exact episode, initialization-run and resolution-run lineage.
All four transitive modules and the actual pinned runtime versions bind resume
identity. Required PIT and truncation diagnostics are recorded; the target-owned
visit-context dependency remains explicitly unavailable.

Canonical observations/targets are losslessly packed, their old hashes preserved
in the imported manifests, and the corrected comparison is evaluation-2.

## Bounded re-review

PASS on substantive local head a86ad01e748e7e5fea4ac7c4c8edcc89cbb0b9f5.
No Blocking or Major findings remain. Verified all 60 Python tests, all four
cached folds, all 39 packed dataset hashes and lossless canonical payloads, all
81,851 normalized/floored forecasts, exact B1 fallback equality, and the report's
counts, scores, intervals and phase results.

The sole Minor clarification exposes the already-computable sensitivity deltas
in REPORT.md. It changes no estimator, cohort, frozen result or conclusion.
Frozen artifacts preserve the exact execution code/content hashes. Local review
commit IDs are provenance strings; the GitHub review anchors the published tree.
GitHub independent review: [PASS](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/pull/55#pullrequestreview-5517455205), anchored to c1772682ae7f1cac4fef8b1d095db62d09856aee. The later commit records this link only.
