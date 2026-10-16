# Independent implementation, result and recovery review

Outcome: PASS for the recovered delivery after one bounded re-review. No open
Blocking, Major or Minor findings remain. This is not certification that the lost
historical root evidence was restored. It does not approve merge, viewer
replacement, deployment or final evaluation.

Reviewer: independent agent `/root/hypothesis_result_review`.
Full scoped review: 15 October 2026. Bounded recovery re-review: 16 October 2026.
Task: [issue #59](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/issues/59).
Review record: [PR #60](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/pull/60).
Passing independent review: [GitHub review5543609802](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/pull/60#pullrequestreview-5543609802),
anchored to published recovery head `ed58ccfd3a7a58cb59d3a7d95019db4056ef828f`.
Protocol PASS: [GitHub review5538828668](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/pull/60#pullrequestreview-5538828668).
This final link update changes review metadata only.

## Scope and findings

The full review covered the registered H1 through H4 procedures, numerical
implementation, chronological evaluation, weighting, causal inputs, target and
complete probability output, matched cohorts, selection, thresholds, reports and
saved results. It also covered the fixed orchestration and B0 metadata helper.
Numerical source bytes remain those bound by the original inputs; recovery does
not retrain any validation candidate or change the registered procedures.

One Major finding concerned the original final refit: its recorded scope had
133 races but its actual-read ledger had only 132 entries, missing 2020 R13.
The reviewer did not certify that original final delivery. The proposed repair
was interrupted by an execution-service outage; a later workspace reset lost
separate root evidence. No missing historical entry or timestamp was invented.

The bounded re-review checked this finding, the declared recovery and its caused
regressions. A separate frozen H1 final refit now has complete checked evidence.
The earlier localized B0 metadata persistence gap is resolved by exact-identity
reconstruction. Completed recovery verification exits without writes. The report
now distinguishes surviving candidate evidence, lost historical records and new
recovery records. These resolve the findings without a new candidate search.

## Candidate results retained from the full review

The four candidate archives preserve their validation models, forecasts, scores
and fold hashes. All procedures have 130,836 attempts and the same 93,650 scored
checkpoints across 115 races. There are 122,816 eligible forecasts and 29,166
unknown outcomes; unknowns are not converted to no-stop outcomes.

The prior independent checks covered matched cohorts, saved model forecast
reproduction, score identities, primary aggregation, threshold selection and
confusion counts. The original reviewer scratch files were lost; those checks
remain recorded conclusions, not newly restored scratch evidence. Recovery
rechecks the surviving fold/input bindings and reproduces the aggregate scores.

| Procedure | Mean log score | Earlier-season alert threshold | 2025 TP / FP / FN / TN |
| --- | ---: | ---: | --- |
| RF_CONTEXT | 2.169202 | 0.24 | 908 / 2,293 / 1,140 / 20,333 |
| H1_PERCENT | 2.161464 | 0.23 | 951 / 2,478 / 1,097 / 20,148 |
| H2_DETAIL | 2.293525 | 0.29 | 965 / 2,442 / 1,083 / 20,184 |
| H3_BOOST | 2.257591 | 0.24 | 960 / 2,360 / 1,088 / 20,266 |
| H4_RECENT | 2.229888 | 0.27 | 767 / 1,864 / 1,281 / 20,762 |

The registered paired race-cluster standard-error rule selects H1_PERCENT, also
the raw lowest score. Its gain over RF_CONTEXT is 0.007738 with a 95% race-cluster
interval of -0.002720 to 0.018196. This is a small uncertain development gain.
Its 2025 precision is 27.7%, recall 46.4%, and 2,478 of 3,429 known-outcome alerts
are false. Better probability scoring does not establish useful alerts.

## Independently verified replacement final refit

The recovered inputs reproduce the exact original SHA-256
`648f012d1c3894f5c22f347daca40ccc88a5910f76f0ddfde0a5c926fd15ecb2`.
Every numerical module matches that input record. The new freeze binds the
reconstructed summary and unchanged H1 selection before any replacement fit read.

I independently checked exactly 133 unique ordered before-read intents and 133
actual-read entries against the complete admitted partition. Every manifest and
resolution hash matches; all reads concern pre-2026 races and follow the new
selection freeze. The previously missing 2020 R13 is present in this new ledger.
The helper persists the intent before opening labels and checks the actual ledger
after every race. These are new actual reads, not replacement historical dates.

The model and B0 artifact digests, full training scope, terminal allocation,
64-tree forest and fixed parameters pass. Training retains 55,400 positive and
1,239,034 negative periods, with 150,000 sampled negatives weighted by their
inverse inclusion probability. The estimator SHA-256 is
`e910da39d02513ee567bd1d7acdcaccaadd60f83cb0dbc448b7245a5dcdd40a1`,
which matches the previously recorded original digest. The original estimator
payload is unavailable, so this does not restore it or its historical ledger.

All six reconstructed H4 B0 artifacts exactly match the archived models' B0_ref,
q_open, k_terciles and declared two-season training scopes. Their complete new
read/intention ledgers contain only pre-2026 races. The new final H1 B0 artifact
is saved directly with the replacement fit.

All 670 payload hashes in recovery-complete.json pass. Its SHA-256 is
`dca1fb7d4ba3a849205e7812d683c9843ab39c12e9f5d6ba78695b4ece81c3df`.
Running `python research/hypotheses/recover_delivery.py verify` independently
preserved every output file's size and modification time. Bounded verification
scripts, logs and JSON results accompany the new private review evidence.

## Limits of this approval

REPORT.md states the recovery and practical limitations plainly. The original
root opening ledger, completion manifests, final selected-model payload,
interruption/parity records, stdout-repair evidence and reviewer scratch records
were lost. Historical prediction-before-label ordering and interruption parity
cannot be re-audited from the restored files. New source snapshots, ledgers and
completion hashes certify the recovery rather than those lost historical facts.

All model comparisons remain exploratory development, including 2025. The
intervals omit training and selection uncertainty. Archive assumptions and
unknown-outcome limitations still apply. The review did not open protected 2026
source, outcome or capability evidence. Prior exposure and final-test locks remain
unchanged. The recorded 98-test suite passes; this bounded re-review additionally
checked the replacement fit, reconstructed metadata and immutable recovery resume.
