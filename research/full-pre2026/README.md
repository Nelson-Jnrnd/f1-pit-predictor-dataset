# Issue 53 follow-up reproduction

Start from PR #55 and recover its exact private evidence archive as described in
research/model-comparison/DATASET.md. Verify the ZIP SHA-256 before extraction.
Use the existing Python 3.12 / NumPy 2.3.5 / SciPy 1.17.0 dependency lock.

From repository root:

```sh
python -m pipeline.historical_audit --output /tmp/pre2026-audit.json
python -m unittest discover -s pipeline/tests -v
python -m pipeline.practical_metrics --dataset research/model-comparison/dataset-2 --saved research/model-comparison/evaluation-2 --output /tmp/practical-diagnostics
python -m pipeline.tyre_fit_diagnostic --dataset research/model-comparison/dataset-2 --saved research/model-comparison/evaluation-2 --output /tmp/tyre-diagnostics
```

No acquisition or previous experiment rerun is needed. Practical metrics verify
saved forecast hashes, exact checkpoint/model coverage and source dataset manifest
identities before their separate development-label joins. Additional ledger files
record development openings. All guards retain the 39-race allowlist. The broader
scope remains a declared plan pending admission, not an implemented guard bypass.

The audit reports CSV files and row/identifier overlap without assuming one file
is one distinct verified race. The archive census is the saved 2026-10-10 metadata,
not a fresh availability claim. Every admitted raw endpoint is hash-checked.

The tyre investigation repeats only training fits to diagnose their components.
Its mean-loss optimization probe emits numerical diagnostics, no model artifact
or forecast. It does not change B1 or reuse a probe as a repaired candidate.

Results: REPORT.md, audit.json, practical-2/summary.json and
tyre-diagnostic-1/summary.json. REVIEW.md records the independent outcome.
