# Expanded issue 53 reproduction

Use Python 3.12, NumPy 2.3.5 and SciPy 1.17.0, pinned in
research/model-comparison/requirements.txt. Recover the original private #55 ZIP
as specified in research/model-comparison/DATASET.md. The private archives in DATASET.md
contain additional raw and canonical payloads; Git holds their manifests,
model artifacts, admission evidence, summaries and ledger.

```sh
python -m unittest discover -s pipeline/tests -v
python -m pipeline.expanded_sources acquire --workers 6
python -m pipeline.expanded_sources verify
```

Acquisition resumes verified complete endpoints and records every unavailable
session. Verification must finish all 173 sessions before independent admission
review. Never add the review attestation yourself. It binds the complete evidence
and code identity, so changes to admission invalidate the gate.

After recovering the independently reviewed evidence and committing registration:

```sh
python -m pipeline.expanded_data
python -m pipeline.expanded_comparison
```

The first command imports the frozen 39-race canonical dataset unchanged and
reconstructs newly admitted sessions separately. Each race saves full canonical
artifacts plus separate causal checkpoint and outcome files. The second command
uses rolling seasons, predicts validation races before their label joins, keeps
all attempts/failures, and resumes only folds whose input/code/model hashes match.
After selecting a supported full-cohort procedure it freezes selection/thresholds
and refits on all admitted pre-2026 races. It does not create a final evaluation
lock or read 2026.

Both commands persist progress. Source requests have finite timeouts/retries and
optimizer iterations are bounded. Changed code or input identities require a new
output path rather than reuse of a stale completed fold. No output overwrites the
old #55 comparison, #56 saved-run diagnostic or viewer model.
