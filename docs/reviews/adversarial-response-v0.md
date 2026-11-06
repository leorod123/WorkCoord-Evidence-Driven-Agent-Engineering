# Adversarial Review Response — Reference Lab v0.3

**Date:** 2026-11-06  
**Review baseline:** draft PR #1 at `e9b4179138a75449c31e7881496a7abde61d7ac8`  
**This response:** subsequent synthetic branch changes, not a human approval, production certification or real-agent study.

The adversarial review found that the previous 32/32 green tests did not detect removing the owner/generation or expiry predicates in `_fenced`. This was a weakness in the *negative controls*, not evidence that those predicates were absent from the original code.

| Finding | Result after review | Evidence / remaining limit |
| --- | --- | --- |
| R01 — mutation-insensitive fencing tests | **Addressed for specified mutations** | Isolated tests at SUBMIT, VERIFY and COMPLETE; CI mutant M1/M2 each fails an expected negative control |
| R02 — revision invalidation dead end | **Addressed for synthetic state machine** | Source change clears stale evidence and review, preserves still-valid claim, permits same-holder resubmission |
| R03 — backwards logical time | **Addressed within reference clock** | SQLite-local nondecreasing tick, including failed transition attempts; no trusted cross-host clock |
| R04 — sectorized context is only a keyword filter | **OPEN / next research milestone** | Scope and revision-aware context navigation not yet implemented; do not claim it exists |
| R05 — declared groups called independent | **Terminology corrected** | `has_distinct_declared_groups` counts labels only; cannot prove true independence or support closure |
| R06 — event history under-specified | **Partially addressed** | Lease issue/expiry, authority, revision, evidence digest and decision times recorded; no full replay or external anchoring |
| R07 — outcome confounded with gate blocking | **Protocol revised, not run** | A/B/C share held-out external acceptance; invalid attempt and gate rejection separately recorded |
| R08 — contribution cannot be identified from A/B/C | **Claim restricted** | Initial comparison evaluates *package*, RQ4 deferred until controlled ablations |
| R09 — HOLD auto-graded valid | **Toy labeler corrected** | HOLD must undergo external abstention review; repair goes to independent acceptance |
| R10 — deduplication only inside one call | **Limitation retained, explicit** | Stateful delivery across retries/restarts remains future work |

## What was checked

At the subsequent candidate `bac856ba36de93e56c63e0c7b5a19dc3cccabb76`, GitHub Actions run `42153241306` completed green on Python 3.10, 3.11 and 3.13. Each matrix job executed **43 unittest cases**, the synthetic demo, and both mutation-kill checks. These are local synthetic properties, not an LLM productivity experiment.

## Boundaries still requiring independent review

1. This response does not reperform the original adversarial review as an independent human reviewer.
2. Public HMAC keys, caller-supplied source identity and tick inputs, untrusted reviewer strings and lack of OS isolation remain explicitly outside a secure production claim.
3. No comprehensive audit of Git history, third-party rights, CI artifacts and semantic confidentiality has yet been signed off.
4. Licensing remains a repository-owner decision.
5. No agent benchmarks or claims of effectiveness have been executed.

**PR stays draft. Main is not merged by this response.** The next research step should demonstrate sector/perspective/depth navigation and preserve counterevidence, then evaluate under a common independent oracle.
