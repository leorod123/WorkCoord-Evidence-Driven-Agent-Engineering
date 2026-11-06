# Research Method — Small, Falsifiable and Evidence-Aware

**Maturity:** Proposed method. Its effect on agent performance has not been measured.

A useful investigation is a sequence of decisions that can be challenged and reconstructed—not a longer chain-of-thought transcript.

## Investigation record

For each substantive issue, capture:

1. **Question and source identity** — precisely what system behavior is under investigation, and at which revision?
2. **Hypotheses and alternatives** — at least one explanation and a plausible competing explanation.
3. **Falsifiers** — which observation would contradict each explanation?
4. **Evidence map** — source, authority, timestamp/revision, limitations, and dependence between observations.
5. **Next discriminating action** — smallest permitted test that can usefully change the decision.
6. **Decision and scope** — proceed, defer, reject or HOLD; record why and what remains unknown.
7. **Post-action result** — test outcomes, costs, rework, and whether the finding transfers to other cases.

## Proportional depth

- **QUICK:** small, reversible, well-scoped tasks; record a concise decision and a minimal check.
- **STRUCTURED:** nontrivial alternatives, stale context or dependencies; compare evidence and cost.
- **CRITICAL:** high-impact or irreversible proposals; independent review and explicit authorization outside this reference lab.

The escalation rule itself is a research hypothesis. Simpler tasks may get slower under mandatory governance. The benchmark must record those cases.

## Example: duplicate notifications

A repeated notification can result from a retry after a lost acknowledgement, two distinct event producers, or a faulty consumer. A test that only verifies the HTTP response cannot discriminate between them. The investigation should identify the smallest observation that distinguishes causes before asserting a root cause.

The fictional simulator will let users reproduce a visible incident. The future evaluation must withhold instance-specific answers and acceptance tests from the agents, and treat public examples as **training/demo cases**, never unseen confirmation tasks.

## What counts as progress?

An actionable, falsifiable observation, a correctly scoped rejection, or a verified repair can all be useful. Increasing the number of agents, generated documents, task closures, or tokens is not itself a measure of progress.

## Executable research-admission companion (draft)

The [Research Quality v0 reference](research-quality-v0.md) checks eight *generic* scientific-error domains in public fictional packets. It separates source availability from observation time, requires falsifiable alternatives and negative controls for nontrivial tasks, flags late outcome freezes, and prevents a declaration of `TESTED` or `VALIDATED` from being treated as external proof.

It is **advisory and schema-level only**: no source authentication, causal inference, independent scientific review, benchmark or action permission is implemented. A lightweight `QUICK` case has no unnecessary hypothesis-grid/baseline requirement.
