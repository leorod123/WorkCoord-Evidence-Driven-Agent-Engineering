# Knowledge & Learning v0 — Executed Synthetic Development Results

**Status:** deterministic public *development fixture*. **Not** a held-out agent benchmark, independently authenticated source history, proof of scientific truth, or demonstration of model learning.

## Exact executed candidate

- **Validated head before this documentation addition:** `f0c8c469d6932a2633f6e7ea5d27d2e1d4d9b0ac`.
- [GitHub Actions run 42165653914](https://github.com/leorod123/WorkCoord-Evidence-Driven-Agent-Engineering/actions/runs/42165653914): **PASS** on Python **3.10, 3.11, 3.13**.
- On **each** Python version: **249/249 deterministic tests PASS**; **70/70 deliberate mutations M1–M70** produced their designated failing negative-control assertions; **19/19 published case expectations** matched.
- Three archived SHA-256-bound result artifacts: `knowledge-genealogy-py-3.10`, `-3.11`, `-3.13`.
- The first CI candidate exposed a mutation-harness issue: mutators ran the entire new test module, allowing unrelated exceptions. The harness was corrected to invoke **only each designated negative-control test**, rejecting exceptions and timeouts. The verified run above is on the revised source.

## Synthetic checkpoint classification

The **19 fictional cases produce 23 final claim endpoints**, because four scenarios contain two claims. Therefore the following counts are **not 23 separate empirical tasks**.

| Final advisory claim status | Number of fictional claim endpoints |
| --- | ---: |
| `ADVISORY_CURRENT` | 9 |
| `HOLD_STALE_BASIS` | 6 |
| `HOLD_COUNTEREVIDENCE` | 2 |
| `HOLD_REVIEW_REQUIRED` | 2 |
| `HOLD_UPSTREAM` | 1 |
| `HOLD_UPSTREAM_REVIEW_CHANGED` | 1 |
| `HOLD_RETRACTED_BASIS` | 1 |
| `HOLD_UNREVIEWED` | 1 |
| **Total claim endpoints** | **23** |

These figures are descriptive properties of a deliberately constructed JSON catalog and are not sampling estimates.

## What the negative examples demonstrate

**KG02 — source revision makes a once-current conclusion stale.** At historical cut 4, the fictional claim is `ADVISORY_CURRENT`. Once `worker-r1` is explicitly superseded by `worker-r2`, the exact same claim becomes `HOLD_STALE_BASIS`. The earlier event chain, review and source ID remain reconstructible.

**KG03 — new evidence alone cannot silently restore acceptance.** The replacement observation is recorded first; only a new `REVIEW_ACCEPT` changes the status back to *advisory current*. Both source revisions remain in history. In **KG15**, the new source body is **byte-identical** to the old one but has a different revision identity; silent acceptance is still rejected.

**KG04–KG06 — recorded negative evidence cannot disappear by vote.** An active contradictory observation changes status to `HOLD_COUNTEREVIDENCE`. An explicit retraction records a reason and leaves `HOLD_REVIEW_REQUIRED`; a further review may restore advisory status. Historical output retains the retracted contradictory observation.

**KG07–KG09 — invalidate dependents, then re-review both sides.** A downstream conclusion is blocked when its reviewed upstream source changes. Restoring the upstream review does not automatically restore the downstream; the latter still binds the old upstream review identity until it receives an explicit new review.

**KG12–KG13 and KG17 — unrelated revisions must not indiscriminately block work.** Registering a staged successor does not invalidate the current accepted source before supersession. Changes to unrelated source lineages do not invalidate unrelated claims. This is an essential negative control against excessive process.

**History integrity:** tests detect altered event content, out-of-order events, missing middle records, duplicate IDs and forged future availability. However, a malicious writer can reseal a complete log, and a truncated suffix remains undetectable without an **externally pinned head hash**. This limitation is explicit rather than hidden.

## Exact scientific boundary

The reference is a **replay and provenance-consistency demonstration**. It does not verify where a source came from, whether its observations are true, whether an apparent retraction is justified, or whether a re-review was carried out by a genuinely independent person. No source data is fetched from a private or production repository; the observations and statuses are all fictional self-declarations.

An `ADVISORY_CURRENT` result **never** means a verified diagnosis, a successfully repaired bug, an agent that learned from experience, or permission to take action. Every checkpoint explicitly returns `knowledge_promotion=NOT_GRANTED`, `execution_authority=NONE`, and `model_learning_or_training_performed=false`.

## Research gate after the synthetic stack

Before a real-agent comparison, separate the author's public fixture from independently prepared **held-out** data, freeze source availability cutoffs and evaluator access, and include a case where version-change governance adds overhead **without improving correctness**. Count total tokens, context selection, repeated analysis, latency, tool use, human review and invalid outcomes, not merely the number of accepted records.

See [contract and limits](knowledge-genealogy-v0.md), [public scenario catalog](../examples/knowledge-genealogy-cases-v0.json), and [draft evaluation design](experimental-design.md).
