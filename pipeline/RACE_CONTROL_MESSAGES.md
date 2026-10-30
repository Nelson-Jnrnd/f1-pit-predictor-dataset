# Race-control message replay

`pipeline.race_control_messages.replay` reconstructs the last reported race-control information at a prediction time. It handles safety-car and virtual-safety-car announcements, ending messages, track clearance, red flags, restart instructions, corrections and session resets.

```python
from pipeline.race_control_messages import replay

status = replay(boundary, messages, session_status, clock, causes)
```

This is a pure function. It does not download data, train a model or change H1's input features. The caller supplies ordered archived records and the existing clock evidence. It must not pass retrospective corrections as earlier availability evidence.

## Inputs

- `boundary`: prediction record with `prefix` (seconds), `ordinal` and `stream`.
- `messages` and `session_status`: ordered records with `prefix`, `ordinal`, `stream`, `ref` and `payload`. Message payloads contain `Messages`; session payloads contain `Status`. References identify the exact source records.
- `clock`: admitted race bounds, `start` and `end`, in prefix seconds.
- `causes`: existing clock exclusions, each with `start`, `end` and `cause`. An empty list asserts healthy timing; it must not be used to hide unavailable clock evidence.

Same-stream records use prefix and ordinal order. Other streams require a strict ten-second separation. The caller owns the input clock authority and the assumption that source order preserves delivery order; this module cannot prove either from an archive.

## Output and limits

`state` names the last reported information. `projected` is a conservative SC/VSC announcement projection, not a complete physical flag state. A restart instruction remains distinct from confirmed normal racing or active safety car. `certificate` separates the content record from the record establishing its availability. `reason`, `released` and source references explain how the answer was obtained. `delivery_completeness_proven` remains false.

A failed lap-based clock check does not automatically erase a valid message. Message-specific checks use earlier trusted calibration. A previously rejected message can be used only after a later trusted record establishes its availability in the ordered feed. It never repairs an earlier prediction. Status and pending messages reset at session transitions; clock calibration has its separate lifetime. Corrections, deletions, gaps in message identities and malformed packets prevent unsupported claims. Fixed timing cutoffs are preserved.

The private verification for issue #67 is complete. The owner authorized integrating this implementation on 30 October 2026. This merge adds the reusable handler and its constructed regression tests; it does not replace canonical observation timing, admit new H1 features, rerun completed experiments or access protected 2026 data. Issue #65 owns the later prediction comparison and #62 owns the required input-admission review.

Run the regression checks from the repository root:

```sh
python -m unittest pipeline.tests.test_race_control_messages -v
```
