# Development replay implementation plan

Task: one development-race Replay Explorer integration, from main `684be43`.

Prespecified preview: Austria 2024 R11; fixed B0 climatology fitted only on Spain
2024 R10, whose race concluded before Austria. These are P-F1 development races.
No selection, tuning, scoring, final reads or deployment. This is a B0-only
engineering preview, not a P-F1 fold evaluation (its minimum is 15 training races).
B1 is not implemented. `selection_evidence_refs` is empty.

Implement the canonical boundaries in sequence: frozen source/authority manifest;
observation and per-attempt records; causal initialization; separate retrospective
resolution; ledger-first development join; frozen B0; replay snapshots and failures;
separate retrospective mapping; validated development-only export.

Use only the six endpoints admitted by SUPPORT_MATRIX S-RD. Position/CarData remain
unverified and must not be read as causal state. Real positions require a separately
reviewed endpoint authority and matching coordinate geometry; export null positions
and neutral sector/minis overlays until that dependency is satisfied. The circuit outline is identity imagery only, not verified position geometry.

Maintain the approved UI and shared race clock. Run canonical boundary/export tests,
frontend tests/build, real browser checks where possible, and the bounded independent
review. Any source gap, unsupported target or insufficient baseline fit fails closed.

Source preflight corrected the initial calendar mapping: Canada is R9 and its
TimingData was rewritten on 20 June. It is excluded; no observations or training
artifacts are made from it. Spain is R10. The implementation uses Spain → Austria.
