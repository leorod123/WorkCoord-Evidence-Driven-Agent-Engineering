# Cognitive Perspectives v0 — Executed Synthetic Development Results

**Status: synthetic, public and fully reproducible. NOT a multi-agent benchmark or externally verified decision-quality improvement.**

## Exact verification

- Candidate head: `080effef046a8f32a458127847a51a062e0962dc`.
- [GitHub Actions run 42163822388](https://github.com/leorod123/WorkCoord-Evidence-Driven-Agent-Engineering/actions/runs/42163822388): **PASS** in Python **3.10, 3.11 and 3.13**.
- Each Python version ran **206/206 deterministic unit tests** successfully.
- Each job detected the named negative tests for **53/53 deliberate mutations M1–M53**; no crash or import error counted as a mutation kill.
- All **19/19 fictional public development cases** matched their pre-authored expected classifications.
- A deterministic JSON receipt was archived for each Python version as `cognitive-perspectives-py-3.10`, `-3.11` and `-3.13`. Each receipt contains the catalog SHA-256 and case-level checkpoint hashes.

## Public toy-case classifications

| Advisory output | Cases | Meaning inside this toy contract |
| --- | ---: | --- |
| `ADVISORY_READY` | 5 | Locally complete, unchallenged *declared* review, no action authority |
| `HOLD_CONTRADICTION` | 2 | A challenge and support coexist; no voting it away |
| `HOLD_UNRESOLVED_UNCERTAINTY` | 2 | At least one relevant review remains uncertain |
| `HOLD_MISSING_PERSPECTIVE` | 2 | A required lens was not supplied |
| `HOLD_STALE_PERSPECTIVE` | 1 | At least one review is pinned to a different source revision |
| `HOLD_SOURCE_GAP` | 5 | A cited source is missing, old, causally unavailable or uncited |
| `HOLD_UNRESOLVED_CHALLENGE` | 1 | Opposition without a supporting counterpart is unresolved |
| `REQUIRES_EXTERNAL_REVIEW` | 1 | Critical consensus is still only a request for review |
| **Total** | **19** | **All publicly authored and not held out** |

These counts describe the deliberately constructed fixture, **not** frequency estimates for real teams or models.

## Selected adversarial observations

**CP02 — three supporters against one risk challenge.** The checkpoint retains all four stances and the additional downstream delivery record. The result is `HOLD_CONTRADICTION`, not majority-based approval. The presence of the record does not establish which diagnosis is true.

**CP08 versus CP01 — proportional overhead.** The self-declared low-risk one-lens engineering case reports **1 review-effort unit** versus **8 declared units** for the four-lens example. These units were put into the input fixture. They are **not measured time, tokens, labor cost or productivity**.

**CP09 — extra opposition on a simple task.** Although a QUICK case requires only Engineering, a voluntarily supplied Risk challenge is still evaluated and blocks consensus. Optional review does not mean that a recorded objection may be suppressed.

**CP05–CP06, CP10 and CP16 — causal and revision consistency.** Stale review/source revisions and source or review timestamps after their respective cutoffs produce explicit HOLD results. The clocks and revisions are claimed by the synthetic fixture rather than independently checked.

**CP07 — four supporters cannot authorize critical work.** The output remains `REQUIRES_EXTERNAL_REVIEW`. All cases return `execution_authority=NONE`, `knowledge_promotion=NOT_GRANTED` and `work_ownership=NOT_ASSIGNED`.

**CP11 — not four independent witnesses.** The fixture deliberately makes multiple sources share an origin label; the result never claims authenticated independence. A lens is a *perspective* and can cite the very same evidence as another lens.

**Changed cited source text invalidates the checkpoint.** A test modifies a referenced fictional source body without changing its length; the source digest and checkpoint hash both change. The digest binds input bytes, not their truth or external origin.

## Interpretation

This successful execution supports a narrow claim: **the reference data contract and its regression tests preserve disclosed disagreements, revision and availability gaps, and non-authority boundaries** for these specifically authored cases.

It does **not** prove that the four lenses are independent, that a language model can generate them reliably, that a source is authentic, that the resulting recommendation is causally correct, or that this method has a positive net return over a simpler workflow. It also does not validate external project acceptance or grant any action privilege.

Next: a separate **Knowledge & Learning v0** reference that tests source supersession, negative evidence, conclusion invalidation and reconstructible lineage. A real-agent study requires held-out instances, external grading and full cost measurement.
