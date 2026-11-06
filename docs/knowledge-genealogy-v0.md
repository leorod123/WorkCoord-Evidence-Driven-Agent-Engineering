# Knowledge & Learning v0 — Traceable Source and Belief Genealogy

> **Status:** executable, standalone, public fictional development demonstration. The code does **not** authenticate sources, learn a statistical model, certify a conclusion, grant work ownership, or authorize actions.

## Question

How can a previously admissible advisory conclusion become outdated when the evidence it relied upon changes, **without rewriting history or silently reinstating the conclusion**?

The reference deliberately separates three things:

1. **Sources and immutable revisions.** A source ID belongs to a declared lineage and revision. A later revision may be staged, but only an explicit `SOURCE_SUPERSEDE` changes the active version.
2. **Observations and counterevidence.** An observation is linked to a source ID and a claim and is explicitly `SUPPORT` or `CHALLENGE`. A negative observation is not diluted by a majority of positives. A later retraction is an appended event with a reason, not a deletion.
3. **Claims and review receipts.** A review binds the exact set of currently applicable supporting observation IDs and the accepted review identities of dependent claims. The result is only `ADVISORY_CURRENT`—**not scientific validation**.

A source revision, dependent review or relevant new observation can invalidate that advisory state. The system never updates a claim to point to a newer source just because one exists; a new observation and an explicit review are required.

## One typed append-only log

The event model is intentionally small:

| Event | Required meaning |
| --- | --- |
| `SOURCE_ADD` | Register a source ID, lineage, revision, fictional body and availability tick |
| `SOURCE_SUPERSEDE` | Explicitly replace the active source in one lineage with a staged successor; preserve the old ID |
| `CLAIM_OPEN` | Record a proposed conclusion and dependencies on earlier claims |
| `OBSERVATION_ADD` | Add a source-linked SUPPORT or CHALLENGE finding |
| `OBSERVATION_RETRACT` | Append a named retraction with a reason; retain the negative observation |
| `REVIEW_ACCEPT` | Bind **all** currently applicable supports and the reviews of current parent claims, only when no current contradiction exists |

Every event has a contiguous sequence, unique event ID, monotonic *logical* tick, predecessor SHA-256 and digest of its canonical JSON bytes. Replay checks the complete supplied hash chain before evaluating a prefix. Historical snapshots are requested with `at_seq`.

**Audit refinement A02:** The identity of an `at_seq` checkpoint contains **only events available in that prefix**; the former `verified_supplied_chain_head_sha256` field was removed from the historical receipt. Call `verify_chain(records)` separately to verify and retrieve the **entire supplied chain** head. Later replay of the prefix is deterministic, but without an independently trusted anchor it is **not evidence that the checkpoint was actually anchored at that earlier time**.

The digest provides **internal tamper evidence relative to a trusted head**; an attacker able to rewrite and rehash the entire log can forge a new chain. No independent anchor, signature, trusted clock, source retrieval or external reviewer identity is provided here.

## The central negative demonstration

The fictional notification incident starts with:

1. A source at revision `r1`, a supportive observation, and an explicit review → `ADVISORY_CURRENT`.
2. A fictional `r2` source is registered → no change, because it is only **staged**.
3. `SOURCE_SUPERSEDE(r1, r2)` → the earlier conclusion becomes **`HOLD_STALE_BASIS`**. The previous source, review and observation remain inspectable.
4. A new observation citing `r2` arrives → **still HOLD**; there is no implicit source rebinding.
5. A new `REVIEW_ACCEPT` explicitly binds the replacement source observation → `ADVISORY_CURRENT` again. This is renewed *advisory eligibility*, not confirmation of causal truth.

`KG02` exercises the invalidation; `KG03` exercises the explicit reconstruction; `KG15` checks that even **identical body text under a new revision** does not silently inherit an old review's legitimacy.

### Negative evidence is first-class

In `KG04`, a current `CHALLENGE` immediately yields `HOLD_COUNTEREVIDENCE`. A subsequent `REVIEW_ACCEPT` cannot omit it. `KG05` records a retraction but leaves the claim at `HOLD_REVIEW_REQUIRED` until re-reviewed. `KG06` shows re-review followed by current advisory status **while the retracted negative observation and its reason remain in historical output**.

### Transitive effects are not majority votes

`KG07` creates a second reviewed claim depending on the first. When the first claim's source is superseded, the dependent claim becomes `HOLD_UPSTREAM`.

`KG08` then restores the upstream review, but the dependent claim stays at `HOLD_UPSTREAM_REVIEW_CHANGED`: the dependency's accepted review identity is different. `KG09` requires a new explicit downstream review to restore the second claim. An unrelated lineage update (`KG13`) does not invalidate a claim, so the mechanism does not simply mark everything stale.

## Exactly what is evaluated

`replay_events` reconstructs active source lineages, all observations including retracted ones, claim status, and an ordered **transition history**. The report includes distinct `HOLD_UNREVIEWED`, `HOLD_STALE_BASIS`, `HOLD_COUNTEREVIDENCE`, `HOLD_RETRACTED_BASIS`, `HOLD_REVIEW_REQUIRED`, `HOLD_UPSTREAM` and `HOLD_UPSTREAM_REVIEW_CHANGED` states.

Every result explicitly declares:

- `knowledge_promotion: NOT_GRANTED`
- `execution_authority: NONE`
- `work_ownership: NOT_ASSIGNED`
- `independent_scientific_validation: false`
- `model_learning_or_training_performed: false`

Thus `ADVISORY_CURRENT` is a temporal consistency label on authored sources and reviews. It is never equivalent to `VALIDATED`, a verified software repair, production permission, or an independently correct diagnosis.

## Reproduce

Python 3.10+ with only the standard library:

```bash
PYTHONPATH=src python -m workcoord_lab.knowledge_genealogy_suite --output artifacts/knowledge-genealogy-v0.json
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/verify_genealogy_mutations.py
```

The [19 public fictional cases](../examples/knowledge-genealogy-cases-v0.json) provide their own *visible*, human-authored expected labels, so they are not held-out benchmarks. Each scenario is sealed into a reproducible SHA-256 event chain, re-evaluated, and optionally replayed at predefined historical cuts.

The receipt records the fixture SHA-256, case-level event-head hashes, claim status maps and transition counts. The CI matrix (Python 3.10, 3.11, 3.13) re-runs all existing reference tests and **M1–M53**, plus the new genealogy mutations **M54–M70**. Each named mutation must lead to an assertion failure in its designated test; an exception or timeout does not count as successful detection.

A single JSON list of fictional actions can be evaluated with:

```bash
PYTHONPATH=src python -m workcoord_lab.knowledge_genealogy example-actions.json --at-seq 4
```

## Limits and scientific next gate

This is **knowledge history and decision hygiene**, not machine learning. No source file is independently authenticated, no external Git revision is verified, no reviewer signature is checked, no real temporal clock is trusted, and no new fact is discovered by the replay rules. Hashes do not confer provenance or legality on user-supplied strings.

The reference intentionally does not integrate with production databases, work coordination, model training, authorization backends or an external agent. It cannot know whether a withdrawn counterexample was withdrawn for valid reasons; its behavior ensures only that the withdrawal is visible and followed by a new review.

A meaningful held-out experiment must isolate the evaluator and source truth, measure retrieval/compute/token costs, and test whether agents can use these records to avoid stale conclusions **without over-reacting to irrelevant history**. A lightweight ungoverned control must remain in the comparison.
