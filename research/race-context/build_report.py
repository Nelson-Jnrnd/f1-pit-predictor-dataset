"""Plain-language report from frozen results only; does not fit or select models."""
import json
from pathlib import Path

root=Path(__file__).parent
s=json.loads((root/'evaluation/summary.json').read_text())
chosen=s['selected'];names={'B0':'Lap baseline','PERCENT_PROGRESS':'Race progress','TYRE_RIDGE':'Stable tyre baseline',
    'RF_GRID':'Random Forest: timing','RF_TYRE':'Random Forest: timing + tyres','RF_CONTEXT':'Random Forest: tyres + pace/traffic'}
pr=s['practical'][chosen];alert=pr['diagnostic_2025'];counts=alert['checkpoint'];raw=s['raw_best']
pct=lambda v:'undefined' if v is None else f'{100*v:.1f}%'
metric=lambda n,k:f"{s['models'][n][k]:.6f}"
text=f'''# Does richer race information improve pit-stop prediction?

The richer Random Forest beats the simple baselines on probability scoring.
The selected procedure is **{names[chosen]} ({chosen})**. Its chronological
validation log score is **{metric(chosen,'mean_log_score')}**, compared with
**{metric('B0','mean_log_score')}** for the lap baseline and
**{metric('PERCENT_PROGRESS','mean_log_score')}** for race progress. Lower is better;
these values are probability penalties, not percentage accuracy.

On the exploratory 2025 alert diagnostic, **{counts['FP']:,} of
{counts['TP']+counts['FP']:,} alerts are false**. Precision is **{pct(counts['precision'])}**
and recall is **{pct(counts['recall'])}**. The threshold is fixed using earlier
seasons. These figures describe alerts at successive checkpoints, so one stop
can trigger several alerts. It still raises frequent false alerts and misses many positive checkpoints.
Its practical value remains limited. This does not establish 2026 performance.

## Exactly what was compared

| Procedure | Inputs available at the checkpoint | Mean log score |
| --- | --- | ---: |
| Lap baseline | Laps ahead; grid length | {metric('B0','mean_log_score')} |
| Race progress | Fraction of scheduled race completed | {metric('PERCENT_PROGRESS','mean_log_score')} |
| Stable tyre baseline | Causal tyre age/compound and race progress; fixed logistic model | {metric('TYRE_RIDGE','mean_log_score')} |
| RF_GRID | Completed/scheduled laps, race progress and future offset | {metric('RF_GRID','mean_log_score')} |
| RF_TYRE | RF_GRID plus current compound and projected tyre age | {metric('RF_TYRE','mean_log_score')} |
| RF_CONTEXT | RF_TYRE plus completed-lap pace, last-minus-best pace, rank, numeric gaps | {metric('RF_CONTEXT','mean_log_score')} |

All forests use64 trees, depth at most12 and at least100 sampled rows per leaf.
Settings are fixed; no validation tuning search was run. Negative training-period
sampling is corrected by weights. There are no balanced class weights, learned
imputation or fitted probability calibration. The full timing distribution has
explicit no-stop probability; it is not an arbitrary conversion of a binary score.

The raw lowest score belongs to **{names[raw]}**. The registered rule selects
**{names[chosen]}** after allowing for race-level uncertainty and preferring the
simpler procedure within one standard error. Selection does not establish utility.
Original B1 remains unsupported. B1-R0, historically called B-thesis, is only a
B1 diagnostic and is not the historical Random Forest. Historical result IDs stay
unchanged. [Thesis and feature audit](THESIS_AND_FEATURES.md) identifies the pinned
historical evidence and exact retained/excluded features.

## What the added information contributed

The following matched comparisons use the identical complete resolvable cohort.
Positive differences favour the model in the second column. Intervals group
checkpoints by race and are conditional on these fitted procedures.

| Compared procedure | Added-information procedure | Log-score reduction | 95% race-cluster interval |
| --- | --- | ---: | --- |
'''
for a,b in [('RF_GRID','RF_TYRE'),('RF_TYRE','RF_CONTEXT'),('TYRE_RIDGE','RF_TYRE'),('PERCENT_PROGRESS','RF_GRID')]:
 d=s['pairs'][a+' vs '+b]['difference_a_minus_b'] if a+' vs '+b in s['pairs'] else None
 if d is None:
  d=s['pairs'][b+' vs '+a]['difference_a_minus_b'];v=-d['mean'];ci=[-d['cr2_95'][1],-d['cr2_95'][0]]
 else:v=d['mean'];ci=d['cr2_95']
 text+=f'| {names[a]} | {names[b]} | {v:.6f} | {ci[0]:.6f} to {ci[1]:.6f} |\n'
