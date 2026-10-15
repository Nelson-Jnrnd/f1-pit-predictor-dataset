# Exploratory loop log

The four procedures were fixed before scores under REGISTRATION.md. Only the
interpretation and reporting narrative adapt. No parameters or features are
changed after seeing an outcome. All results remain development evidence.

## H1: percentage representation

Six completed fold scores give mean log score 2.161464 over 93,650 matched
checkpoints, compared with 2.169202 for RF_CONTEXT. This is a small point-estimate
improvement. Full uncertainty and alert diagnostics remain part of the saved
summary. Representation alone does not explain the current model's weaknesses.

Next: H2 tests whether deeper trees and smaller leaves preserve useful patterns.
Its settings remain the previously registered depth 20 / leaf 30. It starts from
RF_CONTEXT, not from H1. H1's code, models and forecasts remain unchanged.

## H2: deeper forest and smaller leaves

The six-fold mean log score is 2.293525 over the same 93,650 checkpoints. This
is worse than RF_CONTEXT's 2.169202. The registered joint change does not improve
transfer to later races. It does not isolate which of the two settings caused
the degradation, and training performance was not used to establish overfitting.

Next: H3 tests fixed gradient boosting on the original RF_CONTEXT inputs. The
registered 150 iterations, 15-leaf trees and regularization remain unchanged.
This tests another estimation procedure, not another arbitrary increase in forest
capacity. No H1/H2 feature or setting is inherited.

## H3: gradient boosting

The six-fold mean log score is 2.257591 on the same scored checkpoints. This
also fails to beat RF_CONTEXT on complete timing probabilities. This fixed
boosting configuration does not improve the reference with the current inputs.
No iteration count, regularization or other parameter is retuned.

Next: H4 keeps the original forest and inputs but limits training to the latest
two admitted earlier seasons. This tests whether the training-history procedure
transfers better. Recency, training volume and archive completeness vary together;
it cannot establish an isolated causal effect of older seasons.
