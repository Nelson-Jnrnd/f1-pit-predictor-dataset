# Four pit-prediction hypotheses

The lowest probability penalty is 2.161464 from H1: Percentage inputs. The registered uncertainty rule recommends H1: Percentage inputs. These are exploratory development findings.

Among exploratory 2025 alerts with known outcomes, 2,478 of 3,429 alerts are false. Precision is 27.7% and recall is 46.4%. False alerts and missed stops remain material. These results do not establish dependable operational use.

## Scores

| Hypothesis | Mean log score | Improvement over current forest | 95% race-cluster interval |
| --- | ---: | ---: | --- |
| Current forest | 2.169202 | Reference | |
| H1: Percentage inputs | 2.161464 | 0.007738 | -0.002720 to 0.018196 |
| H2: Detailed forest | 2.293525 | -0.124323 | -0.182627 to -0.066018 |
| H3: Gradient boosting | 2.257591 | -0.088388 | -0.147918 to -0.028859 |
| H4: Recent seasons | 2.229888 | -0.060686 | -0.093420 to -0.027952 |

H1: Percentage inputs: A small timing-score gain remains uncertain across races. More stops are detected, but precision falls and false alerts rise.


H2: Detailed forest: Timing scores worsen clearly. Alert recall rises slightly, with more false alerts. Depth and leaf size change together.


H3: Gradient boosting: This fixed boosting setup scores worse for full timing. Its 2025 F1 improves slightly. The two objectives give different rankings.


H4: Recent seasons: Recent seasons score worse. The test also changes the amount and completeness of training data, plus the estimate of no further stop.


Lower log score is better. It measures the penalty assigned to the observed stop timing or no-stop outcome. It is not percentage accuracy. Positive improvement favours the new procedure. Every model has the same 93,650 scored checkpoints across 115 validation races.

## Hypotheses and decisions

H1 replaces the raw lap grid with percentage features and scales tyre age by scheduled distance. It retains inverse scheduled distance, so this tests a different representation rather than removing race-length information.

H2 increases maximum tree depth from 12 to 20 and reduces minimum leaf size from 100 to 30. It tests both settings jointly.

H3 uses 150 fixed gradient-boosting iterations on the same inputs. It tests a different way of fitting trees. No validation-driven early stopping or hyperparameter search occurs.

H4 trains on the two most recent admitted earlier seasons and recomputes the terminal probability on that subset. It tests a training-history procedure, not the effect of age alone.

## Exploratory 2025 alerts

| Model | Threshold from earlier seasons | Precision | Recall | F1 | False alerts | Stops detected |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Current forest | 0.24 | 28.4% | 44.3% | 34.6% | 2,293 | 353/697 |
| H1: Percentage inputs | 0.23 | 27.7% | 46.4% | 34.7% | 2,478 | 365/697 |
| H2: Detailed forest | 0.29 | 28.3% | 47.1% | 35.4% | 2,442 | 382/697 |
| H3: Gradient boosting | 0.24 | 28.9% | 46.9% | 35.8% | 2,360 | 367/697 |
| H4: Recent seasons | 0.27 | 29.2% | 37.5% | 32.8% | 1,864 | 302/697 |

Recommended-model confusion: TP=951, FP=2,478, FN=1,097, TN=20,148. False checkpoint alerts per eligible driver-race: 5.17. Repeated positive checkpoint alerts: 586.

These alerts concern the first up to three canonical regions, usually the current lap and next two. Short grids retain an open-ended final region. Several alerts can concern the same stop. Distinct-stop detection uses stops with known in-horizon evidence, which excludes stops without such evidence.

Positive prevalence in 2025 is 8.3%. Always alerting has that precision and 100% recall. Never alerting has zero recall and undefined precision. Unknown eligible outcomes: 1,921. Excluded attempts: 541. Missing forecasts on known binary outcomes: 0.

## Calibration and timing windows

| Model | Short-horizon Brier | Median window regions | Event coverage | Predicted conditional mass |
| --- | ---: | ---: | ---: | ---: |
| Current forest | 0.083067 | 12 | 76.6% | 81.8% |
| H1: Percentage inputs | 0.082820 | 13 | 77.6% | 81.7% |
| H2: Detailed forest | 0.088160 | 11 | 70.6% | 82.1% |
| H3: Gradient boosting | 0.088557 | 11 | 72.5% | 82.2% |
| H4: Recent seasons | 0.084909 | 12 | 75.7% | 81.8% |

## Training, unknown outcomes and limitations

Six chronological folds validate 2019, 2020, 2021, 2023, 2024 and 2025. H1-H3 train on every earlier admitted race. H4 uses the latest two admitted seasons. The absent 2022 season is not invented. No random lap split or future information enters training or inference.

All 133 admitted pre-2026 races support the reused features. Forecast coverage is 122,816/122,816 eligible checkpoints. Of those, 29,166 have unknown outcomes and remain outside score calculations. There are 130,836 total attempts. Earlier-season unknown shares exceed 40%, limiting what the scored population represents. Detailed seasonal accounting remains saved.

All validation results were already exposed to development. Repeated hypothesis testing can overfit these development races. Race-cluster intervals condition on the fitted procedures and omit training and selection variability. Archive assumptions RA1 through RA6 still apply. No new 2026 source or outcome was opened. Prior 2026 exposure and final-test locks remain unchanged.

The registered rule freezes H1: Percentage inputs and its thresholds before the final pre-2026 refit. The final model follows its declared training scope. This recommendation does not install it in the viewer or demonstrate dependable operational performance.

## Evidence and recovery

Commands and exact procedures: REGISTRATION.md and README.md. The four candidate archives preserve fitted validation models, forecasts, scores and practical metrics. New recovery records preserve the replacement final model, its actual-read ledger, reconstructed B0 metadata, current source snapshot and new completion hashes. The archival limits below apply to the missing original root records. Their retrieval receipt accompanies the presentation. Original #57 artifacts remain byte-identical. Independent review is recorded in REVIEW.md.


## Recovery and archival limits

The workspace reset preserved all four candidate archives but lost the separate root opening ledger, completion manifests, original final selected model and interruption evidence. The new recovery reconstructs aggregate metadata under a new identity and repeats only the frozen H1 final fit with a checked 133-race actual-read ledger. Candidate models and validation scores remain unchanged. The prior independent result checks stand as recorded conclusions. Historical opening times, prediction-before-label ordering and interruption parity cannot be re-audited from the lost root evidence. See README.md and the private recovery/inventory.json.
