"""Plain-language aggregate report derived from the immutable experiment summary."""
from pathlib import Path
from pipeline import comparison_data as data

ROOT=Path(__file__).resolve().parent
NAMES={'RF_CONTEXT':'Current forest','H1_PERCENT':'H1: Percentage inputs','H2_DETAIL':'H2: Detailed forest','H3_BOOST':'H3: Gradient boosting','H4_RECENT':'H4: Recent seasons'}


def main():
    s=data.read_json(ROOT/'evaluation/summary.json');order=list(NAMES)
    models={**s['models'],'RF_CONTEXT':s['reference']}
    pct=lambda x:f'{100*x:.1f}%' if x is not None else 'undefined'
    chosen_alert=models[s['recommended']]['practical']['diagnostic_2025']['checkpoint']
    lines=['# Four pit-prediction hypotheses', '',
        f"The lowest probability penalty is {s['means'][s['raw_best']]:.6f} from {NAMES[s['raw_best']]}. The registered uncertainty rule recommends {NAMES[s['recommended']]}. These are exploratory development findings.", '',
        f"Among exploratory 2025 alerts with known outcomes, {chosen_alert['FP']:,} of {chosen_alert['TP']+chosen_alert['FP']:,} alerts are false. Precision is {pct(chosen_alert['precision'])} and recall is {pct(chosen_alert['recall'])}. False alerts and missed stops remain material. These results do not establish dependable operational use.", '',
        '## Scores', '', '| Hypothesis | Mean log score | Improvement over current forest | 95% race-cluster interval |', '| --- | ---: | ---: | --- |']
    for n in order:
        r=s['models'].get(n);delta=r['improvement_over_reference'] if r else None
        interval=' to '.join(f'{v:.6f}' for v in delta['cr2_95']) if delta else None
        lines.append(f"| {NAMES[n]} | {s['means'][n]:.6f} | {delta['mean']:.6f} | {interval} |" if delta else f"| {NAMES[n]} | {s['means'][n]:.6f} | Reference | |")
    interpretations=data.read_json(ROOT/'INTERPRETATIONS.json')
    for n in order[1:]:lines+=['',f'{NAMES[n]}: {interpretations[n]}','']
    lines+=['', 'Lower log score is better. It measures the penalty assigned to the observed stop timing or no-stop outcome. It is not percentage accuracy. Positive improvement favours the new procedure. Every model has the same 93,650 scored checkpoints across 115 validation races.', '',
        '## Hypotheses and decisions', '',
        'H1 replaces the raw lap grid with percentage features and scales tyre age by scheduled distance. It retains inverse scheduled distance, so this tests a different representation rather than removing race-length information.', '',
        'H2 increases maximum tree depth from 12 to 20 and reduces minimum leaf size from 100 to 30. It tests both settings jointly.', '',
        'H3 uses 150 fixed gradient-boosting iterations on the same inputs. It tests a different way of fitting trees. No validation-driven early stopping or hyperparameter search occurs.', '',
        'H4 trains on the two most recent admitted earlier seasons and recomputes the terminal probability on that subset. It tests a training-history procedure, not the effect of age alone.', '',
        '## Exploratory 2025 alerts', '',
        '| Model | Threshold from earlier seasons | Precision | Recall | F1 | False alerts | Stops detected |', '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for n in order:
        pr=models[n]['practical'];a=pr['diagnostic_2025'];v=a['checkpoint'];st=a['unique_stops']
        lines.append(f"| {NAMES[n]} | {a['threshold']:.2f} | {pct(v['precision'])} | {pct(v['recall'])} | {pct(v['f1'])} | {v['FP']:,} | {st['detected']}/{st['with_known_horizon_checkpoint']} |")
    best=models[s['recommended']]['practical']['diagnostic_2025'];v=best['checkpoint'];st=best['unique_stops']
    lines+=['',f"Recommended-model confusion: TP={v['TP']:,}, FP={v['FP']:,}, FN={v['FN']:,}, TN={v['TN']:,}. False checkpoint alerts per eligible driver-race: {best['false_alerts_per_driver_race']:.2f}. Repeated positive checkpoint alerts: {st['repeated_positive_alerts']:,}.", '',
        'These alerts concern the first up to three canonical regions, usually the current lap and next two. Short grids retain an open-ended final region. Several alerts can concern the same stop. Distinct-stop detection uses stops with known in-horizon evidence, which excludes stops without such evidence.', '',
        f"Positive prevalence in 2025 is {pct(v['prevalence'])}. Always alerting has that precision and 100% recall. Never alerting has zero recall and undefined precision. Unknown eligible outcomes: {v['unknown_binary']:,}. Excluded attempts: {v['excluded_attempts']:,}. Missing forecasts on known binary outcomes: {v['missing_forecast_known_binary']}.", '',
        '## Calibration and timing windows', '', '| Model | Short-horizon Brier | Median window regions | Event coverage | Predicted conditional mass |', '| --- | ---: | ---: | ---: | ---: |']
    for n in order:
        v=models[n]['practical']['validation'];w=v['conditional_window_coverage']
        lines.append(f"| {NAMES[n]} | {v['brier_p3']:.6f} | {v['window_width']['quantiles']['median']:.0f} | {pct(w['observed'])} | {pct(w['expected'])} |")
    lines+=['', '## Training, unknown outcomes and limitations', '',
        'Six chronological folds validate 2019, 2020, 2021, 2023, 2024 and 2025. H1-H3 train on every earlier admitted race. H4 uses the latest two admitted seasons. The absent 2022 season is not invented. No random lap split or future information enters training or inference.', '',
        'All 133 admitted pre-2026 races support the reused features. Forecast coverage is 122,816/122,816 eligible checkpoints. Of those, 29,166 have unknown outcomes and remain outside score calculations. There are 130,836 total attempts. Earlier-season unknown shares exceed 40%, limiting what the scored population represents. Detailed seasonal accounting remains saved.', '',
        'All validation results were already exposed to development. Repeated hypothesis testing can overfit these development races. Race-cluster intervals condition on the fitted procedures and omit training and selection variability. Archive assumptions RA1 through RA6 still apply. No new 2026 source or outcome was opened. Prior 2026 exposure and final-test locks remain unchanged.', '',
        f"The registered rule freezes {NAMES[s['recommended']]} and its thresholds before the final pre-2026 refit. The final model follows its declared training scope. This recommendation does not install it in the viewer or demonstrate dependable operational performance.", '',
        '## Evidence and recovery', '',
        'Commands and exact procedures: REGISTRATION.md and README.md. The four candidate archives preserve fitted validation models, forecasts, scores and practical metrics. New recovery records preserve the replacement final model, its actual-read ledger, reconstructed B0 metadata, current source snapshot and new completion hashes. The archival limits below apply to the missing original root records. Their retrieval receipt accompanies the presentation. Original #57 artifacts remain byte-identical. Independent review is recorded in REVIEW.md.', '']
    lines += ['','## Recovery and archival limits','','The workspace reset preserved all four candidate archives but lost the separate root opening ledger, completion manifests, original final selected model and interruption evidence. The new recovery reconstructs aggregate metadata under a new identity and repeats only the frozen H1 final fit with a checked 133-race actual-read ledger. Candidate models and validation scores remain unchanged. The prior independent result checks stand as recorded conclusions. Historical opening times, prediction-before-label ordering and interruption parity cannot be re-audited from the lost root evidence. See README.md and the private recovery/inventory.json.','']
    (ROOT/'REPORT.md').write_text('\n'.join(lines))

if __name__=='__main__':main()
