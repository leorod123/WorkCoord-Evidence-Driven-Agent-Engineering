"""Deterministic D01-D15 acceptance probes (not real-agent efficacy tests)."""
import os
import tempfile
import threading
import unittest

from workcoord_lab.ledger import Ledger, GateError
from workcoord_lab.evaluator import issue_delivery_attestation
from workcoord_lab.policies import FakeSandbox, discover, score_decision
from workcoord_lab.simulator import deliver, semantic_oracle


TEST_KEY = b"fictional-evaluator-test-key-32-bytes"


class InvariantTests(unittest.TestCase):
    def setUp(self):
        self.db = Ledger(verification_key=TEST_KEY)
        self.db.create("one", "rev-a")

    def tearDown(self):
        self.db.close()

    def _proof(self, work_id="one", identity="test-a"):
        self.db.record_attested_evidence(issue_delivery_attestation(
            TEST_KEY, identity, "rev-a", ["event-1", "event-1"], ["event-1"],
        ))
        return identity

    def _verified(self, work_id="one", owner="a"):
        generation = self.db.claim(work_id, owner, 1, 50)
        key = self._proof(work_id, identity=f"proof-{work_id}")
        self.db.submit(work_id, owner, generation, 2, key)
        self.db.verify(work_id, owner, generation, 3)
        return generation

    def test_D01_concurrent_claim(self):
        results, lock = [], threading.Lock()
        def attempt(n):
            try:
                self.db.claim("one", f"agent-{n}", 1, 50)
                value = "yes"
            except GateError:
                value = "no"
            with lock:
                results.append(value)
        pool = [threading.Thread(target=attempt, args=(i,)) for i in range(20)]
        for t in pool:
            t.start()
        for t in pool:
            t.join()
        self.assertEqual(results.count("yes"), 1)

    def test_D02_lease_expiry_and_fence(self):
        first = self.db.claim("one", "a", 1, 2)
        second = self.db.claim("one", "b", 3, 20)
        self.assertEqual(second, first + 1)
        with self.assertRaises(GateError):
            self.db.submit("one", "a", first, 4, "missing")

    def test_D03_old_owner_cannot_complete(self):
        old = self.db.claim("one", "a", 1, 2)
        self.db.claim("one", "b", 3, 20)
        with self.assertRaises(GateError):
            self.db.complete("one", "a", old, 4)

    def test_D04_cycle_rejected(self):
        self.db.create("two", "rev-a")
        self.db.add_dependency("one", "two")
        with self.assertRaises(GateError):
            self.db.add_dependency("two", "one")
        self.assertEqual(self.db.get("two")["deps"], "[]")

    def test_D05_changed_revision_invalidates_proof(self):
        generation = self._verified()
        self.db.change_revision("one", "rev-b")
        with self.assertRaises(GateError):
            self.db.complete("one", "a", generation, 5)

    def test_D06_completion_replay_idempotent(self):
        generation = self._verified()
        receipt = self.db.complete("one", "a", generation, 5)
        count = self.db.event_count()
        self.assertEqual(self.db.complete("one", "a", generation, 6), receipt)
        self.assertEqual(self.db.event_count(), count)

    def test_D07_persistent_reopen_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "lab.sqlite")
            one = Ledger(path)
            one.create("p", "rev-a")
            gen = one.claim("p", "a", 1, 20)
            one.close()
            two = Ledger(path)
            self.assertEqual(two.get("p")["generation"], gen)
            with self.assertRaises(GateError):
                two.claim("p", "b", 2, 10)
            self.assertTrue(two.verify_event_chain())
            two.close()

    def test_D08_unpermitted_action_denied(self):
        sandbox = FakeSandbox({"src/app.py": "pass"})
        with self.assertRaises(GateError):
            sandbox.access("deploy", "src/app.py")
        self.assertEqual(len(sandbox.denials), 1)

    def test_D09_confident_hypothesis_not_proof(self):
        gen = self.db.claim("one", "a", 1, 20)
        self.db.record_evidence("hyp", "rev-a", "hypothesis", True, "confident")
        with self.assertRaises(GateError):
            self.db.submit("one", "a", gen, 2, "hyp")

    def test_D10_historical_doc_excluded(self):
        documents = [
            {"id":"old","title":"notification","body":"old guidance","authority":"historical"},
            {"id":"new","title":"notification","body":"observed current","authority":"validated"},
        ]
        result = discover(documents, "notification")
        self.assertEqual(result["selected"], ["new"])
        self.assertEqual(result["excluded_with_reason"][0]["id"], "old")

    def test_D11_correlated_evidence(self):
        self.db.record_evidence("a", "rev-a", "observation", independent_group="one-log")
        self.db.record_evidence("b", "rev-a", "observation", independent_group="one-log")
        self.db.record_evidence("c", "rev-a", "observation", independent_group="second-log")
        self.assertFalse(self.db.independent_evidence(["a","b"]))
        self.assertTrue(self.db.independent_evidence(["a","c"]))

    def test_D12_evaluator_excluded_in_virtual_interface(self):
        sandbox = FakeSandbox({"src/app.py":"pass","oracle/answers.json":"demo-hidden"})
        with self.assertRaises(GateError):
            sandbox.access("read", "oracle/answers.json")
        self.assertEqual(sandbox.denials[0]["action"], "read")

    def test_D13_duplicate_oracle(self):
        events = ["event-1", "event-1"]
        self.assertFalse(semantic_oracle(events, deliver(events)))
        self.assertTrue(semantic_oracle(events, deliver(events, idempotent=True)))

    def test_D14_unnecessary_abstention(self):
        self.assertEqual(score_decision(True, "HOLD"), "INCOMPLETE")
        self.assertEqual(score_decision(False, "HOLD"), "VALID_ABSTENTION")

    def test_D15_no_artifact_no_submission(self):
        gen = self.db.claim("one", "a", 1, 20)
        self.db.record_evidence("empty", "rev-a", "test", passed=True)
        with self.assertRaises(GateError):
            self.db.submit("one", "a", gen, 2, "empty")

    def test_explicit_review_gate(self):
        self.db.create("two", "rev-a", "REVIEW_REQUIRED")
        gen = self._verified("two")
        with self.assertRaises(GateError):
            self.db.complete("two", "a", gen, 4)
        self.db.approve("two", "independent-reviewer")
        self.assertTrue(self.db.complete("two", "a", gen, 5))

    def test_dependencies_block_early_verification(self):
        self.db.create("two", "rev-a")
        self.db.add_dependency("two", "one")
        gen = self.db.claim("two", "a", 1, 20)
        proof = self._proof("two", "test-two")
        self.db.submit("two", "a", gen, 2, proof)
        with self.assertRaises(GateError):
            self.db.verify("two", "a", gen, 3)


if __name__ == "__main__":
    unittest.main()
