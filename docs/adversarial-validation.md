# Adversarial Verification — V0.2 Scope

**Status:** engineering test plan with executable synthetic probes, not a security certification and not a measured productivity gain.

## Cross-process coordination

Eight separate Python interpreter processes open the same SQLite file and try to claim a single fictional work unit after a barrier. Exactly one should succeed; all others should reject the still-valid exclusive claim. After the contest, the work-generation counter and linked event sequence are checked.

Two additional subprocesses simulate interruption: one exits during a transaction (changes must roll back); another exits immediately after a committed claim (the lease must persist until expiration). These probes cover specific local SQLite semantics only.

## Evidence evaluation boundary

A separate deterministic oracle function computes the expected synthetic notification behavior from logical events and observed deliveries. It generates an HMAC-tagged receipt with evidence ID, revision, evaluation rule, PASS/FAIL and a digest of the evaluated fixture. The ledger rejects standalone claims of PASS during submission and rechecks the receipt at later state transitions.

**Crucial limitation:** the reference evaluator key is intentionally public in demonstrations and test fixtures. A party with that key, the ledger's interpreter, or raw SQLite write access can forge or alter the underlying records. HMAC shows how a separated evaluator could authenticate a receipt **if** credentials and processes were independently controlled; it does not supply that isolation in this repository.

The synthetic oracle also takes expected logical events as parameters; it does not independently authenticate the origin of those inputs. Production-grade verification would need isolated test infrastructure, external source pinning, independent approval identities and controlled execution authority.

## Exit criteria before changing the README's implementation status

1. All D01-D15 tests remain green.
2. Cross-process claim and interruption tests pass on both supported Python versions.
3. Untrusted PASS flags, mutated receipts and invalid source revisions are rejected.
4. Documentation explicitly disclaims distributed consistency, protected secrets, independent process isolation and real-agent benchmark results.
5. A separate human review checks the PR's exact commit, scope, privacy and copyright/licensing before merge.

Even when all items pass, the result proves only the tested synthetic properties.
