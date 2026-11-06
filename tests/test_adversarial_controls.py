"""Adversarial negative controls: isolate each fencing and expiry predicate.

An unrelated error must not make a fencing regression test pass.
The expected failure path leaves work state and event count unchanged.
"""
import json
import threading
import tempfile
from pathlib import Path
import unittest

from workcoord_lab.ledger import Ledger, GateError
from workcoord_lab.evaluator import issue_delivery_attestation

KEY = b"synthetic-evidence-fixture-key-not-secret"


class AdversarialControlTests(unittest.TestCase):
    def fixture(self, stage="CLAIMED", ttl=40, authority="EDIT_SANDBOX"):
        db = Ledger(verification_key=KEY)
        self.addCleanup(db.close)
        db.create("work", "r1", authority)
        gen = db.claim("work", "owner", 1, ttl)
        db.record_attested_evidence(issue_delivery_attestation(
            KEY, "proof-1", "work", "r1", ["e", "e"], ["e"],
        ))
        if stage in {"SUBMITTED", "VERIFIED"}:
            db.submit("work", "owner", gen, 2, "proof-1")
        if stage == "VERIFIED":
            db.verify("work", "owner", gen, 3)
        return db, gen

    @staticmethod
    def advance(db, stage, agent, gen, now):
        if stage == "CLAIMED":
            return db.submit("work", agent, gen, now, "proof-1")
        if stage == "SUBMITTED":
            return db.verify("work", agent, gen, now)
        if stage == "VERIFIED":
            return db.complete("work", agent, gen, now)
        raise AssertionError(stage)

    def reject_unchanged(self, db, action):
        before = db.get("work")
        event_count = db.event_count()
        with self.assertRaises(GateError):
            action()
        self.assertEqual(db.get("work"), before)
        self.assertEqual(db.event_count(), event_count)
        self.assertTrue(db.verify_event_chain())

    def test_identity_fencing_isolated(self):
        """All other preconditions valid; only agent identity or generation differs."""
        for stage in ("CLAIMED", "SUBMITTED", "VERIFIED"):
            for variant in ("wrong-owner", "wrong-generation"):
                with self.subTest(stage=stage, variant=variant):
                    db, generation = self.fixture(stage=stage)
                    agent = "impostor" if variant == "wrong-owner" else "owner"
                    gen = generation if variant == "wrong-owner" else generation + 999
                    self.reject_unchanged(
                        db, lambda: self.advance(db, stage, agent, gen, now=4)
                    )

    def test_expiry_fencing_isolated(self):
        """Correct owner/proof/state; reject at tick expires and expires+1."""
        for stage in ("CLAIMED", "SUBMITTED", "VERIFIED"):
            for now in (6, 7):
                with self.subTest(stage=stage, now=now):
                    db, generation = self.fixture(stage=stage, ttl=5)  # expiry=6
                    self.reject_unchanged(
                        db, lambda: self.advance(db, stage, "owner", generation, now)
                    )

    def test_last_valid_tick_is_accepted(self):
        for stage in ("CLAIMED", "SUBMITTED", "VERIFIED"):
            with self.subTest(stage=stage):
                db, gen = self.fixture(stage=stage, ttl=5)
                self.advance(db, stage, "owner", gen, now=5)
                expected = {"CLAIMED": "SUBMITTED", "SUBMITTED": "VERIFIED", "VERIFIED": "DONE"}[stage]
                self.assertEqual(db.get("work")["status"], expected)

    def test_revision_revalidation_for_each_nonterminal_stage(self):
        for stage in ("CLAIMED", "SUBMITTED", "VERIFIED"):
            with self.subTest(stage=stage):
                db, gen = self.fixture(stage=stage, authority="REVIEW_REQUIRED")
                if stage == "VERIFIED":
                    db.approve("work", "reviewer")
                    self.assertEqual(db.get("work")["approved_by"], "reviewer")
                db.change_revision("work", "r2")
                state = db.get("work")
                self.assertEqual(state["status"], "CLAIMED")
                self.assertEqual(state["owner"], "owner")
                self.assertEqual(state["generation"], gen)
                self.assertIsNone(state["evidence_id"])
                self.assertIsNone(state["approved_by"])
                db.record_attested_evidence(issue_delivery_attestation(
                    KEY, "proof-2", "work", "r2", ["e", "e"], ["e"],
                ))
                self.reject_unchanged(db, lambda: db.submit("work", "owner", gen, 4, "proof-1"))
                db.submit("work", "owner", gen, 4, "proof-2")
                db.verify("work", "owner", gen, 5)
                self.reject_unchanged(db, lambda: db.complete("work", "owner", gen, 6))
                db.approve("work", "reviewer-2")
                receipt = db.complete("work", "owner", gen, 6)
                self.assertEqual(len(receipt), 64)
                self.assertEqual(db.get("work")["status"], "DONE")

    def test_rejected_expiry_does_not_advance_clock_or_disable_valid_owner(self):
        db = Ledger(verification_key=KEY)
        self.addCleanup(db.close)
        db.create("work", "r1")
        gen = db.claim("work", "owner", 100, 10)
        db.record_attested_evidence(issue_delivery_attestation(
            KEY, "p", "work", "r1", ["e", "e"], ["e"],
        ))
        db.submit("work", "owner", gen, 109, "p")
        self.reject_unchanged(db, lambda: db.verify("work", "owner", gen, 110))
        self.reject_unchanged(db, lambda: db.verify("work", "owner", gen, 0))
        self.reject_unchanged(db, lambda: db.verify("work", "owner", gen, -1))
        self.assertEqual(db.db.execute("SELECT tick FROM logical_clock WHERE id=1").fetchone()[0], 109)
        db.verify("work", "owner", gen, 109)
        self.assertEqual(db.get("work")["status"], "VERIFIED")

    def test_rejected_actor_cannot_advance_lease_clock(self):
        db, generation = self.fixture(stage="CLAIMED", ttl=110)
        previous = db.db.execute("SELECT tick FROM logical_clock WHERE id=1").fetchone()[0]
        self.reject_unchanged(
            db, lambda: db.submit("work", "impostor", generation, 1000, "proof-1")
        )
        current = db.db.execute("SELECT tick FROM logical_clock WHERE id=1").fetchone()[0]
        self.assertEqual(current, previous)
        db.submit("work", "owner", generation, 2, "proof-1")
        self.assertEqual(db.get("work")["status"], "SUBMITTED")
        self.assertTrue(db.verify_event_chain())

    def test_injected_time_source_ignores_untrusted_actor_now(self):
        tick = [100]
        db = Ledger(time_source=lambda: tick[0])
        self.addCleanup(db.close)
        db.create("work", "r1")
        first = db.claim("work", "owner", now=999999, ttl=10)
        self.assertEqual(first, 1)
        self.assertEqual(db.db.execute("SELECT tick FROM logical_clock WHERE id=1").fetchone()[0], 100)
        self.reject_unchanged(
            db, lambda: db.claim("work", "intruder", now=1000000, ttl=10)
        )
        tick[0] = 110
        self.assertEqual(db.claim("work", "next-owner", now=0, ttl=10), 2)
        self.assertEqual(db.db.execute("SELECT tick FROM logical_clock WHERE id=1").fetchone()[0], 110)
        self.assertTrue(db.verify_event_chain())

    def test_clock_persists_across_sqlite_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "clock.sqlite")
            first = Ledger(path)
            first.create("work", "r1")
            first.claim("work", "owner", 100, 10)
            first.close()
            second = Ledger(path)
            try:
                with self.assertRaises(GateError):
                    second.claim("work", "impostor", 99, 1)
                with self.assertRaises(GateError):
                    second.claim("work", "impostor", 101, 1)
                self.assertEqual(second.claim("work", "new-owner", 110, 10), 2)
                self.assertTrue(second.verify_event_chain())
            finally:
                second.close()

    def test_invalid_clock_types(self):
        db = Ledger()
        self.addCleanup(db.close)
        db.create("work", "r1")
        for now, ttl in ((True, 10), (0, True), (-1, 10), (0, 0), (0, -1)):
            with self.subTest(now=now, ttl=ttl):
                self.reject_unchanged(db, lambda n=now, t=ttl: db.claim("work", "owner", n, t))

    def test_ttl_changes_event_digest_and_relevant_payload(self):
        histories = []
        for ttl in (10, 100):
            db = Ledger()
            db.create("work", "r1", "REVIEW_REQUIRED")
            db.claim("work", "owner", 1, ttl)
            events = [json.loads(r["payload"]) for r in db.db.execute("SELECT payload FROM events ORDER BY seq")]
            hashes = [r["event_hash"] for r in db.db.execute("SELECT event_hash FROM events ORDER BY seq")]
            self.assertEqual(events[0]["authority"], "REVIEW_REQUIRED")
            claim_event = next(e for e in events if e["type"] == "claim")
            clock_events = [e for e in events if e["type"] == "clock_advance"]
            self.assertEqual(len(clock_events), 1)
            self.assertEqual(clock_events[0]["previous_tick"], -1)
            self.assertEqual(clock_events[0]["tick"], 1)
            self.assertEqual(claim_event["issued_at"], 1)
            self.assertEqual(claim_event["expires_at"], 1 + ttl)
            self.assertEqual(claim_event["ttl"], ttl)
            histories.append(hashes)
            db.close()
        self.assertNotEqual(histories[0], histories[1])

    def test_transition_audit_contains_revision_artifact_and_time(self):
        db, gen = self.fixture(stage="CLAIMED")
        db.submit("work", "owner", gen, 2, "proof-1")
        db.verify("work", "owner", gen, 3)
        db.complete("work", "owner", gen, 4)
        rows = [json.loads(x["payload"]) for x in db.db.execute("SELECT payload FROM events ORDER BY seq")]
        by_type = {e["type"]: e for e in rows}
        for name, at in (("submit", 2), ("verify", 3), ("complete", 4)):
            self.assertEqual(by_type[name]["at_tick"], at)
            self.assertEqual(by_type[name]["revision"], "r1")
            self.assertEqual(len(by_type[name]["artifact_sha256"]), 64)
        self.assertEqual(by_type["attested_evidence"]["work_id"], "work")
        self.assertEqual(len(by_type["attested_evidence"]["receipt_mac"]), 64)

    def test_get_does_not_expose_uncommitted_write_on_shared_connection(self):
        db = Ledger()
        self.addCleanup(db.close)
        db.create("work", "r1")
        written = threading.Event()
        release = threading.Event()
        reading = threading.Event()
        result = []
        errors = []

        def writer():
            try:
                with db._transaction():
                    db.db.execute("UPDATE work SET revision='not-yet-committed' WHERE id='work'")
                    written.set()
                    if not release.wait(5):
                        raise AssertionError("test writer timed out")
            except BaseException as exc:
                errors.append(exc)

        def reader():
            reading.set()
            try:
                result.append(db.get("work")["revision"])
            except BaseException as exc:
                errors.append(exc)

        producer = threading.Thread(target=writer)
        observer = threading.Thread(target=reader)
        producer.start()
        self.assertTrue(written.wait(3))
        observer.start()
        try:
            self.assertTrue(reading.wait(3))
            observer.join(timeout=0.1)
            self.assertTrue(observer.is_alive())
        finally:
            release.set()
            producer.join(timeout=3)
            observer.join(timeout=3)
        self.assertFalse(producer.is_alive())
        self.assertFalse(observer.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(result, ["not-yet-committed"])

    def test_revision_noop_and_ready_case(self):
        db = Ledger()
        self.addCleanup(db.close)
        db.create("work", "r1")
        before = db.event_count()
        db.change_revision("work", "r1")
        self.assertEqual(before, db.event_count())
        db.change_revision("work", "r2")
        self.assertEqual(db.get("work")["status"], "READY")
        self.assertIsNone(db.get("work")["owner"])


if __name__ == "__main__":
    unittest.main()
