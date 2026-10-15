# Reproduce the race-context comparison

Restore the exact private canonical/source archives described in
research/expanded-pre2026/DATASET.md and the original source archive described in
research/model-comparison/DATASET.md. Historical experiments need not rerun.

```sh
python -m pip install -r research/race-context/requirements.txt
python -m unittest discover -s pipeline/tests -v
python -m pipeline.race_features
PYTHONPATH=. python research/race-context/complete_feature_policy.py
python -m pipeline.race_feature_verify
```

An independent reviewer must verify the generated private feature evidence and
write FEATURE_REVIEW.json. It binds both audit files, not merely a claimed PASS.
The author must not create this attestation. Keep protocol registration committed
before execution. Then:

```sh
python -m pipeline.race_context
```

Each completed season has input/code/registration identities, forest artifacts,
predictions, scores, practical diagnostics and hashes. Forecasts are persisted
before each later validation outcome opening; the ledger records actual reads.
Resume checks the exact configuration and every saved payload. A changed procedure
requires a new output directory and registration; never reuse a stale completion.
Fixed tree count/depth and optimizer settings bound computation. There are no
network requests in this comparison and no unbounded wait loops.

Large feature/source/run payloads remain private. Git holds implementation,
methods, review records and aggregate findings. Forest joblib artifacts require
the pinned dependencies; load only this experiment's verified artifacts. Saved
forest hashes bind the model metadata. The final refit records exact training scope.
No new 2026 reads, final evaluation, viewer installation or automatic merge.

## Identity repair during execution

Independent implementation review found two provenance defects before pooled
selection: the original runner omitted comparison_models.py from its cache code
hash, and its selection record did not directly bind all inputs/fold completions.
Numerical code, fixed parameters and inputs were unchanged. Original fold configs,
execution hashes, model IDs and predictions are retained exactly.

The input-freeze and fold-input-binding supplements bind missing dependencies,
all133 input manifests/features, reviewed admission and the checked old full-data
baseline refit. The latter must match the preserved #56 DELIVERY hash, training
list and cutoff. The independent reviewer checks this explicit repair. The final
delivery-complete manifest binds original execution plus supplements and refit.

The original runner source and11 module hashes are retained under execution/.
Local execution revision d132510 is an execution-time identifier, not a GitHub
commit link. Portable verification uses those exact saved source bytes/hashes.
The updated runner includes transitive dependencies and input/fold bindings from
the start. It rejects old cache identities by default. The explicit
--resume-original-execution option accepts only the proved unchanged numerical
core and identical input configuration, retaining a separate identity-upgrade
record. It never silently rewrites an old completion config or model identity.

Completed runs are immutable: invoking the updated runner on a completed delivery
verifies its bound payloads and exits without rewriting summaries, selections,
refit models or artifact IDs. Use a new output path for a new execution.
