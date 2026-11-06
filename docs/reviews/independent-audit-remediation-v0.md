# Independent Adversarial Audit — Contract Remediation v0

> Public synthetic reference, not a production certification or a real-agent performance result. This report responds to the external static audit of the public draft PR stack on November 6, 2026.

## Scope and methodology

The audit correctly distinguished published `main` (design-only) from the executable **draft** PR stack. This follow-up changes only the reference implementation and associated regression probes. It does **not** invoke external agents, copy private source systems, access model credentials, or alter `main`.

| Finding | Remediation and directed probe | Residual boundary |
| --- | --- | --- |
| **A01 — untrusted lease tick** | Clock advancement now occurs **after accepted state transitions**, atomically with the SQLite update and a hash-chained `clock_advance` event. Rejected owners cannot poison other leases. Optional `time_source` overrides the actor's supplied tick. Test: `test_rejected_actor_cannot_advance_lease_clock`. | Default is still a synthetic actor-provided clock. A malicious *accepted* actor could submit an enormous tick absent a trusted host clock; identity is not authenticated. |
| **A02 — future history in prior receipt** | A historical genealogy checkpoint is derived from the requested event **prefix only**. `verify_chain(records)` remains a separate full-chain operation. Test: `test_historical_checkpoint_stable_after_future_append`, including an unchanged vertical checkpoint. | No trusted signature, immutable external head anchor, independent timestamp or replay-time source verification. |
| **A03 — unread-source answer-key leak** | The selector now reveals only excluded IDs and budget reason, not a hidden `contradicts` signal. Test: `test_unread_source_stance_not_exposed` changes an unread source's annotation and verifies identical agent-visible output. | Metadata and source IDs remain visible; offline evaluator may still inspect withheld gold annotations. |
| **A04 — unreferenced historical background** | An evidence record can declare `role=background` (default `basis`). Old or unavailable background produces **warnings**, not a scientific HOLD; using it as a hypothesis basis triggers a blocking issue. Test: `test_uncited_historical_background_does_not_force_hold`. | Roles and times remain caller-provided; background labeling cannot certify honest use or actual independence. |
| **A05 — concealed unresolved counterevidence** | A SUPPORT lens with cited unresolved counterevidence returns `HOLD_UNRESOLVED_COUNTEREVIDENCE`. A declared RESOLVED entry requires typed justification and a distinct cited supporting source; open records remain visible. Test: `test_unresolved_counterevidence_blocks_advisory_ready`. | A claimed resolution is still not externally authenticated or proven scientifically correct. |
| **A08 — unsafe shared SQLite reads** | `get`, event counts, chain checks and declared-group reads now acquire the same per-instance `RLock` as writes. Dedicated concurrent-read control checks against uncommitted values. | Multiple hosts and shared database files still require an operational concurrency/threat model. |
| **A09 — CI supply chain** | GitHub Actions commit-SHA pinned to official repository tag targets; `contents: read`, disabled persisted checkout credentials, and a job timeout. | Runner and operating-system images are not pinned; external supply chain is not fully reproducible. |

## Directed controls and legacy compatibility

The test suite retains all earlier narrow negative controls **M1–M88**. New isolated mutations **M89–M95** attempt to reintroduce the poisoned clock, ignore a host time source, leak a future chain head into a historical checkpoint, disclose unread diagnostic labels, block uncited historical background, count an unresolved counterexample as advisory consensus, or allow a shared-connection dirty read.

Earlier tests that explicitly expected bad behavior have been updated rather than grandfathered in. In particular, a rejected expiry tick **must not** prevent a valid owner from submitting at a still-valid prior tick. Existing synthetic case catalogs are unchanged; new negative cases are separate.

Each audit mutation runs the **single named negative-control unittest** in a temporary package copy. An import error, unexpected exception or timeout never counts as a mutation kill.

Reproduce with Python 3.10+ from repository root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/verify_audit_mutations.py
```

## Publication and agent API constraints

The project has no selected open-source software license or complete human provenance audit. The stacked PRs should remain **draft** and `main` untouched. Public CI artifacts and future benchmark data must not include API keys, provider tokens, personal/private source paths or raw confidential conversations.

The Codex API or any agent connector is **not needed for deterministic remediation tests**. If a later Harbor or Terminal-Bench pilot uses a connected model, the key must stay in the connector/secret-management boundary. Publish only sanitized task IDs, code versions, environment descriptions, bounded trajectories and independently scored outcomes; inspect them for leakage before committing.

### Remaining known high-priority work

**A06:** no demonstrated complete bridge from investigation/context/semantic evidence to Ledger claim, attested artifact, revision-aware approval and work completion. This is the next separate synthetic integration study, not a reason to create another coordinator.

**A07:** no cryptographically authenticated reviewer identity or source-of-truth validation. Public HMAC examples are deliberately non-secret test fixtures.

**A10:** license, copyright, historical confidentiality and provenance review require an explicit owner decision. No automated text-marker scan can certify those rights.

**Experimental benchmark:** once contract fixes and a full Ledger path are reviewed, use a recognized external environment such as Harbor + Terminal-Bench (or coding benchmarks with independent graders) for a small controlled pilot. No real-agent superiority or cost advantage has yet been demonstrated.
