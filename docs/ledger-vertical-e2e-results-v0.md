# Ledger End-to-End v0 — Executed Synthetic Development Results

**Status:** public, self-scored and deliberately fictional software-control probe. **Not** an independent task benchmark, an actual repaired application, trusted evaluator evidence, authenticated reviewer identity, or a real-agent efficiency result.

## Validated implementation candidate

- Source commit under test: `ca1945c4d9526bddc49310e72ad2118078366eba`.
- [GitHub Actions run 42177449958](https://github.com/leorod123/WorkCoord-Evidence-Driven-Agent-Engineering/actions/runs/42177449958): **PASS** on Python **3.10, 3.11 and 3.13**.
- Per Python version: **322/322 deterministic tests passed**, including **20 new targeted E2E tests**.
- **106/106 deliberate mutant regressions M1–M106** were caught by named negative assertions, including the new **11/11 M96–M106** that try to ignore the source hash, context retrieval, late contradiction, Ledger revision, semantic oracle, verification/complete rechecks, reading budget, work identity, reviewer gate and report redaction.
- **24 JSON artifacts** archived: eight existing synthetic development receipt families across 3 Python versions, including three new `ledger-vertical-e2e-py-3.10`, `-3.11`, `-3.13` artifacts. Each new archive contains the redacted `ledger-vertical-e2e-v0.json`.

The first candidate run found a real field-adaptation error: the ContextNavigator returns `source_revision`, not `revision`. Because the bridge failed closed, a correctly selected document was initially blocked. The code was corrected and the exact candidate above rerun successfully. A successful previous commit is not substituted for this tested code version.

## The replay and controls

One fixture [documents](../examples/ledger-vertical-fixture-v0.json) both `fictional-r2` and `fictional-r3`. This is **one task with two revisions**, not 20 independent experimental tasks.

| Stage / attempted regression | Observed deterministic behavior |
| --- | --- |
| Initial source r2, history cut 4 | The primary observation is actually retrieved within the reading budget; Research/Problem/Cognitive/Genealogy return an advisory candidate |
| Same issue, later contradictory source at cut 6 | The advisory gate returns `HOLD_KNOWLEDGE`; a new synthetic proof cannot be submitted under that current snapshot |
| Wrong-owner submit with a large caller tick | The Ledger rejects it without moving the accepted logical clock or adding an event |
| Two duplicate deliveries for one logical event | The toy semantic oracle returns FAIL; it cannot create a passing attestation/submission |
| Passing r2 behavioral observation | The existing synthetic evaluator produces a revision-bound receipt; Ledger reaches VERIFIED and accepts a *declared* distinct reviewer label |
| Source changed to r3 before completion | The previous proof/approval are cleared and status becomes CLAIMED while preserving the lease generation |
| Previous r2 proof after the source change | Rejected by the Ledger's revision-bound evidence control |
| Original four-stage packet with the new genealogy | `HOLD_REASSESS_REVISION`; a genealogy review alone cannot make older Research/Problem/Cognitive inputs current |
| New source r3 at cut 7, before a new explicit review | HOLD; new evidence is not silent acceptance |
| New source r3 at cut 8, after explicit review | New selected context source and all four authored stage inputs align again; local advisory admission may resume |
| Renewed r3 behavioral proof | A fresh synthetic oracle result can be submitted and verified against the new revision |
| Completion without new review, or owner self-review | Rejected; the reviewer identifier is still **only a string**, not a verified human |
| Renewed declared review and completion | Ledger locally reaches `DONE`; repeat completion returns the same SHA-256 receipt without new events |

The module also reports the local event-chain integrity check and a sanitized event-type sequence. Its HMAC key is generated in memory through `secrets.token_bytes(32)`, never committed, never passed to an agent and never published. **Raw MAC-dependent event heads vary by run and are intentionally omitted** from the deterministic public receipt.

## Scientific boundary and next hurdle

The toy semantic oracle checks only one-delivery-per-distinct-event over fictional strings. WorkCoord has not repaired a third-party repository, authenticated its source data, verified identity, or measured a single real-agent token, cost or latency. `DONE` in the Ledger is a **local work-state transition**, not authenticated problem acceptance.

This bridge is a bounded **cooperative wrapper**. The Ledger itself does **not** enforce that every external caller has passed these upstream gates; source snapshots and historical cuts are still supplied by the caller. A production integration would need trusted source revisions, independent reviewer identity, a secured API boundary, effective server-side admission and externally anchored receipts.

Before using an actual Codex API or agent, finish human confidentiality/IP/license review, retain draft PRs until approved, then choose small, locked-down Harbor/Terminal-Bench tasks with an independent grader and comparable agent/tool budgets. No model secret belongs in this public repo or report.

See the [reproducible method](ledger-vertical-e2e-v0.md), [original Ledger trust limits](reference-lab.md), and [experiment design](experimental-design.md).
