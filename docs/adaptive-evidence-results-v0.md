# Adaptive Evidence Escalation — Executed Synthetic Results v0

**Status:** deterministic, public development evidence about a scripted policy. **Not an independent held-out evaluation, agent-performance benchmark or production reliability claim.**

**First complete validated execution:** [GitHub Actions run 42158041852](https://github.com/leorod123/WorkCoord-Evidence-Driven-Agent-Engineering/actions/runs/42158041852), candidate commit `98e9c5c7257eaccb8c16408e378b4e80abce8e57`. Python 3.10, 3.11 and 3.13 each passed **98/98 unit tests**. Five deliberate M12–M16 mutations (deepen, expand, risk-coverage criterion, false HOLD credit and evidence completeness) were detected by named failing tests. Earlier M1–M11 regressions remain checked. Each job saved a source-hash-bound JSON receipt `adaptive-eval-v0.json`.

## All seven public synthetic cases

| Strategy | Source-body chars read, total | Mean recall of required sources | Evidence-supported provisional labels | Justified limited-access HOLDs | Unsupported proposals | Avoidable HOLDs | Other |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Full corpus | **6,001** | **57.1%** | **4** | **2** | **0** | **0** | 1 infeasible under common cap |
| Local sector | **1,400** | **14.3%** | **1** | **2** | **4** | **0** | No budget-infeasible comparator |
| Fixed dependency expansion | **2,522** | **28.6%** | **2** | **2** | **3** | **0** | 1 lucky-looking label without decisive evidence |
| **Adaptive policy** | **3,161** | **42.9%** | **3** | **2** | **0** | **1** | 1 budget-limited HOLD, *not credited as success* |

These percentages are descriptive fractions of seven deliberately authored tasks, **not confidence estimates**. The 2 HOLDs reflect the matched pair of worlds with identical allowed observations and opposite inaccessible causes. The full-corpus comparator cannot fit all permitted source bodies into AD06's very small budget; its reported zero characters in that case mean **infeasible**, not a cheap success.

## Adaptive policy: case-level result

| Case | Recorded decision | Public development grade | What it demonstrates |
| --- | --- | --- | --- |
| AD01 | STAY | SUPPORTED_PROVISIONAL | Avoiding unnecessary expansion in the deliberately low-risk local case |
| AD02 | EXPAND and eventually STAY | SUPPORTED_PROVISIONAL | Following queue and API links to current counterevidence |
| AD03 | HOLD | **AVOIDABLE_HOLD** | A missing link prevents discovery of sources that still exist and are accessible |
| AD04 | DEEPEN then STAY | SUPPORTED_PROVISIONAL | Reaching a permitted `deep` source that a fixed focused expansion misses |
| AD05A / AD05B | HOLD in both | JUSTIFIED_HOLD_UNDER_DECLARED_ACCESS | Opposite hidden causes with identical observable inputs cannot be distinguished |
| AD06 | HOLD | RESOURCE_LIMITED_HOLD_NOT_SCORED_SUCCESS | Honoring the budget without inventing evidential resolution |

The adaptive result is intentionally **mixed**. It avoids unsupported provisional proposals in these fixtures but is more expensive in source-body characters than fixed dependency expansion, and it does not resolve all cases which the full-corpus comparator can handle. A method that labels every case HOLD would not satisfy the evaluator, because an avoidable HOLD is not a success.

## What this run does and does not establish

**Reproducible:** the policy records its navigation steps, stop reasons, source IDs and exact character budget. The public evaluator is applied to the resulting action records and can identify unsupported hypotheses, missing decisive evidence and unjustified abstentions. M12–M16 regressions are detected in test copies.

**Not proven:** that a real AI agent can reliably recognize independent evidence, choose better contexts, achieve lower total token/API costs, diagnose real faults, or become more efficient by adopting this policy. The rubric is explicitly published; the source stances are authored labels; `risk_tier` and source requirements are designed for these examples, which makes the measured outcomes susceptible to construction bias.

Character accounting excludes metadata scans, index cost, context packing, prompts, inference, latency and rework. The pair validates observational equivalence **at the declared access depth**, not cryptographic isolation of hidden evaluator information.

## Forward gate

1. Conduct an independent adversarial review of case design, policy leakage, evaluator bias, ranking sensitivity and selection failure modes.
2. Separate **training/public cases** from new, truly held-out real-agent tasks and freeze source visibility, prompts, tool budgets and acceptance rubrics.
3. Include at least one credible control where the full-corpus strategy is stronger and at least one case where the adaptive strategy adds overhead without improving the outcome.
4. Measure end-to-end successful outcomes **and** failed work/attempts/cost; never promote `SUPPORTED_PROVISIONAL` into a verified repair.

See [method and limits](adaptive-evidence-v0.md), [new cases](../evals/adaptive-cases-v0.json), and [public development evaluator](../evals/adaptive-oracle-v0.json).
