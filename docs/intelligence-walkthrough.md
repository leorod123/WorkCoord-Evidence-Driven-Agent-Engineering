# Intelligence Walkthrough — Source, Perspective, Depth and Counterevidence

> **Status:** deterministic **synthetic** reference fixture, not a live agent, a validated diagnosis, a production source registry or a measured efficiency improvement.

## Research question

Can a bounded, sectorized context interface make a revision of an investigation **traceable** when an old validated note is challenged by newer observations from another subsystem, without silently discarding the conflicting evidence?

The fixture describes a fictional SaaS notification incident. It is independent of any private repository or operational system.

## Execute

From the repo root using Python 3.10+:

\`\`\`bash
PYTHONPATH=src python -m workcoord_lab.intelligence_demo
PYTHONPATH=src python -m unittest discover -s tests -v
\`\`\`

The demo prints machine-readable JSON with a source manifest, three selection passes, provisional hypothesis scores, contradictions, explicit gaps and measured reading characters.

## Navigation sequence

| Pass | Selection request | Expected behavior |
| --- | --- | --- |
| 1. Worker | sector \`worker\`; perspective \`reliability\`; depth \`overview\` | A *historically validated* worker guide suggests producer duplication. Its prior-revision status is explicit. |
| 2. Queue | follow declared dependency; \`queue/reliability/focused\` | A *current observed* acknowledgement-timeout trace contradicts producer duplication and supports retry-related duplication. Old and new evidence are both retained. |
| 3. API | cross-check \`api/reliability/focused\` | A current single-producer-event observation further contradicts the original hypothesis. The result remains provisional and requests independent validation. |

The fixture's human-authored \`signals\` provide an intentionally transparent **illustrative ranking heuristic**. The code **does not infer diagnosis from natural language**, authenticate the observations, or prove causal correctness.

The walkthrough is not an agent benchmark. The expected hypothesis shift is built into the toy data, and its success cannot support claims about real-world reasoning quality.

## Public contract

\`ContextNavigator(documents, current_revision, issue_tags, max_chars)\` accepts typed synthetic source annotations and retains independent axes:

- **Sector:** API, queue or worker; expanding to a new sector requires an explicit request.
- **Perspective:** e.g. reliability, performance, security; changing it changes eligible sources.
- **Depth:** overview, focused, deep; finer sources remain unavailable until requested.
- **Revision:** old validated documentation remains readable **as historical context**, never promoted to validation of the current revision.
- **Maturity:** draft, historical, observed, validated; observations remain usable to **investigate**, never granted completion authority.
- **Dependencies and contradictions:** linked sectors are surfaced as suggestions. Supporting and contradicting references remain visible in the final assessment.
- **Cost and gaps:** real \`len(body)\` character counts are tracked with a hard cumulative cap; over-budget documents and potential counterevidence are explicitly reported.

A status of \`PROVISIONAL_INVESTIGATION_ONLY\` is invariant. Neither the selector nor its assessment can authorize a production action or mark a diagnosis as externally proven.

## Negative cases

The tests cover revision conflicts, perspective/depth changes, explicit dependency expansion, counterevidence under budget pressure, lack of source coverage, deterministic order, no double-counting and refusal to promote observed notes to current validated authority.

## Limits and next experiment

All metadata, including maturity and provenance, is authored by the fixture itself. Current versus stale is a string equality check, **not** a VCS-verified source identity. Reading-character counts are not token counts or LLM cost measurements; small context is not automatically better context. The ranking weights are not calibrated or an independent grader.

Next, measure **evidence recall** and quality of resulting decisions under the same independent evaluator for broad versus selective context. Include a case where selection misses an essential distant dependency or suppresses critical counterevidence. That comparison requires real agents and frozen instances; it has **not** been run.

See the [experimental design](experimental-design.md) and [architecture](architecture.md).
