# Architecture — Context, Investigation, Work and Proof

**Maturity:** Reference design. Implementation details may evolve without changing the central separation of concerns.

## Why this boundary exists

An agent may have the right information but the wrong task, the right task but stale evidence, or a valid proposed fix without authorization to change an environment. These are different failure modes, so they need different contracts.

```mermaid
flowchart LR
  C["Context selection"] --> R["Research"]
  R --> D["Decision"]
  D --> W["Work unit"]
  W --> E["Evidence gate"]
  E --> O["Observed outcome"]
  O -. "feedback with limitations" .-> C
  A["Authorization policy"] -. "separate approval" .-> W
```

## Sectorized context

A candidate [executable fictional navigator](intelligence-walkthrough.md) demonstrates explicit sector/perspective/depth selection, current versus historical source revision, and traceable counterevidence under a character budget. **It is not source authentication, autonomous causal reasoning or execution authority.**


Context is selected along independent dimensions rather than injected as a large undifferentiated history:

| Dimension | Question | Example |
| --- | --- | --- |
| Sector | Which subsystem? | API, queue, worker, notification adapter |
| Perspective | Which engineering lens? | Reliability, causality, performance, security |
| Depth | How far to investigate? | Overview, focused, deep |
| Authority | Is this information reliable? | Draft, historical, observed, validated |
| Dependencies | What else may be affected? | Queue-to-worker delivery contract |
| Source identity | Which version was observed? | Pinned synthetic revision |

A selected context response should expose its source, reason for inclusion, authority, and known gaps. The selector is not permission to execute.

## Cognitive perspectives are not technical sectors

The [Cognitive Perspectives v0 reference](cognitive-perspectives-v0.md) distinguishes *where evidence came from* (API, worker, queue) from *which question should be challenged* (Research, Engineering, Efficiency, Risk). One fictional issue and one proposed remedy receive separately recorded advisory views and a **single revision-bound checkpoint**.

A dissenting risk view cannot be overruled by the number of supporting views; missing, old or causally unavailable source references appear as explicit gaps. A QUICK local check can use fewer perspectives, but additional volunteered objections are never silently ignored. This is a deterministic source-declaration contract, not independent agents, authenticated evidence, work coordination, or new execution authority.

## Research discipline

Record the question, falsifiable hypotheses, observations, contradictory evidence, cost of investigation, and the next discriminating test. For a simple low-risk task, use a lightweight route; for a high-risk dependency-heavy task, require explicit alternatives and independent review.

The agent may return **HOLD** when evidence cannot support a sound conclusion. HOLD is not automatically correct, and will be penalized when the task is resolvable.

## Three separate state dimensions

**Knowledge:** HYPOTHESIS, OBSERVED, TESTED, VALIDATED (transitions need evidence; no confidence-only promotion).

**Work:** READY, CLAIMED, SUBMITTED, VERIFIED, DONE; failure/recovery/blocked states are separate. One exclusive valid owner per unit at a time, with monotonic lease-generation fencing.

**Authority:** READ_ONLY, EDIT_SANDBOX, REVIEW_REQUIRED and explicit approval for a specifically scoped action. Neither a test pass nor a claim is a production authorization.

## Minimum work record

```json
{
  "work_id": "incident-repair-1",
  "status": "CLAIMED",
  "owner": "agent-a",
  "generation": 2,
  "expires_at_tick": 42,
  "source_revision": "fictional-r1",
  "dependencies": [],
  "evidence_ids": [],
  "authorization_scope": "EDIT_SANDBOX"
}
```

The eventual reference implementation will use a caller-provided logical clock for reproducible tests and a small transactional store for claims. This is a reference design, not a distributed transaction coordinator.

## Problem closure is not task completion

The [independent Problem & Decision reference](problem-decision-v0.md) models a **required hierarchy of problem and acceptance criteria** separately from work-unit states. The task may be `DONE` while a required behavior probe is missing; semantic closure remains blocked. An optional unknown node stays visible without automatically forcing a low-risk route into heavyweight governance.

Alternatives are compared at a common assumed time horizon, and the application plan is distinct from choosing the remedy. This is a fictional advisory contract; the code does not independently inspect an operational system or grant a correct outcome.

## Decision and completion gates

1. A unit can be claimed only with an unexpired, uniquely fenced lease.
2. Submission includes a source-bound test artifact. The artifact must be verifiable in a stronger future integration; self-asserted markers are not independent proof.
3. Prerequisite units must be complete before dependent work can be verified.
4. Verification and authorization are independent. Explicit review is needed when the scope requires it.
5. Final completion is idempotent and leaves an inspectable event receipt.

## Limits and non-goals

This project does not implement a hosted service, production runtime, real authorization backend or general-purpose agent scheduler. Initial synthetic components are teaching and test fixtures. Correctness claims remain limited to the exact invariants and test environment exercised.
