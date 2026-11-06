"""Adversarial proofs for the bounded *synthetic* context-to-Ledger path.

No Codex/LLM agent, real source authentication, production action or key file.
All expected outcomes are public development expectations written by authors.
"""
from copy import deepcopy
import json
import secrets
import unittest

from workcoord_lab.evaluator import issue_delivery_attestation
from workcoord_lab.ledger import GateError, Ledger
from workcoord_lab.ledger_vertical_e2e import (
    BridgeHold, CANDIDATE, ELIGIBLE,
    complete_under_gate, evaluate_context_and_decision,
    load_fixture, packets, run_walkthrough, sha_body,
    submit_under_gate, verify_under_gate,
)
from workcoord_lab.intelligence_demo import fixture as navigator_fixture
from workcoord_lab.vertical_integration import evaluate_vertical


class LedgerVerticalE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_fixture()
        cls.first, cls.revised, cls.late = packets(cls.fixture)
        cls.context = navigator_fixture()["documents"]
        cls.old_doc = cls.fixture["initial_primary_document"]
        cls.new_doc = cls.fixture["revised_primary_document"]

    def gate(self, packet=None, doc=None, *, cut=4, previous=None, budget=None):
        return evaluate_context_and_decision(
            self.first if packet is None else packet, at_seq=cut,
            primary_document=self.old_doc if doc is None else doc,
            background_documents=self.context if previous is None else previous,
            max_chars=(self.fixture["context_budget_chars"]
                       if budget is None else budget),
        )

    def ledger(self, authority="REVIEW_REQUIRED", revision=None, work_id=None):
        key = secrets.token_bytes(32)  # runtime only, never a repository secret
        db = Ledger(verification_key=key)
        self.addCleanup(db.close)
        db.create(work_id or self.fixture["work_id"],
                  revision or self.first["manifest"]["source_revision"],
                  authority=authority)
        name = work_id or self.fixture["work_id"]
        gen = db.claim(name, self.fixture["owner_label"], now=10, ttl=50)
        return db, key, gen

    def add_valid_proof(self, db, key, gen, *, work_id=None, verify=False,
                        approve=False):
        work_id = work_id or self.fixture["work_id"]
        proof = issue_delivery_attestation(
            key, "fixture-valid-proof", work_id, "fictional-r2",
            self.fixture["logical_events"],
            self.fixture["correct_delivery_observations"],
        )
        db.record_attested_evidence(proof)
        db.submit(work_id, self.fixture["owner_label"], gen, now=11,
                  evidence_id=proof["evidence_id"])
        if verify:
            db.verify(work_id, self.fixture["owner_label"], gen, now=12)
        if approve:
            db.approve(work_id, self.fixture["reviewer_label"])
        return proof

    def test_one_case_executes_context_problem_claim_proof_and_completion(self):
        result = run_walkthrough()
        self.assertEqual(result["schema"], "workcoord.ledger-vertical-result/v0")
        self.assertEqual(result["final_ledger_status"], "DONE")
        self.assertTrue(result["ledger_event_chain_valid"])
        self.assertEqual(result["before_revision_ledger_status"], "VERIFIED")
        self.assertEqual(result["after_revision_ledger_status"], "CLAIMED")
        self.assertEqual(result["ledger_generation"], 1)
        self.assertEqual(len(result["final_synthetic_completion_sha256"]), 64)
        self.assertTrue(all(result["invariant_probes"].values()))
        self.assertGreaterEqual(len(result["invariant_probes"]), 8)
        self.assertIn("revision_invalidated", result["ledger_event_types"])
        self.assertIn("complete", result["ledger_event_types"])
        self.assertIn("approve", result["ledger_event_types"])
        self.assertGreater(result["ledger_event_types"].count("clock_advance"), 2)

    def test_public_receipt_deterministic_despite_ephemeral_hmac_key(self):
        first = run_walkthrough()
        second = run_walkthrough()
        self.assertEqual(first, second)
        self.assertEqual(first["fixture_sha256"], second["fixture_sha256"])
        self.assertEqual(first["final_synthetic_completion_sha256"],
                         second["final_synthetic_completion_sha256"])

    def test_context_actual_primary_source_read_and_manifest_pinned(self):
        result = self.gate()
        self.assertEqual(result["status"], ELIGIBLE)
        self.assertEqual(result["vertical_status"], CANDIDATE)
        self.assertEqual(result["navigator_status"],
                         "PROVISIONAL_INVESTIGATION_ONLY")
        self.assertTrue(result["requires_independent_test"])
        self.assertIn(self.first["manifest"]["primary_observation_id"],
                      result["selected_context_source_ids"])
        self.assertEqual(sha_body(self.old_doc["body"]),
                         self.first["manifest"]["primary_source_sha256"])
        self.assertLessEqual(result["unique_context_body_chars"],
                             self.fixture["context_budget_chars"])
        self.assertEqual(result["context_sectors_visited"],
                         ["worker", "queue", "api"])

    def test_missing_selected_primary_source_never_counts_as_retrieval(self):
        other = deepcopy(self.old_doc)
        other["id"] = "unrelated-observation"
        result = self.gate(doc=other)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["reason"], "PRIMARY_SOURCE_NOT_READ")

    def test_context_body_mismatch_rejected(self):
        bad = deepcopy(self.old_doc)
        bad["body"] = "X" + bad["body"][1:]
        self.assertEqual(len(bad["body"]), len(self.old_doc["body"]))
        result = self.gate(doc=bad)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["reason"],
                         "PRIMARY_CONTEXT_REVISION_OR_BODY_MISMATCH")

    def test_context_old_revision_rejected_even_when_body_is_identical(self):
        bad = deepcopy(self.old_doc)
        bad["revision"] = "fictional-r1"
        result = self.gate(doc=bad)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["reason"],
                         "PRIMARY_CONTEXT_REVISION_OR_BODY_MISMATCH")

    def test_tiny_budget_does_not_consume_unread_primary(self):
        result = self.gate(budget=1)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["reason"], "PRIMARY_SOURCE_NOT_READ")
        self.assertEqual(result["unique_context_body_chars"], 0)
        self.assertNotIn(self.old_doc["id"],
                         result["selected_context_source_ids"])

    def test_late_contradiction_prevents_sandbox_submission(self):
        result = self.gate(packet=self.late,
                           cut=self.fixture["late_counterevidence_history_cut"])
        self.assertEqual(result["vertical_status"], "HOLD_KNOWLEDGE")
        self.assertEqual(result["status"], "HOLD")
        db, key, gen = self.ledger()
        before = db.event_count()
        with self.assertRaises(BridgeHold):
            submit_under_gate(
                db, self.late, at_seq=6, primary_document=self.old_doc,
                background_documents=self.context, max_chars=2400,
                work_id=self.fixture["work_id"],
                owner=self.fixture["owner_label"], generation=gen, now=11,
                evidence_id="must-not-be-issued", key=key,
                logical_events=self.fixture["logical_events"],
                observed_deliveries=self.fixture["correct_delivery_observations"],
            )
        self.assertEqual(db.event_count(), before)
        self.assertEqual(db.get(self.fixture["work_id"])["status"], "CLAIMED")

    def test_revision_supersession_requires_new_four_stage_review(self):
        old = deepcopy(self.first)
        old["knowledge_actions"] = deepcopy(self.revised["knowledge_actions"])
        result = self.gate(packet=old, cut=8)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["vertical_status"], "HOLD_REASSESS_REVISION")
        self.assertTrue(result["source_epoch_drift"])
        self.assertEqual(self.gate(
            packet=self.revised, doc=self.new_doc, cut=7,
            previous=self.context + [self.old_doc])["status"], "HOLD")
        refreshed = self.gate(
            packet=self.revised, doc=self.new_doc, cut=8,
            previous=self.context + [self.old_doc])
        self.assertEqual(refreshed["vertical_status"], CANDIDATE)
        self.assertEqual(refreshed["status"], ELIGIBLE)
        self.assertNotEqual(refreshed["vertical_checkpoint_sha256"],
                            self.gate()["vertical_checkpoint_sha256"])

    def test_explicit_new_source_observation_and_review_are_in_fixture(self):
        actions = self.revised["knowledge_actions"]
        self.assertEqual([x["kind"] for x in actions[-4:]],
                         ["SOURCE_ADD", "SOURCE_SUPERSEDE",
                          "OBSERVATION_ADD", "REVIEW_ACCEPT"])
        self.assertEqual(actions[-1]["data"]["basis_ids"],
                         [self.revised["manifest"]["primary_observation_id"]])
        self.assertEqual(self.revised["manifest"]["primary_source_sha256"],
                         sha_body(self.new_doc["body"]))
        self.assertEqual(actions[-3]["data"]["old_source_id"],
                         self.first["manifest"]["primary_source_id"])

    def test_ledger_revision_mismatch_fails_before_proof(self):
        db, key, gen = self.ledger(revision="fictional-r3")
        before = db.event_count()
        try:
            submit_under_gate(
                db, self.first, at_seq=4, primary_document=self.old_doc,
                background_documents=self.context, max_chars=2400,
                work_id=self.fixture["work_id"],
                owner=self.fixture["owner_label"], generation=gen, now=11,
                evidence_id="should-not-be-issued", key=key,
                logical_events=self.fixture["logical_events"],
                observed_deliveries=self.fixture["correct_delivery_observations"],
            )
        except (BridgeHold, GateError):
            pass
        else:
            self.fail("stale source unexpectedly submitted")
        self.assertEqual(db.event_count(), before)
        self.assertEqual(db.get(self.fixture["work_id"])["status"], "CLAIMED")

    def test_work_identity_mismatch_blocks_proof(self):
        db, key, gen = self.ledger(work_id="other-fictional-task")
        before = db.event_count()
        with self.assertRaises(BridgeHold):
            submit_under_gate(
                db, self.first, at_seq=4, primary_document=self.old_doc,
                background_documents=self.context, max_chars=2400,
                work_id="other-fictional-task",
                owner=self.fixture["owner_label"], generation=gen, now=11,
                evidence_id="identity-forgery", key=key,
                logical_events=self.fixture["logical_events"],
                observed_deliveries=self.fixture["correct_delivery_observations"],
            )
        self.assertEqual(db.event_count(), before)

    def test_unexpected_ledger_authority_rejected_by_bridge(self):
        db, key, gen = self.ledger(authority="EDIT_SANDBOX")
        before = db.event_count()
        with self.assertRaises(BridgeHold):
            submit_under_gate(
                db, self.first, at_seq=4, primary_document=self.old_doc,
                background_documents=self.context, max_chars=2400,
                work_id=self.fixture["work_id"], owner=self.fixture["owner_label"],
                generation=gen, now=11, evidence_id="wrong-authority", key=key,
                logical_events=self.fixture["logical_events"],
                observed_deliveries=self.fixture["correct_delivery_observations"],
            )
        self.assertEqual(db.event_count(), before)

    def test_false_behavior_oracle_cannot_create_proof_or_submit(self):
        db, key, gen = self.ledger()
        before = db.event_count()
        try:
            submit_under_gate(
                db, self.first, at_seq=4, primary_document=self.old_doc,
                background_documents=self.context, max_chars=2400,
                work_id=self.fixture["work_id"], owner=self.fixture["owner_label"],
                generation=gen, now=11, evidence_id="broken-duplicate", key=key,
                logical_events=self.fixture["logical_events"],
                observed_deliveries=self.fixture["broken_delivery_observations"],
            )
        except (BridgeHold, GateError):
            pass
        else:
            self.fail("a failed semantic oracle was submitted")
        self.assertEqual(db.event_count(), before)
        self.assertEqual(db.get(self.fixture["work_id"])["status"], "CLAIMED")

    def test_cannot_verify_when_new_contradiction_is_in_current_packet(self):
        db, key, gen = self.ledger()
        self.add_valid_proof(db, key, gen, verify=False)
        before = db.event_count()
        with self.assertRaises(BridgeHold):
            verify_under_gate(
                db, self.late, at_seq=6, primary_document=self.old_doc,
                background_documents=self.context, max_chars=2400,
                work_id=self.fixture["work_id"], owner=self.fixture["owner_label"],
                generation=gen, now=12,
            )
        self.assertEqual(db.get(self.fixture["work_id"])["status"], "SUBMITTED")
        self.assertEqual(db.event_count(), before)

    def test_cannot_complete_after_late_contradiction_despite_approved_proof(self):
        db, key, gen = self.ledger()
        self.add_valid_proof(db, key, gen, verify=True, approve=True)
        before = db.event_count()
        with self.assertRaises(BridgeHold):
            complete_under_gate(
                db, self.late, at_seq=6, primary_document=self.old_doc,
                background_documents=self.context, max_chars=2400,
                work_id=self.fixture["work_id"], owner=self.fixture["owner_label"],
                generation=gen, now=13,
            )
        self.assertEqual(db.get(self.fixture["work_id"])["status"], "VERIFIED")
        self.assertEqual(db.event_count(), before)

    def test_actual_revision_change_resets_prior_approval_and_proof(self):
        db, key, gen = self.ledger()
        self.add_valid_proof(db, key, gen, verify=True, approve=True)
        before = db.get(self.fixture["work_id"])
        db.change_revision(self.fixture["work_id"], "fictional-r3")
        after = db.get(self.fixture["work_id"])
        self.assertEqual(before["status"], "VERIFIED")
        self.assertEqual(after["status"], "CLAIMED")
        self.assertEqual(after["generation"], gen)
        self.assertIsNone(after["approved_by"])
        self.assertIsNone(after["evidence_id"])
        with self.assertRaises(GateError):
            db.submit(self.fixture["work_id"], self.fixture["owner_label"],
                      gen, now=13, evidence_id="fixture-valid-proof")

    def test_approval_is_still_required_after_reproof(self):
        db, key, gen = self.ledger()
        self.add_valid_proof(db, key, gen, verify=True)
        with self.assertRaises(GateError):
            complete_under_gate(
                db, self.first, at_seq=4, primary_document=self.old_doc,
                background_documents=self.context, max_chars=2400,
                work_id=self.fixture["work_id"], owner=self.fixture["owner_label"],
                generation=gen, now=13)
        with self.assertRaises(GateError):
            db.approve(self.fixture["work_id"], self.fixture["owner_label"])
        db.approve(self.fixture["work_id"], self.fixture["reviewer_label"])
        receipt = complete_under_gate(
            db, self.first, at_seq=4, primary_document=self.old_doc,
            background_documents=self.context, max_chars=2400,
            work_id=self.fixture["work_id"], owner=self.fixture["owner_label"],
            generation=gen, now=13)
        self.assertEqual(len(receipt), 64)
        self.assertEqual(db.get(self.fixture["work_id"])["status"], "DONE")

    def test_public_receipt_never_contains_mac_or_secret_material(self):
        result = run_walkthrough()
        text = json.dumps(result, sort_keys=True)
        self.assertNotIn('"mac":', text)
        self.assertNotIn('"receipt_mac":', text)
        self.assertNotIn('"attestation":', text)
        self.assertNotIn('"verification_key":', text)
        self.assertNotIn(self.old_doc["body"], text)
        self.assertNotIn(self.new_doc["body"], text)
        self.assertFalse(result["external_source_authenticated"])
        self.assertFalse(result["reviewer_identity_authenticated"])
        self.assertFalse(result["independent_real_world_outcome_verified"])
        self.assertFalse(result["model_or_codex_api_used"])
        self.assertEqual(result["production_authorization"], "NONE")

    def test_all_published_outcomes_remain_advisory_not_production_rights(self):
        result = run_walkthrough()
        expected = self.fixture["expected_states"]
        self.assertEqual(result["first_gate"]["vertical_status"],
                         expected["initial_vertical"])
        self.assertEqual(result["late_counterevidence_gate"]["vertical_status"],
                         expected["late_vertical"])
        self.assertEqual(result["stale_source_gate"]["vertical_status"],
                         expected["stale_vertical"])
        self.assertEqual(result["refreshed_gate"]["vertical_status"],
                         expected["refreshed_vertical"])
        self.assertEqual(result["before_revision_ledger_status"],
                         expected["before_revision_ledger"])
        self.assertEqual(result["after_revision_ledger_status"],
                         expected["after_revision_ledger"])
        self.assertEqual(result["final_ledger_status"],
                         expected["after_reproof_ledger"])
        self.assertTrue(all(result["invariant_probes"].values()))


if __name__ == "__main__":
    unittest.main()
