"""Tests for synthetic evaluator-scored evidence and tamper detection."""
import copy
import unittest
from workcoord_lab.ledger import GateError, Ledger
from workcoord_lab.evaluator import issue_delivery_attestation, verify_attestation


KEY = b"public-fictional-attestation-only-key-v1"
OTHER_KEY = b"wrong-fictional-attestation-only-key-v1"


class AttestationTests(unittest.TestCase):
    def setUp(self):
        self.db = Ledger(verification_key=KEY)
        self.db.create("one", "r1")
        self.generation = self.db.claim("one", "investigator", 1, 30)

    def tearDown(self):
        self.db.close()

    def receipt(self, evidence_id="one-proof", revision="r1", deliveries=None):
        if deliveries is None:
            deliveries = ["logical-event"]
        return issue_delivery_attestation(KEY, evidence_id, revision,
                                          ["logical-event", "logical-event"], deliveries)

    def test_evaluator_accepts_semantically_correct_output(self):
        receipt = self.receipt()
        self.assertTrue(receipt["passed"])
        self.assertTrue(verify_attestation(receipt, KEY))
        self.db.record_attested_evidence(receipt)
        self.db.submit("one", "investigator", self.generation, 2, "one-proof")
        self.db.verify("one", "investigator", self.generation, 3)
        self.assertTrue(self.db.complete("one", "investigator", self.generation, 4))

    def test_self_reported_pass_cannot_be_submitted(self):
        self.db.record_evidence("fake", "r1", "test", passed=True, artifact="self-reported-passed")
        with self.assertRaises(GateError):
            self.db.submit("one", "investigator", self.generation, 2, "fake")

    def test_false_result_cannot_be_promoted(self):
        invalid = self.receipt(deliveries=["logical-event", "logical-event"])
        self.assertFalse(invalid["passed"])
        self.db.record_attested_evidence(invalid)
        with self.assertRaises(GateError):
            self.db.submit("one", "investigator", self.generation, 2, "one-proof")

    def test_pass_flag_tampering_invalidates_receipt(self):
        invalid = self.receipt(deliveries=["logical-event", "logical-event"])
        forged = copy.deepcopy(invalid)
        forged["passed"] = True
        self.assertFalse(verify_attestation(forged, KEY))
        with self.assertRaises(GateError):
            self.db.record_attested_evidence(forged)

    def test_wrong_evaluator_key_fails_closed(self):
        valid = self.receipt()
        self.assertFalse(verify_attestation(valid, OTHER_KEY))
        wrong_db = Ledger(verification_key=OTHER_KEY)
        try:
            with self.assertRaises(GateError):
                wrong_db.record_attested_evidence(valid)
        finally:
            wrong_db.close()

    def test_modified_revision_or_digest_fails(self):
        original = self.receipt()
        for field, value in (("revision", "r2"), ("artifact_sha256", "0" * 64)):
            forged = dict(original)
            forged[field] = value
            self.assertFalse(verify_attestation(forged, KEY))

    def test_revision_mismatch_is_not_accepted(self):
        receipt = self.receipt(revision="r2")
        self.db.record_attested_evidence(receipt)
        with self.assertRaises(GateError):
            self.db.submit("one", "investigator", self.generation, 2, "one-proof")

    def test_db_tampering_invalidates_stored_attestation(self):
        receipt = self.receipt()
        self.db.record_attested_evidence(receipt)
        self.db.db.execute("UPDATE evidence SET artifact='broken' WHERE id='one-proof'")
        with self.assertRaises(GateError):
            self.db.submit("one", "investigator", self.generation, 2, "one-proof")

    def test_reviewer_must_differ_from_owner(self):
        self.db.create("reviewed", "r1", authority="REVIEW_REQUIRED")
        gen = self.db.claim("reviewed", "investigator", 1, 30)
        receipt = self.receipt(evidence_id="review-proof")
        self.db.record_attested_evidence(receipt)
        self.db.submit("reviewed", "investigator", gen, 2, "review-proof")
        self.db.verify("reviewed", "investigator", gen, 3)
        with self.assertRaises(GateError):
            self.db.approve("reviewed", "investigator")
        self.db.approve("reviewed", "reviewer")
        self.assertTrue(self.db.complete("reviewed", "investigator", gen, 4))

    def test_missing_key_denies_attested_submission(self):
        no_key = Ledger()
        try:
            with self.assertRaises(GateError):
                no_key.record_attested_evidence(self.receipt())
        finally:
            no_key.close()


if __name__ == "__main__":
    unittest.main()
