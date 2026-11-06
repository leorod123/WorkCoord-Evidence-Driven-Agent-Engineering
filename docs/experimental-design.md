# Experimental Design v0 — Draft

> **DRAFT / NOT SEALED / NO AGENT EXPERIMENTS RUN.** This document is a public plan, not an efficacy report.

## Research questions

- **RQ1:** Does evidence-gated two-agent coordination reduce invalid completions relative to basic two-agent collaboration?
- **RQ2:** Does it improve valid outcomes per measured cost when source identity and dependency complexity matter?
- **RQ3:** When is a simpler single-agent or lightweight workflow preferable?
- **RQ4 (DEFERRED):** Which component contributes: context selection, investigation protocol, or exclusive ownership? The initial A/B/C study cannot identify individual effects because the integrated arm changes several mechanisms at once. A future experiment must predefine ablations.

Null results and measured overhead are acceptable findings.

## Fictional evaluation environment

The separate [synthetic context walkthrough](intelligence-walkthrough.md) provides a transparent *design probe*, with expected diagnostic annotations authored in the fixture. A subsequent [three-strategy retrieval comparison](context-comparison-v0.md) includes four public development cases with explicit failures of selective retrieval. A further [adaptive decision-policy experiment](adaptive-evidence-v0.md) adds a fourth strategy, seven new cases, a paired-world indistinguishability test and independent-of-selection public grading of avoidable versus justified HOLD. **Both exercises are excluded from future held-out agent evaluation** and cannot establish measured token, decision quality or productivity improvements.


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

The primary contrast is **C vs B** for the complete integrated package only. C vs A is secondary and also varies agent count. No improvement should be attributed specifically to context selection, research or fencing without controlled ablations. A proposed exploratory pilot uses **8 scenarios × 3 configurations × 3 repetitions = 72 planned runs**. Three repetitions per condition are not sufficient for strong inference.

Budget caps (not yet frozen): 900 seconds wall time, 60 calls, 60,000 input tokens and 12,000 output tokens **per full run**, shared by collaborating agents. Freeze model version, prompts, seeds, run order, scoring and spending limits before collecting results.

## Deterministic gate (D01–D15)

D01 concurrent exclusive ownership; D02 stale generation fencing; D03 stale-owner closure rejection (now with isolated controls and M1/M2 mutations); D04 dependency cycles rejected; D05 revision changes invalidate prior evidence; D06 idempotent completion; D07 recovery; D08 unauthorized action denial; D09 confidence-only promotion rejected; D10 historical context does not become current authority; D11 distinct declared provenance groups do not constitute independently proven evidence; D12 evaluator-only data is inaccessible; D13 duplicate-delivery oracle distinguishes bug from fix; D14 unjustified HOLD is not rewarded by a toy labeler; external review is required; D15 incomplete test artifact is not validation.

These probes must be implemented and pass before real-agent comparison. **Passing a reference fixture test is not a proof of a production security boundary or empirical AI improvement.**

## Common external evaluator — required before real-agent runs

**Unit and denominator:** one preassigned scenario × arm × repetition run. The primary result is the proportion of **externally validated correct outcomes** among all preassigned runs, including failures and timeouts. A valid repair passes the **same independent held-out behavioral acceptance tests** across A, B and C; a valid abstention must satisfy an access-aware rubric and identify specific missing discriminating information. A blank HOLD earns no credit. Report correct repairs and abstentions separately as well as the combined rate.

**Attempt versus gate:** capture the proposed diagnosis/patch, independent correctness, each unjustified declaration of completion, whether the arm's gate accepted or rejected it, subsequent recovery, and the final external outcome. Blocking every completion cannot yield a successful experiment. An erroneous attempted closure remains an erroneous attempt even if C blocks it.

**Harness errors and retries:** define shared infrastructure/evaluator faults *without seeing the candidate's correctness*. Include original assigned runs in the primary denominator as not externally validated, report them separately and show an eligibility-restricted sensitivity analysis. Arm-specific crashes count as INCOMPLETE. Permit at most one same-seed replacement for an independently established common harness error, preserve both records, and prohibit outcome-driven reruns.

**Cost and stopping:** stop on external acceptance, per-run tool/token/wall-time cap, or a defined irreversible policy block. Account for total cost of *all assigned runs*, including failed attempts and coordination overhead. Cost per valid outcome is undefined/infinite if there are no valid outcomes; never silently report zero. Retain each scenario's distribution, do not rely on aggregate rates alone.

**Status:** DRAFT, not frozen. Model, prompts, seeds, hidden instances, external evaluator, budget and run order must be fixed before any agent efficacy claim. RQ4, context selection benefit and adaptive process depth remain separate untested hypotheses.

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

## Public cognitive-perspective development probe

The [Cognitive Perspectives v0 cases](cognitive-perspectives-v0.md) are a **published, deterministic reference demonstration** of cross-perspective disagreement and a shared checkpoint. Their authored opinions, expected outputs and invented review costs are not hidden from any agent inspecting the repository and **must not** be reused as independent confirmatory evaluation instances. A future empirical study must record actual human/agent effort, source retrieval and errors, including cases where four-lens review adds cost without improving the outcome.

## Public knowledge-history development probe

The [Knowledge & Learning v0 fixture](knowledge-genealogy-v0.md) includes time-cut replay, source supersession, contradiction/retraction, dependent claim invalidation and recovery. Its public expected labels and source texts are written by the experiment authors, so this is a deterministic interface demonstration **not an independent test of an agent's ability to learn, generalize or avoid stale sources**. Any confirmatory evaluation must use separately held-out source histories and score final outcomes rather than confidence or log length; full revision/review overhead belongs in the cost denominator.
