# Full Ledger Cycle v0 — Public Synthetic End-to-End Demonstration

**Status:** deterministic, authored fictional software-contract test. Not a real-agent benchmark, deployed orchestration service, authenticated reviewer, independently proved repair or production authorization.

## Purpose and scope

This study connects the existing components without creating a new coordinator:

1. **ContextNavigator:** explicitly visit Worker, Queue, API sectors; read a current synthetic source and its byte-bound body digest. Human-authored diagnostic annotations remain *hypotheses*, not proof.
2. **Research / Problem & Decision / Cognitive Perspectives / Knowledge Genealogy:** call the four existing original functions through the [vertical evidence](vertical-evidence-v0.md) reference; all must be locally admissible for a bounded advisory candidate.
3. **SQLite Ledger:** create a fictional unit under `REVIEW_REQUIRED`, acquire an exclusive generation-fenced lease, reject a second claimant and use an injected host-owned *synthetic* clock.
4. **Synthetic external-behavior evaluator:** recompute an actual PASS/FAIL from fictional logical events and observed deliveries. Submit a revision-bound artifact with a publicly disclosed HMAC demonstration key; the Ledger rejects a failed oracle result and evidence from another revision.
5. **Distinct declared reviewer and completion:** submit, verify, and explicitly approve the unit before issuing a local DONE receipt.
6. **Change of assumptions:** if the source revision changes, the Ledger clears prior evidence/approval while retaining the current generation. Old advisory checkpoints cannot be reused. A new source document, four-stage review, successful evaluator evidence **for the new revision**, verification and new approval are required.

Crucial authority distinction: **the Ledger DOES NOT enforce the advisory result**. The *study driver* calls the four advisory gates and refuses to call `Ledger.complete()` when a new contradiction makes them ineligible. A caller bypassing that driver could still satisfy the Ledger's own separately defined work invariants. No production access-control guarantee is claimed.

## Reproduced authored paths

| Scenario | Expected final state | What it demonstrates |
| --- | --- | --- |
| `baseline` | `DONE_SYNTHETIC` | Context/decision locally admissible; distinct declared reviewer and successful fictional behavior evidence; fenced Ledger completes |
| `late_counterevidence` | `HOLD_COUNTEREVIDENCE` | Previously green tests, declared approval and VERIFIED unit **cannot promote through the study driver** when a new contradictory genealogy observation appears; Ledger still reports VERIFIED, making enforcement separation visible |
| `revision_recheck` | `DONE_AFTER_EXPLICIT_REVALIDATION` | `r2 → r3` invalidates prior evidence and approval. A new authored context/decision/knowledge history and a fresh r3 proof/approval are required to reach DONE |
| `behavior_failure` | `HOLD_EXTERNAL_ORACLE` | Even locally favorable advisory reports cannot submit a failing external-behavior oracle result; the unit remains CLAIMED |

Tests also cover a missing fresh knowledge review, an unresolved cognitive counterexample on the new revision, a changed source body under an old digest, a forged/stale issue identity, repeated completion idempotency and a second actor failing to take an active lease.

**The revision recheck intentionally constructs a separate new packet**. It does not merely rewrite a version string or silently assume that the previously reviewed evidence still applies. Both old and new source lineage entries remain in the authored genealogy. A truncated history is evaluated at its latest available prefix, never padded with a future event.

## Limits that matter for independent evaluation

The same public fixture openly includes its sources, outcome labels, chosen revision and expected traces. It is **not held out**, and the complete synthetic source and evaluator key are available to the module. An HMAC over a public demonstration key is only an integrity-format exercise, not a cryptographic trust boundary.

The Ledger's `approve()` accepts an unauthenticated string different from the declared owner; this verifies *declared* separation, not independent human review or distinct identities. The `ContextNavigator.assess()` scores human-authored stances with arbitrary example weights. No external authenticated source, actual commit/build artifact, model reasoning, production permissions or measured benefit is present.

The `time_source` callable is a controlled fictional clock, not a secure distributed time oracle. The Ledger event chain is not independently anchored or proof of reviewer provenance. Every resulting report declares `production_authorization=NONE`, `real_agent_used=false`, `real_world_outcome_verified=false`, `external_reviewer_authenticated=false` and `ledger_enforces_advisory_state=false`.

The study is useful because it makes the integration boundary explicit, **not** because it proves a secure general-purpose agent operating system.

## Exact reproduction

Python 3.10+ and the standard library:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/verify_full_cycle_mutations.py
PYTHONPATH=src python -m workcoord_lab.full_ledger_cycle --output artifacts/full-ledger-cycle-v0.json
```

The public [development fixture](../examples/full-ledger-cycle-v0.json) reuses the existing [vertical base packet](../examples/vertical-integration-cases-v0.json) and contains compact, typed patches for the new r3 review rather than 4 copied author-authored stage packets.

The CI runs the tests in Python 3.10, 3.11 and 3.13 and retains mutation probes M1–M95; M96–M102 target this integration. SHA-256-bound JSON receipts are archived per Python version and must be checked against the **exact PR-head SHA** before the results are called verified.

## What comes next

Before any Codex or Harbor evaluation, review the full draft PR stack, decide a license and provenance policy, and define an independent evaluator with externally controlled source visibility and secrets. If a connected API is used later, keep credentials outside GitHub and do not publish raw provider traffic or private material.

A realistic benchmark must compare valid external outcomes, time, total tokens/costs and avoidable holds against a single-agent and a simpler two-agent baseline. The synthetic demonstration makes no such efficacy claim.
