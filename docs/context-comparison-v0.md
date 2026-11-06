# Three-Arm Retrieval Comparison v0

> **PUBLIC SYNTHETIC DEVELOPMENT EVALUATION — NOT A HELD-OUT AGENT BENCHMARK.**

## Question

When does selective context save reading while retaining decisive evidence, and when do missing dependencies or shallow selection cause it to fail?

The experiment uses **the same fictional FlowDesk source pool, evaluator, heuristic, and 2,400-character cap for all three strategies within a case**.

| Strategy | What it reads | Structural trade-off |
| --- | --- | --- |
| \`full_corpus\` | Every document, including off-topic ones, if the **entire pool** fits | Highest source-body reading cost; reference source availability |
| \`local_sector\` | Only the starting sector/perspective/depth | Fewer characters; possible missing counterevidence |
| \`dependency_expand\` | Identical start, followed by at most two **declared** dependency links at \`focused\` depth | Recovers linked evidence; misses unlinked or too-deep sources |

The evaluator is a **published development oracle**, stored in \`evals/context_oracle_v0.json\`; it is not secret or hidden from a future agent reading this repository. Source-selection functions do **not** receive gold source IDs or the expected hypothesis.

## Four deliberately nonrepresentative cases

| Case | Setup | What should be exposed |
| --- | --- | --- |
| CTX01 | Current worker observation is available at the starting focused depth | Local retrieval can retain decisive evidence with less reading |
| CTX02 | Stale worker guide conflicts with linked queue and API observations | Dependency expansion can recover contrary evidence |
| CTX03 | Worker dependency link is missing from **all arms' case inputs** | Both selective arms can miss essential API evidence |
| CTX04 | Required queue trace is at \`deep\` depth, while expansion stops at \`focused\` | A plausible diagnosis can lack decisive supporting proof |

## Independent-of-selection public grading contract

Every strategy receives the **same deterministic, human-annotated hypothesis reader**. This is not an LLM and cannot infer natural-language causal relations. The reader uses the existing synthetic \`signals\` labels, including old/current maturity weighting.

After selection, a common public rubric grades **decisive evidence recall**, **counterevidence recall**, **whether the provisional label matches a fixture label**, and a stricter **evidence-supported provisional label** (matching label *and* all required sources read). A plausible hypothesis with missing required sources is reported separately rather than treated as a validated outcome.

Every case records source IDs, navigation steps, explicit gaps, unique source-body characters and read count. A common full-corpus budget too small for the complete pool causes an explicit error instead of silent truncation.

**These metrics do not measure real agent reasoning, repair correctness, token savings, time, API cost, or production reliability.** The grading data, source stances and cases are hand-designed public fixtures, so this exercise is an instrumentation and failure-demonstration test.

## Reproduce

Python 3.10+ and standard library, in repository root:

\`\`\`bash
PYTHONPATH=src python -m workcoord_lab.context_comparison --output artifacts/context-comparison-v0.json
PYTHONPATH=src python -m unittest discover -s tests -v
\`\`\`

GitHub Actions runs the three arms on Python 3.10, 3.11, 3.13 and uploads the deterministic JSON evaluation receipt. It includes SHA-256 of the input fixture, case manifest, and rubric, without a dynamic timestamp.

Input files: [cases](../evals/context_cases_v0.json), [development oracle](../evals/context_oracle_v0.json), [source corpus](../examples/flowdesk-context.json).

## Interpretation limits and next experiment

Character counts cover **unique selected source bodies only**, not metadata, retrieval compute, reasoning calls, additional tool actions, or model tokens. A reduced number of source characters does **not** prove reduced overall cost. The same public hand-annotated heuristic helps each strategy and may be systematically biased. There is no statistical significance calculation or claim of generalization from four designed cases.

The follow-up scientific study needs held-out source sets, a truly independent external evaluator, shared real-agent prompts/models/permissions and full accounting of read/compute/token/time cost. It must preserve hard negative examples where narrowing the context suppresses the correct answer. No such study is claimed here.
