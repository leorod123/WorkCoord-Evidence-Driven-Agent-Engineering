# Harbor / Terminal-Bench 2.0 pilot v0 — freeze-first external evaluation protocol

**Status: DRAFT_UNFROZEN.** No task list has been selected, Harbor executed, provider key loaded, Codex invoked, result collected or experimental advantage established. This is a **new evaluation contract**, not an agent adapter or another simulator.

The [machine-readable draft](../evals/harbor-pilot-protocol-v0.json) is deliberately incomplete. The offline checker refuses to call it execution-ready until immutable sources, precise task IDs, common model, adapter implementations, budgets and required human publication review are recorded.

## Why an existing external environment

Use the official [Harbor evaluation harness](https://github.com/harbor-framework/harbor), and the public [Terminal-Bench 2.0](https://github.com/harbor-framework/docs/blob/main/examples/terminal-bench.mdx) task/verifier family. It is a better falsification target than more fictional WorkCoord examples: benchmark tasks and containerized verification are outside the project-specific rules. It is **not necessarily a perfectly independent or uncontaminated evaluator**; evaluate task quality and possible training leakage before any inference.

Harbor documents a built-in [Codex agent adapter](https://github.com/harbor-framework/harbor/blob/main/src/harbor/agents/installed/codex.py). However, **a Codex connector available inside ChatGPT/another app does not imply its API credentials are automatically available in Harbor's external Docker process**. Provider access, a supported model and Docker/environment ownership require separate validation. Do not paste, echo, commit, print or pass raw authentication credentials via CLI arguments, test fixtures, GitHub issues, or recorded traces.

## The three planned arms (package comparison)

| Arm | Agents | Controls |
| --- | ---: | --- |
| **A — strong single agent** | 1 | Same base model, task and tools; ordinary problem solving |
| **B — basic coordination** | 2 | Two-agent workflow with simple hand-off, no WorkCoord research/lineage/fencing bundle |
| **C — WorkCoord bundle** | 2 | Same base model, tools and task set, with the integrated context/research/knowledge/coordination policies |

The **A-vs-B** contrast includes the change from one to two agents. The **B-vs-C** contrast estimates the **package effect**, *not* which specific module caused it. Attribution to context selection, scientific admission, leases or cognitive review would require later predeclared ablations. The benchmark measures terminal-task capability; it may not exercise every WorkCoord governance property equally.

The external evaluator MUST be the same for all arms. Match model version, tool/sandbox access, network policy, scenario start state, time and token ceilings, inference prices, verification rules, task IDs and allowed observation schedules. If the official task needs GPU/network access that cannot be made equivalent, exclude it **before** scoring and record that reason.

## The required frozen manifest

Before paying for a single model trial, replace the draft's NULLs with verified values and set the protocol status to `FROZEN`. It will fail closed unless:

- Harbor commit and dataset commit are each immutable **40-character Git SHAs**, task IDs have been inspected and explicitly listed in **nonoverlapping** `smoke`, `exploratory` and `confirmatory` sets, and `task_manifest_sha256` equals the canonical fingerprint of those commits and exact task sets.
- No wildcard task selection is used. The resolved task IDs must match the **intended set and count** *before* invocation. There has been a documented Harbor task-name filtering issue in which an unmatched glob could select all available tasks: [Harbor issue #2246](https://github.com/harbor-framework/harbor/issues/2246). Treat any zero-match, mismatch, or unexpectedly large expansion as a **hard stop**, never a paid fallback.
- The three implementation/adapter commits and a **single common base model ID** are pinned. Adapter differences must be logged; C must not gain extra tool/secret access.
- Per-trial and total USD spending caps, attempted task counts and shared time budgets are fixed. Concurrency starts at 1 for reproducibility.
- A **human** has reviewed authorship/confidentiality and chosen a license. A clean regex scanner does not satisfy this gate. Freeze does *not* independently authorize a public release or merge.

The fingerprint is a SHA-256 consistency check over *public declared fields*, **not** a digital signature, trusted timestamp or proof of benchmark secrecy. Seal and timestamp the intended pre-registration independently before observing confirmatory outcomes.

### Preparatory commands — environment discovery only

On a computer or a trusted Harbor-compatible runtime with Docker:

```bash
uv tool install harbor
harbor --version
docker info
harbor datasets list
harbor datasets download terminal-bench@2.0
harbor run --help
```

Record the exact checked-out Harbor commit, dataset revision and sandbox capabilities; do not assume an installed package's version label fixes every dependency or dataset artifact. The current Harbor CLI documents `--dataset`, `--task-name`, `--agent`, `--model`, `--n-concurrent` and `--dry-run`; verify actual flags against the **pinned installed version**, not this prose. See the [CLI reference](https://github.com/harbor-framework/docs/blob/main/cli/run.mdx).

**No `harbor run` command is provided for a paid agent here:** there are intentionally no verified task IDs, model, agent adapters or budget authorization. Once frozen, first perform a **no-model environment smoke test** on smoke-only tasks, verify exact task counts, then trial one real task at a time with a hard budget cap. Do not inspect oracle solutions or confirmatory answers while designing agents.

## Scoring policy (the WorkCoord gate does not grade itself)

An *independent* Harbor verifier provides `verifier_status`: `PASS`, `FAIL`, `NOT_RUN` or `HARNESS_ERROR`. Agent declarations such as `DONE` and `HOLD` are recorded **separately**. Only `PASS` contributes to externally verified successes; a blocked invalid attempt is never silently recoded as a valid repair.

Primary metric, with a **fixed intention-to-treat denominator**:

\[
\mathrm{ValidSuccessRate}_{arm} =
\frac{\#\mathrm{externally\ verified\ PASS}}
{\#\mathrm{all\ frozen\ assigned\ task\!-\!attempts}}
\]

Failures, HOLDs, timeouts, missing rows and harness errors are *not* omitted from this primary denominator. Independently adjudicated infrastructure faults may later be shown in an explicitly **paired sensitivity analysis**, excluding the affected task from **every** arm equally and reporting the changed denominator. Never selectively discard just C's errors.

Cost per valid result is **the cost of every assigned attempt**, including failures and governance overhead, divided by the count of externally verified PASS outcomes. If any assigned cost is missing, label the cost estimate **unavailable** rather than substituting zero. With zero successes, cost per success is **undefined** (JSON `null`, not infinity or zero).

Report at least external PASS rate, total cost, cost per valid outcome, latency, input/output tokens, candidate repairs, falsely declared successes, gate-blocked invalid attempts, recovery/rework and justified versus avoidable HOLDs. Counts of false completion and avoidable HOLD require **independent adjudication**; if a verdict has not been reviewed, report `null`, never `0`. Always publish per-task outcomes and uncertainty with the aggregation, when confidentiality permits.

## Normalized safe result boundary

`src/workcoord_lab/harbor_pilot.py` provides **offline only** validation and aggregation. It deliberately does **not** scrape Harbor output, spawn agents, call Codex, authenticate evaluator data, or certify a result. A future **separate** adapter must map Harbor `trial_result.json` and independent reviewer decisions into the restricted normalized fields, including:

- `task_id`, `arm`, `attempt`, `verifier_status`, `agent_end_status`;
- `cost_usd`, `wall_seconds`, `input_tokens`, `output_tokens` (explicit `null` when not measured);
- `independent_adjudication`, `invalid_completion_attempts`, `gate_blocked_invalid_attempts`, `avoidable_holds` (all three `null` when independent review is missing).

Unexpected fields, raw trajectories, prompts, file contents, tool stdout, provider URLs or credentials are **not accepted** into this normalized dataset. The public normalization checker is an allowlist, not a comprehensive sensitive-data detector; human review of any future emitted artifacts is mandatory.

The synthetic unittest includes a **counterexample in which arm C is worse than B** on both externally scored success rate and cost per valid outcome. Those numbers are **unit-test arithmetic**, not a claim about Harbor, Codex or WorkCoord agents.

### Offline checks (no Docker, network or model credits)

```bash
PYTHONPATH=src python -m workcoord_lab.harbor_pilot
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/verify_harbor_protocol_mutations.py
```

The first command must display `DRAFT_UNFROZEN` and `ready_for_model_execution: false`. CI checks schema, scoring and deliberately falsified algorithms, but **never launches a paid agent**.

## Pre-publication evidence and open gates

At the time of drafting, [PR #12](https://github.com/leorod123/WorkCoord-Evidence-Driven-Agent-Engineering/pull/12) passed the [public Git-history hygiene workflow](https://github.com/leorod123/WorkCoord-Evidence-Driven-Agent-Engineering/actions/runs/42236780965) at commit `d6fa41fb5d848a0258881f7a8f2e672bb39c64b1`. It inspected **212 reachable blobs** without matching the scanner's credential patterns, skipped no oversized blob, and found **no LICENSE**. Its own report correctly has `publication_authorized=false`. This is a limited *automated observation*, not a rights audit or confidentiality approval.

**Owner/human requirements still unresolved:** provenance and originality, semantic confidentiality, full remote Git history, PR discussions and CI artifact review, license selection, branch protection/required checks, confirmation of environment ownership and real Codex billing limits, and explicit authorization of any release/merge.

The next acceptable deliverable is a **reviewed and frozen protocol plus a local non-model Harbor smoke test**, not a speculative benchmark table. Only then should A/B/C agent adapters and small exploratory external trials be considered.
