# Expanded pre-2026 raw-source admission

Status: approved. Independent bounded admission/protocol review PASS on
e65374c83f8b674ad10224e51336dd9455c3ad58 (PR #56). The fixed manifest admits
133 sessions and excludes 40. See research/expanded-pre2026/ADMISSION_REVIEW.md.
Issue #53. Owner approval: decisions/2026-10-14-expanded-pre2026-admission-pending.md.

## Evidence boundary

The audit covers all 173 2018–2025 calendar sessions. It reuses the frozen six
endpoint snapshots for 39 S-RD development sessions and acquires all other raw
sessions, including races absent from the 104 historical per-race CSV exports.
Acquisition uses 20-second request timeouts, at most three attempts, and records
terminal 403/404 failures without repeating them. Partial caches retain hashes.
No 2026 source or outcome is requested. The calendar evidence is metadata only.

Every session receives an acquisition and verification record, with complete
source hashes, raw schema/prefix integrity, roster/distance/counter checks,
clock-health exclusions and tyre/penalty diagnostics. Exclusions remain in the
fixed inventory. No CSV value enters observation or target reconstruction.

## Explicit assumptions

S-RD retains RA-1–RA-4 and its existing bounds. Older raw scopes retain RA-1–RA-3,
replace race-day fidelity with RA-5 (rewritten snapshot preserves historical
versions/order), and add RA-6 (the shared ±5s availability bound applies only in
per-session validated healthy windows). Internal consistency cannot prove RA-5
or establish independent tyre-change ground truth. The owner accepted this
weaker evidence standard. These assumptions must follow every older artifact
and every model trained on the mixed corpus.

The same conservative source boundary applies: ±5s bounds, strict 10s cross-stream
separation, pre-start 300s margin, same-stream order and no future corrections.
Older sessions additionally omit EVERY anomalous lap span (absolute residual >1s),
including single-driver anomalies, and ±60s around every out-of-band RCM anchor.
Sparse intervals use the existing no-check/anchor rule. Lap jumps/regressions,
missing roster, unknown drivers or absent initial scheduled distance exclude a
session. The existing unsupported Bahrain/Hungary 2018 verdicts remain excluded.

## Target capability

The positive rule remains the final stint update within a visit carrying
TyresNotChanged=0. Internal New/StartLaps corroboration is reported. A served
penalty test that classifies positive excludes the session. Negative and missing
service evidence remain indeterminate in reconstruction, never guessed no-service.
Raw entry/exit context and same lap counter own event identity. Terminal bounds
and restart handling follow the approved target design. No stop duration or
same-row CSV PitStatus is substituted for tyre service.

## Technical selection amendment

B1 remains unchanged and explicitly failed when unsupported. TYRE_RIDGE is a
new registered candidate with a fixed ridge penalty and pooled empirical final
no-event boundary. The expanded full-cohort selector uses B0 as reference when
B1 is unsupported. This is a delegated evaluation implementation choice under
the user's requested protocol update, retaining log score and target meaning.
It requires independent review before validation scoring and does not silently
change the old P-F1/P-F2 experiment or its frozen claims.
