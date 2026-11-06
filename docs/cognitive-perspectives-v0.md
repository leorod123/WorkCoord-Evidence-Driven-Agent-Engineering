# Cognitive Perspectives v0 — One Problem, Four Advisory Lenses

> **Public synthetic development reference.** This is a deterministic multi-perspective *record evaluator*, **not four LLM agents**, an autonomous research system, an independent source verifier, or a governance authority.

## Purpose

A technical incident can appear resolved from one angle and remain ambiguous from another. Instead of cloning coordinators or creating four permanent agents, we use four **explicit, typed perspectives** to examine **one issue, one proposed remedy and one source revision**.

This adds an independent dimension to the existing [sector-based context navigator](intelligence-walkthrough.md):

- **Technical sector:** where evidence originates — e.g., queue, worker, delivery, API.
- **Cognitive perspective:** which question the evidence must answer.

A perspective can cite sources from multiple technical sectors. All perspectives contribute to **one shared, reproducible advisory checkpoint**; none acquires work ownership, grants execution authority or promotes evidence into truth.

## Perspective questions

| Perspective | Core research question | Typical adversarial observation |
| --- | --- | --- |
| `RESEARCH` | What could falsify the current explanation? | A causal narrative still fits a competing hypothesis |
| `ENGINEERING` | Which required behavior did tests actually exercise? | Green unit tests do not verify external delivery |
| `EFFICIENCY` | Is additional process/component cost justified? | A new service incurs maintenance without sufficient incremental value |
| `RISK` | What failure or permission boundary could invalidate the action? | Downstream retries and unapproved execution scope remain unresolved |

The perspective labels are **not the identities of independent experts**. They can all be written by one person or one test fixture, and their repeated citations may share the same origin group.

## Three admission depths

| Risk tier | Required lenses | Intended trade-off |
| --- | --- | --- |
| `QUICK` | Engineering, as a cheap local check | Avoid mandatory four-lens overhead for a bounded reversible fix |
| `STRUCTURED` | All four perspectives | Expose distinct challenges, missing coverage and disagreements |
| `CRITICAL` | All four, then external review | Even unanimous declarations are not permission to act |

Any additional perspective voluntarily supplied for a `QUICK` issue is still evaluated. **A risk challenge cannot be ignored merely because that lens was optional.**

A review record contains the same `issue_id` and `proposal_id`, perspective, stance (`SUPPORT`, `CHALLENGE`, `UNCERTAIN`), source revision and logical review tick, cited evidence IDs, counterevidence references, rationale, open question, suggested next discriminating test and **declared** review effort.

**Audit refinement A05:** A `SUPPORT` perspective that cites a counterexample can no longer silently reach `ADVISORY_READY`. Counterexamples are `OPEN` unless explicitly included in typed `counterevidence_resolutions` with `state=RESOLVED`, nonempty justification and a **different, cited non-counterexample** `basis_source_id`. Unresolved counterexamples cause `HOLD_UNRESOLVED_COUNTEREVIDENCE`; declared dispositions remain in the checkpoint. These are still unauthenticated declarations, not independently validated resolutions. A CHALLENGE stance remains an objection.

## Shared checkpoint and conflict rules

The reader checks a declared revision and **source availability at the review tick**. For each referenced document it records the technical sector, declared origin group, revision, availability tick and SHA-256 of the literal cited *finding text*. An unknown, old or not-yet-available source creates an explicit gap. A stale lens cannot silently be treated as current after a revision change.

The result preserves all lens notes, source references, counterevidence and open questions in canonical order. The final `checkpoint_sha256` is calculated over the normalized output (excluding the hash itself), so a change to cited text, stance, source revision, costs or conflicts creates a different checkpoint identity.

A `SUPPORT` + `CHALLENGE` disagreement produces **`HOLD_CONTRADICTION`**, even when three perspectives support the proposal and only one challenges it. It is **not** resolved by vote or by claimed confidence. `UNCERTAIN` similarly remains unresolved. Missing mandatory lenses and invalid source references are visible rather than replaced with synthetic agreement.

A complete, unchallenged `QUICK` or `STRUCTURED` packet can return **`ADVISORY_READY`**; this means only that the packet passed its own declared admission checks. A locally complete `CRITICAL` packet returns **`REQUIRES_EXTERNAL_REVIEW`**.

**Every result includes:**

- `execution_authority: NONE`
- `work_ownership: NOT_ASSIGNED`
- `knowledge_promotion: NOT_GRANTED`
- `source_independence_authenticated: false`
- `external_problem_acceptance_verified: false`

It cannot close a Problem Map, authorize execution, establish scientific truth or sign a review.

## Cases that test the limits

The [19 fictional cases](../examples/cognitive-perspective-cases-v0.json) are publicly labeled training/development fixtures.

| Case | Intended adversarial behavior |
| --- | --- |
| CP01 | Four supporting lenses produce only a consultative candidate |
| CP02 | Three supporters cannot outvote an explicit risk challenge backed by counterevidence |
| CP04–CP06 | Missing, stale or source-invalid perspectives block a seemingly complete review |
| CP07 | Critical unanimity still requires external review |
| CP08 | One engineering lens can handle a simple low-risk check with fewer declared review units |
| CP09 | A voluntarily added risk challenge still blocks a QUICK case |
| CP10, CP16 | Sources or reviews cannot be used before their declared availability/decision time |
| CP11 | Duplicate source origin groups do not magically become independent |
| CP12 | Increasing self-reported review cost does not improve authority or accuracy |
| CP18 | A missing engineering lens does not erase the recorded research/risk disagreement |

The catalog's expected statuses are **visible in the repository** and deliberately authored with the cases. They are not held out and do not measure a real model's ability to reason across specialties.

## Reproduce

Python 3.10+, no external runtime dependencies:

```bash
PYTHONPATH=src python -m workcoord_lab.cognitive_perspectives_suite --output artifacts/cognitive-perspectives-v0.json
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/verify_cognitive_mutations.py
```

A single custom fixture can be inspected using:

```bash
PYTHONPATH=src python -m workcoord_lab.cognitive_perspectives my-cognitive-review.json
```

GitHub Actions runs the entire deterministic suite in Python 3.10, 3.11 and 3.13 and uploads a per-version JSON receipt that includes the catalog SHA-256 and case-level checkpoint hashes. Deliberate mutation probes M40–M53 must each be detected by their specific failing negative-control test, never merely by an import error.

## What this does **not** establish

This is a small **contract and disagreement demonstration**. No LLM is invoked, no independent cognitive agent has contributed a genuine novel argument, and the source labels, timestamps and cost units are unverified. SHA-256 binds the text of the cited synthetic record to the checkpoint; it does **not** certify that record's truth, creator, timestamp or legal origin.

The effort model counts **declared review units** and distinct cited source-body characters, not actual human labor, tokens, tool calls or end-to-end cost. A full structured review can be more expensive than the QUICK route without adding value. A four-lens consensus is not proof of correctness, absence of omitted evidence, causal identification, or permission to execute.

The next reference step is **Knowledge & Learning v0**: preserve source lineage, changes, negative observations and invalidations over time. Only then design a genuine, independently scored held-out agent study, with the cost of consulting multiple perspectives counted alongside its potential benefits.
