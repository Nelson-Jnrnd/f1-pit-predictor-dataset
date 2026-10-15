"""Summarize frozen experiment evidence without opening raw or final-test data."""
from pathlib import Path
import hashlib,json,collections
base=Path(__file__).resolve().parent
read=lambda p:json.loads((base/p).read_text())
sha=lambda p:hashlib.sha256((base/p).read_bytes()).hexdigest()
names={'B0':'Laps ahead','B1':'Original tyre model','PERCENT_AHEAD':'Percentage ahead','PERCENT_PROGRESS':'Race progress','TYRE_RIDGE':'Stable tyre model'}
v=read('evaluation/summary.json');sel=v['selected'];pr=v['practical'];s=pr[sel];diag=s['diagnostic_2025'];cp=diag['checkpoint'];b=pr['B0']['diagnostic_2025'];bc=b['checkpoint'];ad=read('admission/verify.json');refit=read('evaluation/all-pre2026-refit.json')
manifest=[json.loads(p.read_text()) for p in sorted((base/'dataset').glob('*/manifest.json'))]
counts=collections.Counter(m['race']['season'] for m in manifest);outcomes=collections.Counter()
for m in manifest:outcomes.update(m['outcomes'])
pct=lambda x:'Undefined' if x is None else f'{100*x:.1f}%'
w=s['validation']['window_width'];cov=s['validation']['conditional_window_coverage'];absolute=s['validation']['absolute_window_coverage']
text=f'''# Expanded pre-2026 model comparison

## Result

The registered rule selects **{names[sel]} ({sel})**. Its pooled mean validation
log score is {v['models'][sel]['mean_log_score']:.6f}, compared with
{v['models']['B0']['mean_log_score']:.6f} for the lap baseline. Lower is better.
This is a probability penalty, not a percentage accuracy.

On the exploratory 2025 alert diagnostic, precision is {pct(cp['precision'])} and
recall is {pct(cp['recall'])}. Its threshold uses earlier validation seasons only.
These are development findings under the approved archive assumptions. They do
not establish 2026 performance. The current viewer remains unchanged.

## Data audit and chronological split

All 173 calendar sessions before 2026 were audited. The fixed list admits 133:
94 older raw archives and 39 frozen race-day sessions. Forty are excluded:
22 unavailable 2022 sessions, 13 counter failures, two roster failures, one
lifecycle failure and two previously unsupported 2018 races. Every exclusion stays
in admission/verify.json. No inaccessible race or missing stream is fabricated.

The separate CSV audit covers 109 files: 104 race exports and five overlapping
season exports. No CSV enters training. Same-row PitStatus does not identify the
next qualifying tyre-service entry, and final TyreLife or TotalLaps cannot establish
what was available earlier. Historical raw compound names outside the declared
categories map to OTHER. Stint age uses causal TimingAppData updates.

| Validation season | Earlier training races | Validation races |
| --- | ---: | ---: |
| 2019 | 18 | 19 |
| 2020 | 37 | 12 |
| 2021 | 49 | 16 |
| 2023 | 65 | 21 |
| 2024 | 86 | 23 |
| 2025 | 109 | 24 |

2018 supplies initial training only. Each subsequent fold trains on every admitted
earlier race and predicts the later season before joining its labels. Validation
covers 115 races. No random split of checkpoints or drivers is used. No 2022 fold
exists because those archives were unavailable. The final refit uses all 133 races.

The canonical dataset contains {sum(m['checkpoints'] for m in manifest):,} attempts,
{sum(m['labels'] for m in manifest):,} eligible labels, and
{outcomes['NOT_REALIZED']:,} unknown outcomes. Unknown outcomes never become
negatives. There are {sum(m['unique_events'] for m in manifest):,} distinct qualifying
events identified by at least one resolved checkpoint. Several checkpoints can
refer to the same stop. They do not create independent stop events.

## Models and probability scores

B0 learns typical timing by laps ahead. Percentage ahead scales future distance
by scheduled race length. Race progress uses the fraction of the race completed.
Original B1 adds causal tyre age and compound. Its original fitting rules remain
unchanged. The separate stable tyre candidate uses the same tyre hazard features,
a fixed ridge penalty of 0.001 and B0's empirical final no-event share. No validation
search selected that penalty. Python 3.12, NumPy 2.3.5 and SciPy 1.17.0 fit the models.

| Model | Forecasts / eligible | Scored checkpoints | Mean log score |
| --- | ---: | ---: | ---: |
'''
for n in ('B0','B1','PERCENT_AHEAD','PERCENT_PROGRESS','TYRE_RIDGE'):
 m=v['models'][n];score='Unsupported; partial fallback' if m['fitting_failures'] else f"{m['mean_log_score']:.6f}"
 text+=f"| {names[n]} | {m['forecast_count']:,} / {m['eligible']:,} | {m['scored']:,} | {score} |\n"
