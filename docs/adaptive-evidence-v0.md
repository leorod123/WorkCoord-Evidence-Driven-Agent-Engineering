# Adaptive Evidence Escalation — Public Development Lab v0.2

> **EXPERIMENTAL / PUBLIC SYNTHETIC FIXTURE / NOT A REAL-AGENT OR HELD-OUT STUDY**

This minimal Python policy demonstrates when a researcher should **STAY**, **EXPAND** to another sector, **DEEPEN** the current sector, or **HOLD** rather than assert a diagnosis from insufficient data.

## Design contract

All four strategies receive the same per-case **source pool, permitted depth and source-body character budget**:

1. \`full_corpus\`: reads the complete **permitted** source pool, if it fits the cap; otherwise reports infeasibility.
2. \`local_sector\`: reads the declared starting sector/perspective/depth.
3. \`dependency_expand\`: follows up to two declared sector links at \`focused\` depth.
4. \`adaptive_policy\`: starts locally, inspects a *metadata-only* index for deeper sources in its current sector, follows **visible** dependency links, and applies a predeclared risk-dependent stopping rule.

The adaptive policy has no oracle parameter. Its \`_policy_args\` passes only start context, risk tier and action/depth/reading budgets, **not the case identifier, world, true cause, gold source IDs or intended answers**. Source-body text and annotated stances are made available only after a navigation action selects them. This is **API-level separation**, not a hardened process or security boundary.

## Conditions for action

- **STAY** produces a **provisional hypothesis only**. In the *low* risk tier, at least one current annotated supporting sector is enough, provided no declared dependency requires immediate expansion; for *high* risk, the heuristic requires support from at least two current source sectors and no visible unfinished link/deeper candidate. These are arbitrary toy parameters, **not true evidence independence** and **not permission to complete work**.
- **DEEPEN** reads the next allowed depth in the current sector, discovered via the source index without reading its body beforehand.
- **EXPAND** follows an unread sector dependency declared in an *already selected* source. It cannot infer missing links.
- **HOLD** records the reason when no permissible or useful next step remains: missing current coverage, conflicting observations, exhausted action/hop budget or evidence unable to fit in the character cap.

These choices are all observable as structured trace events; no concealed language model, extra ingestion service or external account is involved.

## Seven new cases (six situations plus a paired world)

| Case | Condition | Risk tested |
| --- | --- | --- |
| AD01 | Current local evidence, no remaining link | Staying may be cheaper than expanding |
| AD02 | Old worker guide, queue and API evidence connected by visible links | Need to expand |
| AD03 | Missing worker-to-queue links, even though other sectors remain queryable | **Avoidable HOLD**, not credited as sound abstention |
| AD04 | A necessary queue trace requires a permitted \`deep\` pass | Need to deepen |
| AD05A/B | Two hidden worlds have **identical accessible documents** but opposing causes inside *inaccessible* deep traces | **Both must HOLD**, not guess |
| AD06 | Strict common character cap blocks relevant observations | Resource-limited HOLD is not a valid task resolution |

The paired-world constraint is checked in code: the accessible records, task entrypoint, budget and policy are identical; the hidden deep traces differ. Every arm is limited to the **same permitted \`focused\` depth** in this pair.

## Evaluator behavior: no self-scored success

The [public development rubric](../evals/adaptive-oracle-v0.json) is applied by \`adaptive_evaluator.py\` **after** all candidate decisions have been collected. It does not select sources. It classifies each result as:

- **SUPPORTED_PROVISIONAL:** proposed label agrees with the public fixture and *all declared required evidence IDs were accessible and read*; **not causal verification**.
- **UNSUPPORTED_PROVISIONAL:** wrong label **or** missing required evidence, even if the answer happens to sound correct.
- **JUSTIFIED_HOLD_UNDER_DECLARED_ACCESS:** genuinely indistinguishable worlds under the specified permitted view.
- **AVOIDABLE_HOLD:** relevant evidence was accessible with current permissions, but the policy stopped searching.
- **RESOURCE_LIMITED_HOLD_NOT_SCORED_SUCCESS:** inability to satisfy the task due to the declared budget, not proof of a valid resolution.
- **COMPARATOR_INFEASIBLE_UNDER_EQUAL_CAP:** full-corpus baseline cannot include the complete permitted pool without breaking the common cap.

A HOLD that could have been resolved by a broader authorized search does **not** become a success just because the policy explains itself. All metrics are **development-fixture coverage and scripted decision metrics**.

## Reproduce

Python 3.10+; no external runtime libraries required:

\`\`\`bash
PYTHONPATH=src python -m workcoord_lab.adaptive_eval --output artifacts/adaptive-eval-v0.json
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/verify_adaptive_mutations.py
\`\`\`

GitHub Actions uploads a JSON receipt per Python version with the source, scenario, paired-world and public evaluation oracle SHA-256 values. The output includes individual action traces, source IDs, budgets, accepted/inaccessible depth, reasons for HOLD and every rubric grade.

## Explicit limitations

- A catalog that contains all source metadata exists as a local fixture. In a real retrieval system that index has latency, access control, metadata size and possibly sensitive fields; those costs are **not** modeled.
- The ranking heuristic reads **human-authored \`signals\` labels**, not prose comprehension. Revision/maturity are also fixture annotations, not authenticated Git or test provenance.
- Sector count is not independent confirmation; predeclared \`low\` / \`high\` risk tiers and evidence requirements were designed for this fictional set. They are neither calibrated nor neutral empirical treatment conditions.
- The "external" evaluator is external **to policy selection** but **published in the same repository**. It is not secret, held-out, adversarially isolated, or independently audited.
- Reading cost is **unique source-body characters only**; metadata scans, index overhead, model context packing, tokenization, reasoning, API fees and agent runtime are omitted.
- A \`SUPPORTED_PROVISIONAL\` outcome is not a verified root-cause diagnosis, passing patch, authorization, real-agent quality gain, or scientifically generalizable result.
- The full-corpus arm is explicitly **infeasible** under AD06's common cap; a zero read count for an infeasible run is not "cheap success."
- No production services, real trades, real user data, or private project material are involved.

## Next evidence gate

Review negative cases and mutation coverage; only then define a separate, genuine **held-out real-agent** evaluation with independently administered source visibility, same tool budgets and acceptance tests, and total end-to-end cost accounting. Public development cases must never be repurposed as unseen evaluation.

See [prior comparison](context-comparison-v0.md) and [experimental design](experimental-design.md).
