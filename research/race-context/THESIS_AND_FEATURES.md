# What this experiment builds on

Both historical training notebooks inspected at pinned commits train a Random
Forest, including on the branch named training_svm. They use 2,000 trees, depth 5,
entropy and balanced_subsample weighting. They import unavailable f1pitpred
preprocessing; exact equivalence is not claimed.

The later cleaning branch exposes the preprocessing. Its params select 100 trees,
depth 10 and balanced weighting. It shifts PitStatus to the next grouped row,
encodes compound/circuit on training data, randomly splits driver-race groups,
and removes whole groups based on eventual wet tyres, completion and stop count.
Those filters and random splits are not inherited. Historical binary metrics do
not measure the same target, population or split as this timing experiment.

Evidence inspected directly:
- [RF notebook](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/blob/7426255ba9a8185b93fd097a86c49d43aaac5b0c/model_training.ipynb)
- [SVM-branch notebook](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/blob/981a76b831ad67c8e6a303d93dd7fab71c36dd9a/model_training.ipynb)
- [Visible preprocessing](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/tree/fe5abd65acd335c05a472db1e5a45bdbe8cac5b9/f1_pit_predictor/preprocessing)
- [Visible parameters](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/blob/fe5abd65acd335c05a472db1e5a45bdbe8cac5b9/f1_pit_predictor/params.yaml)

| Thesis family | New source and availability | Transformation / missing policy | Decision |
| --- | --- | --- | --- |
| Lap, TotalLaps | Own canonical grid at checkpoint | L, scheduled N, fractions; never eventual distance | Retain |
| Compound, TyreLife | Existing admissible TimingAppData view | Fixed six indicators, age+h; -1 plus missing flag | Retain |
| Stint | Canonical stint indices lack independently verified service identity | None | Omit for this bounded experiment |
| Circuit/Track | No authorized circuit fact in saved canonical state | No race-ID proxy | Omit; add proper canonical metadata in later experiment |
| LapTime | Canonical TimingData LastLapTime | Only explicitly associated completed checkpoint lap; -1 plus missing flag | Retain completed pace only |
| Pace changes | Canonical LastLapTime and BestLapTime.Lap<=L | Last minus best; no later-lap lookup; missing if either absent | New causal pace contrast, not rolling trend |
| Position/gaps/ahead | Canonical TimingData Position, GapToLeader, IntervalToPositionAhead | Numeric rank/gaps with bounds; lapped strings missing, no fabricated zero | Retain timing rank/traffic, not track coordinates |
| TrackStatus flags | Not reconstructed in saved observation state | None | Omit unsupported domain |
| Weather | Collected historically; visible features.py removes weather | None | Omit unsupported stream; do not claim thesis used it |
| PitStatus, shifted status, eventual stop count | Retrospective target-related fields | Never feature inputs | Exclude |
| Future NextCompound, completion, future wet running | Future information | Never input or population filter | Exclude |

The new forest fits a hazard for each possible future lap region, using context
frozen at the prediction checkpoint. Only projected progress and tyre age advance.
Training-negative sampling is corrected by inverse inclusion weights; balanced
class weighting would alter event prevalence and is deliberately avoided here.
Fixed tree settings and chronological seasons replace the older random evaluation.
RF_GRID/RF_TYRE/RF_CONTEXT isolate added information with the same model settings.

These are new models inspired by the thesis. B1-R0 (historically B-thesis) is only
B1's first-region probability and has never been the thesis Random Forest.