text+='''
Selection uses the complete, identical resolvable cohort. It prefers the simplest
procedure within one race-level standard error of the best score. B1 lacks a
supported full-cohort fit, so the predeclared expanded protocol uses B0 as reference.
B1 failures and unmatched counts stay visible. A smaller fallback cohort cannot win.
'''
diff=v['pairs'].get('B0 vs '+sel,{}).get('difference_a_minus_b')
if diff:text+=f"\nB0 minus selected-model log score is {diff['mean']:.6f}, with 95% race-cluster\ninterval {diff['cr2_95'][0]:.6f} to {diff['cr2_95'][1]:.6f}. Positive values favour\nthe selected model. This interval is conditional on the fitted procedures.\n"
if diff and diff['cr2_95'][0]<=0<=diff['cr2_95'][1]:text+='\nThe interval includes no difference. This comparison does not establish a clear\nprobability-score advantage over B0.\n'
text+='''
## Practical alerts in 2025

An alert predicts a qualifying tyre-service entry in R0, R1 or R2. R0 is the current
in-lap after the checkpoint. Short grids can include their open final region, so
this is not always literally three laps of clock time. Thresholds maximize F1 on
the fixed 0.01–0.99 grid, choosing the highest tied threshold. This diagnostic
selects thresholds on validation seasons through 2024 and applies them to 2025.
Prior 2025 exposure makes it exploratory.

| 2025 diagnostic | Lap baseline | Selected model |
| --- | ---: | ---: |
'''
for label,k in [('Correct alerts','TP'),('False alerts','FP'),('Missed positive checkpoints','FN'),('Correct no-alert checkpoints','TN')]:text+=f"| {label} | {bc[k]:,} | {cp[k]:,} |\n"
for label,k in [('Precision','precision'),('Recall','recall'),('Positive prevalence','prevalence')]:text+=f"| {label} | {pct(bc[k])} | {pct(cp[k])} |\n"
text+=f'''| Earlier-season threshold | {b['threshold']:.2f} | {diag['threshold']:.2f} |

The baseline's earlier-selected {b['threshold']:.2f} threshold raises no alerts in 2025. Its
precision is undefined and recall is zero. The threshold stays fixed despite
this later result.

The selected diagnostic includes {cp['n']:,} known binary outcomes,
{cp['unknown_binary']:,} unknown eligible outcomes and {cp['excluded_attempts']:,}
excluded attempts. Missing forecasts for known binary outcomes:
{cp['missing_forecast_known_binary']:,}. Unknown outcomes never become no-stop labels.
Always alerting gives {pct(cp['prevalence'])} precision and 100% recall. Never
alerting gives zero recall and undefined precision. These counts describe checkpoints.

At least one alert precedes {diag['unique_stops']['detected']:,} of
{diag['unique_stops']['with_known_horizon_checkpoint']:,} identifiable stops with
known in-horizon checkpoints. Each event counts once. There are
{diag['unique_stops']['repeated_positive_alerts']:,} repeated positive checkpoint
alerts. Stops without identifiable/resolved horizon evidence stay outside this
diagnostic. Full missing-forecast and unique-stop accounting remains saved.

## Pit windows, calibration and uncertainty

Across validation, the selected model's median window spans
{w['quantiles']['median']:.0f} canonical regions, with middle half
{w['quantiles']['p25']:.0f}–{w['quantiles']['p75']:.0f}. Conditional event coverage is
{pct(cov['observed'])}, compared with {pct(cov['expected'])} mean predicted mass.
A wider window can catch more stops while giving less precise timing.
{pct(w['open_ended_share'])} of windows include an open final region and have no
finite upper bound in laps. Width uses region count rather than a fabricated
finite width for that tail.

Across the full scored window cohort, mean predicted hit probability is
{pct(absolute['expected'])} and observed frequency is {pct(absolute['observed'])}.
The selected three-region Brier score is {s['validation']['brier_p3']:.6f}, versus
{pr['B0']['validation']['brier_p3']:.6f} for B0. Lower is better. Reliability tables
compare predicted probabilities with observed frequencies. No calibration
correction was fitted. No-stop calibration, entropy and ranked probability scores
also remain in the saved summaries.

Uncertainty groups checkpoints by race using CR2+t intervals, Webb bootstrap and
leave-one-race-out checks. Per-season scores, truncation shares, forecast failures
and availability remain visible. Checkpoints never count as independent stops.
Results describe resolvable outcomes, not the unknown population. Sparse-cohort
LOW_POWER flags and inherited prior-exposure declarations remain binding.

## Tyre fitting investigation

The original B1 has numerical hazard failures and a final no-stop logistic
component with only one class in the saved training blocks. That component has no
finite unpenalized maximum-likelihood fit. More data alone does not repair the
registered estimator. research/full-pre2026/tyre-diagnostic-1 preserves the separate
investigation. TYRE_RIDGE is an explicitly new candidate with bounded optimization
and boundary handling, never a relabelled B1 repair. Omitted inputs or unseen
compounds use exact, counted B0 fallback. True fit failures remain failures.

## Frozen selection and refit

selection-freeze.json records the selected procedure, evidence and final alert
thresholds before refitting. The selected final threshold is
{s['final_threshold']['threshold']:.2f}, chosen on all chronological pre-2026
validation forecasts. Its pooled confusion counts are in-sample threshold-selection
diagnostics, separate from the earlier-threshold 2025 diagnostic above.

The selected model and B0 have saved fits using all 133 admitted pre-2026 races.
Training lists, input manifests, dependencies and procedure identities accompany
them. The conservative date cutoff is 1 January 2026, before the symbolic 2026 R1
boundary. DELIVERY.json binds exact admission, canonical manifests, six completed
folds, selection, refit and ledger hashes. It maps source-specific assumptions.

Older archives carry RA1–3 plus RA5/6: rewritten historical versions/order and
healthy-window clock availability remain assumptions. Race-day sources retain
RA1–4. Independent checks cannot prove every historical version or independent
tyre-change ground truth. The owner approved that evidence tradeoff. Negative or
missing tyre-service evidence remains indeterminate.

This experiment adds no 2026 source or outcome exposure. Earlier declared final-
partition exposure remains binding and must qualify later final claims.
No canonical EvaluationLock or final claim
is created. Final resolution-run identity and F2 metadata-only fixed-list resolution
remain separate gated work under the existing evaluation protocol. No merge,
deployment, public data release or viewer replacement occurred.

Independent admission/protocol review: ADMISSION_REVIEW.md. Implementation/result
review: REVIEW.md. Reproduction and interrupted-session recovery: README.md and
DATASET.md. The frozen PR #55 and earlier PR #56 diagnostic reports remain distinct.
'''
(base/'REPORT.md').write_text(text)
refs=['admission/verify.json','dataset/partition.json','REGISTRATION.md','evaluation/summary.json','evaluation/selection-freeze.json','evaluation/all-pre2026-refit.json','evaluation/ledger.jsonl']
refs += [f'evaluation/{y}/{f}' for y in (2019,2020,2021,2023,2024,2025) for f in ('models.json','complete.json','summary.json')]
refs += [str(p.relative_to(base)) for p in sorted((base/'dataset').glob('*/manifest.json'))]
assumptions=[{'race':r['race'],'assumptions':r['assumptions']} for r in ad['results'] if r['status']=='ADMITTED']
(base/'DELIVERY.json').write_text(json.dumps(dict(version='expanded-delivery/v1',status='DEVELOPMENT_ONLY',final_outcomes_opened=False,final_lock_created=False,evidence={p:sha(p) for p in refs},source_assumptions=assumptions),sort_keys=True,indent=2)+'\n')
print(base/'REPORT.md')
