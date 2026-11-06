# Adversarial Verification — V0.2 Scope

**Status:** engineering test plan with executable synthetic probes, not a security certification and not a measured productivity gain.

## Cross-process coordination

Eight separate Python interpreter processes open the same SQLite file and try to claim a single fictional work unit after a barrier. Exactly one should succeed; all others should reject the still-valid exclusive claim. After the contest, the work-generation counter and linked event sequence are checked.

Two additional subprocesses simulate interruption: one exits during a transaction (changes must roll back); another exits immediately after a committed claim (the lease must persist until expiration). These probes cover specific local SQLite semantics only.

## Evidence evaluation boundary

A separate deterministic oracle function computes the expected synthetic notification behavior from logical events and observed deliveries. It generates an HMAC-tagged receipt with evidence ID, **work ID**, revision, evaluation rule, PASS/FAIL and a digest of the evaluated fixture. A valid proof for one work unit must not be reusable to complete a different work unit. The ledger rejects standalone claims of PASS during submission and rechecks the receipt at later state transitions.

**Crucial limitation:** the reference evaluator key is intentionally public in demonstrations and test fixtures. A party with that key, the ledger's interpreter, or raw SQLite write access can forge or alter the underlying records. HMAC shows how a separated evaluator could authenticate a receipt **if** credentials and processes were independently controlled; it does not supply that isolation in this repository.

The synthetic oracle also takes expected logical events as parameters; it does not independently authenticate the origin of those inputs. Production-grade verification would need isolated test infrastructure, external source pinning, independent approval identities and controlled execution authority.

## Focused regression gates added after adversarial review

The first adversarial review demonstrated that the original 32 tests still passed after removing owner/generation or expiry checks. This is a coverage gap, not a claim of a production exploit. The updated negative controls vary **only** the property under test; a dedicated CI mutation script must fail the target tests if those predicates are removed. Documentation: [Gates and mutations](gates-and-mutations.md).

Changing a revision now clears stale verification/approval and provides immediate resubmission under the original still-valid claim. A persistent logical clock rejects backwards ticks. Claim events record issuance and expiry so differing leases do not produce indistinguishable event traces.

## Exit criteria before changing the README's implementation status

1. All D01-D15 tests and targeted negative-control tests remain green; M1/M2 are killed by the mutation check.
2. Cross-process claim and interruption tests pass on both supported Python versions.
3. Untrusted PASS flags, mutated receipts and invalid source revisions are rejected.
4. Documentation explicitly disclaims distributed consistency, protected secrets, independent process isolation and real-agent benchmark results.
5. A separate human review checks the PR's exact commit, scope, privacy and copyright/licensing before merge.

Even when all items pass, the result proves only the tested synthetic properties.
