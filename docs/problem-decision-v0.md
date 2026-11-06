# Problem & Decision v0 — Semantic Closure Is Not a Green Test

> **Experimental public reference.** This is a self-contained, fictional admission checker, not a hosted coordinator, source authenticator, cost optimizer, deployment gate, or independent acceptance test.

## The problem

A work unit can report `DONE` and every technical test can report `PASS` while **the actual user objective remains unresolved**. An output-based acceptance criterion may not have been tested; a required subproblem may still be unknown; the selected remedy may not address one of the obligations.

**Research design, problem definition, solution comparison, application planning, and proof of a resolved outcome are separate objects.**

The companion [Research Quality v0](research-quality-v0.md) checks scientific-design safeguards. This module instead checks whether a **hierarchical problem** and the **selected solution proposal** are complete enough to request an independent acceptance review. Neither module grants authorization or proof of causal correctness.

## Four distinct records

1. **Problem and goal.** A problem ID, statement, desired observable outcome and pinned *declared* source revision.
2. **Problem Map.** Exactly one required root and a hierarchy of required or optional nodes. Each node has a declared knowledge state (`KNOWN`, `HYPOTHESIS`, `UNKNOWN`) and explicit acceptance criteria. A criterion demands either a `technical_test` or `behavior_probe` witness.
3. **Decision.** Several possible remedies (`reuse`, `simplify`, `adapt`, `build`, `defer`), which required **leaf nodes** each addresses, initial and recurring assumed cost, allowance for risk/rework, and a stated choice/rationale.
4. **Application.** Separate steps, implementation mode, rollback when reversible and impact-containment notes for high-stakes work.

The **report** is a fifth, independent object: it never edits the ledger, grants a knowledge transition, authorizes an action, or marks the semantic problem closed.

### Technical pass versus acceptance witness

Consider the fictional FlowDesk incident:

| Required problem | Criterion | Declared witness |
| --- | --- | --- |
| Overall goal | One notification per logical event, even after retry | End-to-end *behavior probe* |
| Worker implementation | Idempotency guard passes a unit check | Technical test |
| Delivery effect | Exactly one externally visible notification | Delivery *behavior probe* |

In **PD02**, the fictional implementation reports **technical tests green**, with a valid-looking worker test and one end-to-end probe, but the **delivery effect witness is missing**. The admission gate returns `HOLD_REQUIRED_PROBLEM_OPEN` and keeps `delivery` on its mandatory open-node list. The parent goal does not become resolved just because the technical task was marked `DONE`.

In **PD16**, a technical test was *incorrectly offered in place of* a required delivery behavior probe. The gate rejects it as the wrong evidence kind. In **PD06**, both PASS and FAIL are declared for the current delivery criterion; the FAIL remains a contradiction and blocks readiness. In **PD17**, the leaf criteria pass, but the root acceptance witness is absent; the result still blocks admission.

Positive fixtures may reach `CANDIDATE_FOR_EXTERNAL_ACCEPTANCE`; that **does not mean a real outcome was independently validated**. The witness IDs, revisions and results are merely self-declared fictional JSON fields.

## Different governance depths

| Depth | Local checks and effort |
| --- | --- |
| `QUICK` | One bounded problem with its specific acceptance witness. An option matrix and application plan are optional. |
| `STRUCTURED` | Distinct remedies, explicitly required-node coverage, same-horizon cost estimates, rationale, plan and rollback if reversible. |
| `CRITICAL` | Structured checks plus impact containment. A locally complete design returns `REQUIRES_EXTERNAL_REVIEW` with no action authority. |

A required node whose knowledge state is `HYPOTHESIS` or `UNKNOWN` cannot be silently closed by technical PASS. Optional unknown nodes remain visible without automatically blocking every parent. Parent cycles, nonexistent parents, required descendants of optional nodes, duplicate IDs and mismatched evidence targets are rejected as malformed input.

## Cost comparison: assumptions, not savings

Every option is compared at **one identical declared horizon** and in the same synthetic effort unit:

```text
assumed_total_units = upfront_units
                    + horizon_cycles * recurring_units
                    + risk_allowance_units
                    + rework_allowance_units
```

This intentionally makes a cheap-to-build but expensive-to-maintain option visible. In **PD10**, the declared total is **11** units for reuse versus **73** for build across 24 cycles. These are invented assumptions, **not measured currency, expected value or a validated return**.

When a selected `build` option is more expensive than a comparable declared `reuse` or `simplify` option covering all required leaves, the alternative's rejection reason must be recorded. A free-text explanation is auditable **but not proof that building is actually necessary**. The admission checker does not choose an option itself or claim that the lowest declared cost is universally optimal.

A selected option that does **not** address all mandatory leaves is incomplete even if all described tests pass. `defer` is a recorded decision **not to complete**, never a successful implementation.

## Deterministic development cases

The [public synthetic catalog](../examples/problem-decision-cases-v0.json) contains **21 case variations**:

- 7 provisional candidates for external acceptance,
- 8 with required problems or evidence still open,
- 5 with incomplete alternative/application decisions,
- 1 locally complete critical design requiring external review.

The catalog contains the expected labels next to the fictional inputs; this is **not a sealed oracle**. The suite only checks whether the documented admission contract behaves as designed. Test names, receipts and negative cases are inspectable.

## Reproduce

From a checkout of the candidate branch, with Python 3.10+:

```bash
PYTHONPATH=src python -m workcoord_lab.problem_decision_suite --output artifacts/problem-decision-v0.json
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/verify_problem_mutations.py
```

The direct evaluator accepts any user-authored JSON packet conforming to the schema:

```bash
PYTHONPATH=src python -m workcoord_lab.problem_decision my-problem.json
```

CI runs the 21-case catalog in Python 3.10, 3.11 and 3.13 and saves the deterministic JSON receipt, containing the **SHA-256 of the public case catalog**. Explicit mutation probes **M25–M37** remove or weaken one check at a time: behavior-vs-test typing, revision matching, required-child coverage, negative evidence, alternative scope, recurring costs, cheaper reuse justification, lightweight quick path, external critical review, knowledge uncertainty, root acceptance, optional branches and illicit closure promotion. A mutant only counts when a named negative-control test fails, not when the process crashes.

## Boundaries and remaining research

- The source revision, witness result, work status, cost assumptions, rationale and rollback are **unverified fields**; no trusted implementation state or external evidence is consulted.
- Readiness is an **advisory proposal**. Output explicitly holds `semantic_closure_granted=false`, `knowledge_promotion=NOT_GRANTED` and `execution_authority=NONE` even for valid-looking cases.
- Hierarchy validity is tested, but this is not a general dependency scheduler or full causal Problem Map. It does not synthesize problems, infer causal necessity, verify source signatures, or track long-term outcome quality.
- Cost calculations deliberately omit measured labor, tokens, infrastructure, externalities and probability calibration. Providing cost numbers does not prove cost effectiveness.
- No agent benchmark or improvement in quality, latency, ROI or productivity is claimed.

**Next:** an independently authored cognitive-perspective example should let research, engineering, efficiency and risk challenge *the same* problem without creating new authorities, autonomous daemons or duplicate coordinators. After that, source genealogy and genuine external evaluation can be studied.
