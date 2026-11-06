# Vertical Evidence Chain v0 — Executed Synthetic Integration Results

**Status:** public deterministic **development** integration. **Not** a real-agent benchmark, independent source validation, verified software repair, scientific correctness result or authorized final decision.

## Exact candidate verification

- Tested source head before adding this documentation: `460752c85731e494c96fffbccba9ace99ca89e35`.
- [GitHub Actions run 42167687682](https://github.com/leorod123/WorkCoord-Evidence-Driven-Agent-Engineering/actions/runs/42167687682): **PASS** in Python **3.10, 3.11 and 3.13**.
- Each job passed **287/287 deterministic unit tests** and killed **88/88 deliberate mutations M1–M88** by their specific negative-control assertion failures. No missing mutation.
- **14/14 synthetic development scenarios** matched their author-declared expected statuses over **21 historical cuts**, and **4/4 malformed cross-stage identity/authority cases were rejected**.
- Three deterministic GitHub Actions JSON receipts were archived as `vertical-evidence-py-3.10`, `vertical-evidence-py-3.11` and `vertical-evidence-py-3.13`. Each contains the catalog SHA-256, per-cut checkpoint digests and stage statuses.

All these outcomes are about *contract software tests*. None is an independently observed model success or real incident outcome.

## Observed public-fixture classifications

Across 14 cases and 21 explicitly declared snapshots:

| Synthetic advisory status | Historical cuts | Meaning |
| --- | ---: | --- |
| `ADVISORY_CANDIDATE_FOR_EXTERNAL_ACCEPTANCE` | 7 | Original gates locally favorable; **no external acceptance** |
| `HOLD_KNOWLEDGE` | 5 | Current genealogy has counterevidence or needs re-review |
| `HOLD_REASSESS_REVISION` | 2 | Active source epoch differs from the version underlying earlier stages |
| `HOLD_PROBLEM` | 1 | Required behavior witness missing despite technical tests green |
| `HOLD_RESEARCH` | 2 | Required falsifier missing or plan frozen after outcome |
| `HOLD_COGNITIVE` | 3 | Missing/uncertain/opposing perspective |
| `REQUIRES_EXTERNAL_REVIEW` | 1 | Locally complete critical packet, never authorization |
| **Total historical cuts** | **21** | **Not 21 independent task samples** |

Four additional malformed packet cases are a separate rejection category; they are not included in these 21 cuts.

## The decisive transition

**VI01** is one fictional ticket with four original evaluators. At **cut 4**, Research returns `DESIGN_ADMISSIBLE`, Problem `CANDIDATE_FOR_EXTERNAL_ACCEPTANCE`, Cognitive `ADVISORY_READY` and Genealogy `ADVISORY_CURRENT`. The vertical result is therefore a narrow **advisory candidate**, not a verified repair.

The same case evaluated at **cut 6** has two additional events: a new fictional downstream source and a `CHALLENGE` observation. Earlier Research, Problem and Cognitive results are **bit-identical**, and their receipt hashes unchanged; the genealogy returns `HOLD_COUNTEREVIDENCE`, so the vertical result is **`HOLD_KNOWLEDGE`**, with the negative observation preserved. The checkpoint hash changes.

Importantly, **cut 5 does not see the event-6 finding**: merely registering a later source is not the same as introducing contradictory observed evidence. The historical cut is respected.

## Adversarial outcomes that matter

- **VI02:** a counterexample that is explicitly retracted still requires a new review. A retraction without review leaves `HOLD_KNOWLEDGE`; only a fresh advisory review may restore candidacy.
- **VI03–VI04:** source supersession creates `HOLD_REASSESS_REVISION`. Even after the Genealogy claim is re-reviewed on the new source, the old Research, Problem and Cognitive inputs are invalid until the entire evaluation is refreshed.
- **VI05:** green technical tests and `DONE` work status do not replace a mandatory user-visible delivery behavior probe.
- **VI06–VI09, VI14:** scientific flaws and unresolved cognitive challenges independently block a favorable final verdict.
- **VI10:** a simple QUICK task can remain a candidate with only one required cognitive perspective and no heavy alternative-cost matrix.
- **VI11:** all locally complete critical inputs still lead to required **external review**, not authority to act.
- **VI12:** unrelated source supersession does **not** invalidate an unaffected claim. Overly broad invalidation would add unnecessary overhead.
- **VI13:** more positive evidence itself requires a fresh review of changed premises.
- **VI15–VI18:** stitching another issue, changing cited text without its digest, silently changing the selected remedy, or forging an approval field leads to explicit input rejection.

### Boundaries

This is one **fictional, self-declared and publicly scored development fixture**, not hidden or confirmatory data. The digest verifies consistency among authored records, but not where the information originated or whether it is true. The genealogy uses logical event cuts; it does not establish a shared external clock with the other three stages. Earlier stages remain frozen for the sake of the demonstration; a real implementation would require authentic source revision checks and independently renewed evaluations.

The 21 cuts deliberately reuse the same authored tickets. They are **not independent observations**, nor estimates of effect size, latency, savings or real success probability. Added context, review overhead and false/avoidable HOLDs still need measured comparisons against a simple baseline.

Every result preserves `authorization=NONE`, `work_ownership=NOT_ASSIGNED`, `knowledge_promotion=NOT_GRANTED`, `independent_outcome_verified=false` and `model_learning_performed=false`.

## Remaining independent gates

1. Conduct an adversarial architecture/security/rights review, especially whether the asserted common-source binding is strong enough for an actual deployment and whether public text is fully independent of private sources.
2. Decide the open-source license and how/when to merge or retarget the stacked draft PRs.
3. Freeze genuinely held-out, **externally evaluated** real-agent scenarios with equal source visibility/decision budgets, include cases where simpler approaches outperform the complete stack, and measure cost per independently valid outcome.

See [method and limitations](vertical-evidence-v0.md), [public synthetic case catalog](../examples/vertical-integration-cases-v0.json) and [draft experimental design](experimental-design.md).
