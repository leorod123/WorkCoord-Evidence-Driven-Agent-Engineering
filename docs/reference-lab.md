# Synthetic Reference Lab — Scope and Reproduction

This is a **fictional, deterministic teaching and invariant-testing reference**, not a real-agent benchmark or a production scheduler.

## Quick start

Python 3.10+ and its standard library are sufficient:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m workcoord_lab.demo
```

PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python -m workcoord_lab.demo
```

The intended demonstration prints before/after notification counts, a simulated semantic oracle decision, a generated synthetic work receipt, and an event-chain integrity check.

The D01–D15 probes are **reference tests for narrow example behavior**. Additional isolated negative controls check owner, generation and expiry on every post-claim transition. A mutation-check script must detect removed identity/expiry predicates. The CI matrix covers Python 3.10, 3.11 and 3.13.

## Limits

- Rejected work transitions **do not** advance the SQLite-persisted logical clock. An accepted transition records an auditable clock change **in the same transaction**. An optional `time_source` callable lets the embedding host supply time independently of the actor's tick. The default fallback is still a synthetic, **untrusted** caller tick; accepted hostile requests may still provide extreme values without a trusted clock authority. This is not production-safe distributed time or authenticated agents.
- The fake sandbox is an in-memory interface, **not an OS security boundary**.
- The hash-linked ledger detects accidental event history edits when verified and now records lease issuance, expiry and other decision-relevant metadata. It is still not a complete replay oracle, a signed record or an independently anchored tamper-proof audit log.
- A small synthetic oracle now recomputes results independently from a caller-supplied `passed` flag, using HMAC-tagged receipts. Directly asserted PASS is not enough for task closure. The published demonstration key is deliberately public; this is **not** production authentication. Real deployments would need independently controlled evaluator credentials, authorization and source provenance.
- The artifact digest and HMAC detect malformed or modified reference receipts without the key; they cannot establish that the source code really ran in an isolated environment.
- New tests cover multiple SQLite client processes, two interruption points, isolated fencing/expiry transitions and revision revalidation; they do not establish distributed linearizability, host-clock reliability, power-loss durability, hostile-client safety, or general crash recovery.
- Changing an unfinished unit's revision invalidates submitted evidence and reviewer approval while preserving its current claim. This revision change is a **synthetic administrative signal** without actor authentication; owners must still submit a valid new proof.
- `has_distinct_declared_groups` counts unverified labels supplied by callers, **not independently verified evidence**, and is not used to approve completion.
- `preliminary_decision_label` does not award final repair or abstention validity. The delivery simulator only deduplicates **inside one call**, not across restarts.
- This lab does not invoke language models, evaluate real agents, or provide evidence of speed/cost improvement.
- Python source and tests are new public examples, not adapted private project files.

Do not promote these reference fixtures to production trust boundaries or empirical comparison results.
