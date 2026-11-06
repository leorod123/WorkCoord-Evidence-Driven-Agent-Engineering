# Context Comparison — First Executed Synthetic Results

**Status:** reproducible public development fixture, **not a real-agent benchmark, causal performance claim, or evidence of token savings**.

**Source:** GitHub Actions [run 42155904485](https://github.com/leorod123/WorkCoord-Evidence-Driven-Agent-Engineering/actions/runs/42155904485), PR #3 candidate `c0b15762af4db58126b42ebf6a409891b762d84c`. The three Python jobs (3.10/3.11/3.13) each passed **77/77 unit tests** and independently ran the same deterministic comparison. Each job uploaded `context-comparison-v0.json` containing the complete case-level records and SHA-256 of all evaluation inputs.

## Public development fixture — four cases

| Arm | Read source-body chars (sum) | Mean decisive source recall | Mean counterevidence recall | Provisional labels matching fixture | Matching labels with *all* declared decisive sources |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full corpus | **6,024** | **100%** | **100%** | **4/4** | **4/4** |
| Local sector | **774** | **25%** | **25%** | **1/4** | **1/4** |
| Dependency expansion | **2,457** | **50%** | **50%** | **3/4** | **2/4** |

The selected total source counts were 44, 5 and 17, respectively, across the four cases. Each arm was constrained by the same 2,400-character maximum **per case**.

## Negative evidence that matters

- **CTX01:** The local strategy retains the current worker trace with less reading; expansion adds avoidable work.
- **CTX02:** Local selection loses the queue/API observations; following two declared dependencies recovers them.
- **CTX03:** When the worker's outgoing dependency link is deleted *for all arms*, the expansion strategy fails to retrieve a decisive API observation even with budget remaining. Full corpus succeeds on the deliberately small fixture.
- **CTX04:** A `focused` expansion does not retrieve the decisive `deep` queue trace. The scripted hypothesis label *matches* the fixture answer but is missing required evidence. This is reported as **unsupported**, not a success.

This is why the stricter source-completeness metric is kept separate from simple provisional label matching.

## Why these figures do **not** prove Intelligence is more effective

The source documents and diagnostic stances are hand-authored; the scoring oracle is **published and not held out**; the common hypothesis reader consumes those annotated stances instead of understanding prose. Source-body characters exclude retrieval computation, tool overhead, repeated reading, tokenization and LLM inference. Four selected examples have no sampling uncertainty or generalization claim.

**Conclusion supported by this run:** the measurement harness makes the trade-off and selective-context failure modes reproducible. **Conclusion not supported:** that real agents will make more correct decisions, use fewer tokens, cost less, or produce better code with the integrated model.

Next: an independently held-out evaluation with real agents, objectively defined evidence access and acceptance, and matched end-to-end budgets. Keep the missing-link and depth-limit counterexamples.