text+='''
Tyres provide a clear improvement. The smaller extra gain from pace/traffic
has a race-level 95% interval spanning zero, so that added value remains uncertain.
The nested forest comparisons isolate tyre information and the pace/traffic group.
The stable-tyre-versus-forest comparison also changes the estimation procedure.
The timing-baseline comparison changes the available grid representation as well
as the model. Feature importance alone is not used as evidence of improvement.

## Training and evaluation scope

All133 admitted pre-2026 races support the declared features, including explicit
missing values. Training uses earlier races; validation uses every admitted race
in the next season. No random split of laps or drivers is used. Existing raw and
canonical evidence, prior source assumptions and all #55/#56 results are preserved.
Legacy CSVs do not enter training. No eventual wet-running, completion or stop-count
filter is introduced. Circuit, stint ordinal, track status and weather are omitted
for the reasons in the feature audit; unsupported data are not fabricated.

| Validation season | Earlier training races | Later validation races | Scored checkpoints per procedure | Unknown share of eligible target cohort |
| --- | ---: | ---: | ---: | ---: |
'''
folds={2019:(18,19),2020:(37,12),2021:(49,16),2023:(65,21),2024:(86,23),2025:(109,24)}
for y,(nt,nv) in folds.items():
 ss=s['by_season'][str(y)];t=ss['truncation'][chosen]['overall']
 text+=f"| {y} | {nt} | {nv} | {ss['models'][chosen]['scored']:,} | {pct(t['share'])} |\n"
ms=s['models'][chosen];window=pr['validation'];w=window['window_width'];cov=window['conditional_window_coverage'];absw=window['absolute_window_coverage']
text+=f'''
Every procedure forecasts **{ms['forecast_count']:,} / {ms['eligible']:,} eligible
validation checkpoints** and is scored on **{ms['scored']:,} identical resolved
checkpoints** across115 races. Each model retains the full attempt accounting.
There are no restricted feature-cohort winners or missing model forecasts.
Unknown/truncated outcomes stay unknown and are never no-stop negatives. Results
describe the resolvable population. Prior validation exposure makes these further
comparisons development, not fresh confirmation.

## Alert performance in2025

An alert concerns qualifying tyre-service entry in the first up to three canonical
regions: usually the current lap and next two. For short grids, the last region
is open-ended. The same definition is used for every model.

| Model | Earlier-season threshold | Precision | Recall | F1 | False alerts |
| --- | ---: | ---: | ---: | ---: | ---: |
'''
for n in s['models']:
 a=s['practical'][n]['diagnostic_2025'];cc=a['checkpoint']
 text+=f"| {names[n]} | {a['threshold']:.2f} | {pct(cc['precision'])} | {pct(cc['recall'])} | {pct(cc['f1'])} | {cc['FP']:,} |\n"
