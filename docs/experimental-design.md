# Experimental Design v0 — Draft

> **DRAFT / NOT SEALED / NO AGENT EXPERIMENTS RUN.** This document is a public plan, not an efficacy report.

## Research questions

- **RQ1:** Does evidence-gated two-agent coordination reduce invalid completions relative to basic two-agent collaboration?
- **RQ2:** Does it improve valid outcomes per measured cost when source identity and dependency complexity matter?
- **RQ3:** When is a simpler single-agent or lightweight workflow preferable?
- **RQ4:** Which component contributes: context selection, investigation protocol, or exclusive ownership?

Null results and measured overhead are acceptable findings.

## Fictional evaluation environment

A small SaaS-style notification application called FlowDesk contains an API, event producer, retry-capable queue, worker, and delivery log. Source code, logs, notes, visible tests, and tool access are matched across evaluation configurations.

The agent must produce a diagnosis, proposed patch or justified HOLD, and a validation record. The evaluator independently assesses the result with tests and instance-level ground truth kept out of the agent worktree.

## Eight planned scenario families

| ID | Challenge | Target property |
| --- | --- | --- |
| S01 | Simple local error | Avoid unnecessary process overhead |
| S02 | Old note contradicts current implementation | Context authority |
| S03 | Two agents pursue the same work | Exclusive claim |
| S04 | Test artifact belongs to an old revision | Revalidation |
| S05 | Failure crosses multiple components | Sectorized diagnosis |
| S06 | Two hidden worlds with identical visible traces | Correct abstention |
| S07 | Lease expires during interrupted work | Fencing and recovery |
| S08 | Visible test passes but delivery remains broken | Behavioral validation |

Descriptions are public **families**, not evaluation-instance solution keys. Public demonstration fixtures are excluded from any subsequent confirmatory set.

## Comparators and sample size

- **A — Strong single agent:** ordinary coding/debugging tools, direct access to the same synthetic facts.
- **B — Basic two-agent:** basic shared task board, no evidence gate.
- **C — Integrated two-agent:** governed discovery, structured investigation, fenced claims and evidence gate.

The primary contrast is **C vs B**. C vs A is secondary. A proposed exploratory pilot uses **8 scenarios × 3 configurations × 3 repetitions = 72 planned runs**. Three repetitions per condition are not sufficient for strong inference.

Budget caps (not yet frozen): 900 seconds wall time, 60 calls, 60,000 input tokens and 12,000 output tokens **per full run**, shared by collaborating agents. Freeze model version, prompts, seeds, run order, scoring and spending limits before collecting results.

## Deterministic gate (D01–D15)

D01 concurrent exclusive ownership; D02 stale generation fencing; D03 stale-owner closure rejection; D04 dependency cycles rejected; D05 revision changes invalidate prior evidence; D06 idempotent completion; D07 recovery; D08 unauthorized action denial; D09 confidence-only promotion rejected; D10 historical context does not become current authority; D11 correlated evidence does not count as independent; D12 evaluator-only data is inaccessible; D13 duplicate-delivery oracle distinguishes bug from fix; D14 unjustified HOLD is not rewarded; D15 incomplete test artifact is not validation.

These probes must be implemented and pass before real-agent comparison. **Passing a reference fixture test is not a proof of a production security boundary or empirical AI improvement.**

## Outcome classes

- **VALID_REPAIR:** correct repair plus independent acceptance and revision-bound evidence.
- **VALID_ABSTENTION:** on genuinely underdetermined evidence, asks for discriminating data rather than asserting an unsupported cause.
- **INVALID_COMPLETION:** incorrect or improperly substantiated closure.
- **INCOMPLETE:** timeout, unresolved case or unnecessary HOLD.
- **HARNESS_ERROR:** independently reported evaluation-system failure.

Report per-scenario and per-arm valid-outcome rate, invalid-completion rate, time, tokens, tool calls, measured cost, and rework. Report **cost per valid outcome** only with explicit cost basis and zero-denominator handling. Do not conceal failures behind an aggregate score.

## Study hygiene and threats to validity

Use comparable models and prompts, matched underlying facts and permissions, independent hidden acceptance, fresh sandbox per run, randomized configuration order, and preserved raw outcomes. Do not give C any additional private data. Publish unsuccessful results, uncertainty, and deviations.

Synthetic tasks can favor the architecture designed around them. The work may not generalize to large repositories or different models; fixed budgets do not guarantee equal reasoning opportunity. A confirmatory study would require held-out cases and a separately justified sample size. **None has been completed.**

See [machine-readable scenario catalog](../evals/scenarios-v0.json) and [draft preregistration](../evals/preregistration-v0.json).
