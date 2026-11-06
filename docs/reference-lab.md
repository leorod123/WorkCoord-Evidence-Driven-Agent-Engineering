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

The 15 D01–D15 probes are **reference tests for narrow example behavior**; the two additional tests inspect explicit review and dependency gates.

## Limits

- Caller-controlled logical ticks are not a safe production lease clock.
- The fake sandbox is an in-memory interface, **not an OS security boundary**.
- The hash-linked ledger detects accidental event history edits when verified. It is not a signed, independently anchored tamper-proof audit log.
- A small synthetic oracle now recomputes results independently from a caller-supplied `passed` flag, using HMAC-tagged receipts. Directly asserted PASS is not enough for task closure. The published demonstration key is deliberately public; this is **not** production authentication. Real deployments would need independently controlled evaluator credentials, authorization and source provenance.
- The artifact digest and HMAC detect malformed or modified reference receipts without the key; they cannot establish that the source code really ran in an isolated environment.
- New tests cover multiple SQLite client processes and two interruption points; they do not establish distributed linearizability, host-clock reliability, power-loss durability, hostile-client safety, or general crash recovery.
- This lab does not invoke language models, evaluate real agents, or provide evidence of speed/cost improvement.
- Python source and tests are new public examples, not adapted private project files.

Do not promote these reference fixtures to production trust boundaries or empirical comparison results.
