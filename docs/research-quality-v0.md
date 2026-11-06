# Research Quality v0 — Evidence Admission, Not Scientific Truth

> **Experimental, public fictional development fixture.** The evaluator below checks research-packet completeness and visible contradictions. It does **not** authenticate source provenance, independently test a causal claim, call a language model, or authorize work.

## Why this is a separate capability

A perfectly executed test suite can still support a poor conclusion if a study used a later observation as though it were available earlier, judged only on a proxy, or chose its hypothesis after seeing the outcome.

This module operates **before a claim is promoted**. It asks whether a *proposed investigation* has enough explicit safeguards to proceed. It returns an advisory diagnostic record. A syntactically complete packet cannot become a `VALIDATED` scientific result by passing this check.

## Depth proportional to the problem

| Mode | What must be present | What it cannot do |
| --- | --- | --- |
| `QUICK` | Specific question, pinned source identity, one checkable observation and next check | Require a heavy study just to fix a simple local issue |
| `STRUCTURED` | Competing falsifiable explanations, baseline, negative control, measure-target fit, current usable evidence and timestamps | Treat a well-formed experiment as a proven causal outcome |
| `CRITICAL` | Structured checks **plus** multiple declared origin groups and review reference | Treat an origin label or reviewer reference as actual independent verification |

The `CRITICAL` mode always returns `REQUIRES_EXTERNAL_REVIEW` when all local checks pass. No mode grants execution authority.

## Eight generic failure domains

| Domain | Example of a rejection |
| --- | --- |
| `source_integrity` | The current explanation relies only on an older revision |
| `time_of_knowledge` | A source was read after the claimed decision time |
| `chronology` | An observation was supposedly available before it existed |
| `outcome_peeking` | The acceptance criterion was frozen after outcome observation |
| `metric_fit` | A metric is declared unrelated to the underlying research target |
| `alternative_tests` | No baseline, falsifier, or negative control |
| `corroboration` | Two apparent supporting records are derived from the same origin |
| `claim_boundary` | A self-declared result claims `TESTED` or `VALIDATED` without external checks |

**Important:** `origin_group`, revisions, authorizations and timestamps are plain fields in a fictional JSON packet. The module checks their internal consistency, not their authenticity. `DESIGN_ADMISSIBLE` is **not** `RESEARCH_CORRECT`.

## Fourteen development cases

The [public catalog](../examples/research-quality-cases-v0.json) contains a simple valid local investigation, a structured falsifiable plan, a valid pre-outcome lock, an externally unreviewed critical study, plus adversarial cases for late freezes, post-decision observations, duplicated provenance groups, proxy validity, absent controls, stale notes, and unsupported promotion.

Expected outcomes are declared alongside each public case. They are **not held out** and cannot be scored as a model benchmark. In the current case set, **3** designs are admissible, **10** require further research and **1** requires external review. These numbers measure test-fixture classification only, not real-world method usefulness.

## Reproduce (Python 3.10+; standard library)

From the repository root:

```bash
PYTHONPATH=src python -m workcoord_lab.research_quality_suite --output artifacts/research-quality-v0.json
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/verify_research_mutations.py
```

The suite produces a deterministic JSON receipt with **catalog SHA-256**, per-case diagnostics, and a marker that empirical efficacy has **not** been measured. Continuous integration runs the same tests on Python 3.10, 3.11 and 3.13. Deliberate mutations M17–M24 must each be caught by an independently named negative-control assertion.

The direct CLI also supports inspecting one JSON packet:

```bash
PYTHONPATH=src python -m workcoord_lab.research_quality my-packet.json
```

## Explicitly not established

The positive result is **research-admission readiness**, not reproducibility of external source bytes, signed source generation, causal identification, statistical significance, calibrated risk, independent-review completion, cost effectiveness or deployability. A valid negative result is a useful finding, but the evaluator cannot determine whether further investigation is economically justified. Those decisions require an external assessment.

The examples use a fictional notification system and have been authored independently for public demonstration. The implementation is a deliberately small stdlib-only reference check. No new service, scheduler, model, work coordinator or persistent database is introduced.

## Next step: a distinct Problem & Decision reference

Introduce a self-contained, independent **problem-node and alternatives** demonstration with a result that is *technically green but semantically incomplete*. The research-admission evaluator should remain separate from problem closure, work ownership and action authorization. That gives an independently falsifiable interface before integrating cognitive perspectives or agent experiments.
