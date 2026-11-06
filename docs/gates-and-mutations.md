# Adversarial Regression Tests — Gates and Mutation Checks

**Status:** synthetic, deterministic, non-production. These tests isolate individual preconditions instead of relying on coincidental validation failures.

## M1: identity fencing

At each otherwise-valid transition (CLAIMED to SUBMITTED, SUBMITTED to VERIFIED, VERIFIED to DONE), a different owner or a wrong fencing generation must be rejected. The existing source-bound evaluator receipt, status, and time remain valid, so rejection tests the identity predicate rather than an unrelated requirement. State and event count must remain unchanged.

## M2: expiry fencing

The same three transitions must reject at `expires` and at `expires+1` even for the correct owner, revision, generation and evidence. At `expires-1` the otherwise-valid transition succeeds. Rejections do not change work/event state; the ledger-local clock may advance.

The CI mutation step copies fictional source to temporary folders, removes only the relevant predicate, and requires the expected negative-control test to fail. A syntax/import error does not count as a killed mutation.

## Revision invalidation

Changing an unfinished work unit from revision R1 to R2 clears its stale proof and previous reviewer approval; a current holder may re-submit an R2 proof using the same lease/generation, if the lease is still valid. A completed unit remains immutable. This transition is an administrative synthetic signal without any identity/authentication authority.

## Ledger-local clock

All claim, submit, verify and complete requests use nonnegative integer logical ticks. A durable ledger-local clock rejects a backwards tick across SQLite connections. A rejected attempted transition can still advance logical time (recorded separately); work state and event sequence remain unchanged. The clock is caller-supplied and **not independently trustworthy**, not synchronized across hosts, and not a production lease clock.

## Audit receipts

State-change events record authority on creation, lease issuance/expiration and TTL on claim, revision and artifact digests on evidence-dependent transitions, and reviewer where relevant. The hash chain is not a complete event-sourced replay system, not authenticated against raw database mutation, and not a guarantee that a real revision or runtime test was independently observed.

A hypothetical failing mutation proves the targeted negative test is capable of detecting that control being removed. It does not establish security in a hostile environment or improvement in AI reasoning.