u=alert['unique_stops']
text+=f'''
Selected-model confusion: **{counts['TP']:,} correct alerts**, **{counts['FP']:,}
false alerts, **{counts['FN']:,} missed positive checkpoints**, and
**{counts['TN']:,} correct no-alert checkpoints**. Positive prevalence is
{pct(counts['prevalence'])}. Always alerting yields that precision and100% recall;
never alerting yields0% recall and undefined precision. Accuracy alone would hide
this imbalance. All99 probability thresholds and their precision/recall/confusion
tradeoffs are retained in the saved results.

There are **{alert['false_alerts_per_driver_race']:.1f} false checkpoint alerts per
eligible driver-race** across{alert['eligible_driver_races']:,} driver-races.
At least one alert detects **{u['detected']:,} of{u['with_known_horizon_checkpoint']:,}**
identifiable stops with known in-horizon evidence. There are
**{u['repeated_positive_alerts']:,} repeated positive checkpoint alerts**.
Stops without known horizon evidence remain outside this separate diagnostic.
The2025 binary cohort has{counts['n']:,} known outcomes,
{counts['unknown_binary']:,} unknown eligible outcomes and
{counts['excluded_attempts']:,} excluded attempts. Missing forecasts for known
binary outcomes:{counts['missing_forecast_known_binary']:,}.

The diagnostic threshold uses validation seasons through2024 only;2025 was already
exposed in previous development and remains exploratory. A separate final threshold
of**{pr['final_threshold']['threshold']:.2f}** uses all pre-2026 validation forecasts.
Its confusion counts are in-sample threshold-selection statistics, not the2025
figures above. No final-test outcomes influenced either threshold.

## Calibration and timing windows

The selected model's short-horizon Brier score is**{window['brier_p3']:.6f}**,
versus**{s['practical']['B0']['validation']['brier_p3']:.6f}** for the lap baseline.
Lower is better. Reliability tables for short-horizon probability, first-region
probability and no-event probability are saved; no probability correction was fitted.

The median pit window spans**{w['quantiles']['median']:.0f} regions**
(middle half{w['quantiles']['p25']:.0f}–{w['quantiles']['p75']:.0f}).
Conditional event coverage is**{pct(cov['observed'])}**, versus
**{pct(cov['expected'])}** mean predicted conditional mass. Absolute window coverage
is{pct(absw['observed'])}, versus{pct(absw['expected'])} predicted mass.
Open-ended windows account for{pct(w['open_ended_share'])}; they have no finite
upper lap-width bound. Wider windows can increase coverage while saying less
about when a stop will occur.

Paired log-score evidence includes CR2+t intervals,9,999 Webb draws with fixed seed
and leave-one-race-out influence checks. Alert-share and Brier uncertainty, per-race
confusion and leave-one-race-out ratios remain saved. Checkpoints are not treated
as independent stops. LOW_POWER and the historical archive assumptions remain
explicit; intervals do not include training variability.

## Frozen model and review status

Selection and alert thresholds were frozen before full-data refitting. The selected
procedure was fitted on all133 admitted races with cutoff2026-01-01. B0's existing
byte-verified full-data refit is reused with exact scope/DELIVERY checks. Model
artifacts, source feature evidence, predictions, targets opened in the actual read
ledger, full metrics, input/fold bindings and final completion hashes are retained
in private evidence. The explicit provenance repair is described in README.md;
original execution/model identities are not relabelled.

No new2026 source or outcome was read. Existing R1–R16 prior exposure declarations,
P-F1/P-F2 final lists and lock gates remain binding. No EvaluationLock, deployment,
viewer replacement or merge was performed. Independent protocol/source review is
recorded in PROTOCOL_REVIEW.md and FEATURE_REVIEW.md; implementation/result review
is recorded separately in REVIEW.md. Review PASS alone does not mean useful
prediction quality.
'''
# Keep generated prose spaced even around exact numeric literals.
import re
text=re.sub(r'(?<=[A-Za-z]{2})(?=\d)', ' ',text)
text=re.sub(r'(?<=\d)(?=[A-Za-z])', ' ',text)
text=text.replace('of**','of **').replace('is**','is **').replace('for**','for **')
(root/'REPORT.md').write_text(text)
print('Report generated from frozen summary')
