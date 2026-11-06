"""Adversarial tests of the synthetic complete-context-to-Ledger cycle.

All cases are visible development fixtures; not a real-agent success rate.
"""
from copy import deepcopy
import hashlib
import json
import unittest

from workcoord_lab.evaluator import issue_delivery_attestation
from workcoord_lab.full_ledger_cycle import (
    CycleInputError, FIXTURE, FIXTURE_TEST_KEY, READY,
    investigate_and_evaluate, load_packets, read_fixture, run_case, run_suite,
)
from workcoord_lab.ledger import GateError, Ledger
from workcoord_lab.vertical_integration import VerticalInputError, evaluate_vertical


class FullLedgerCycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = read_fixture()
        cls.packets = load_packets(cls.fixture)

    def test_all_four_published_synthetic_cases(self):
        result = run_suite()
        self.assertEqual(result["case_count"], 4)
        self.assertEqual({k: v["status"] for k, v in result["cases"].items()}, {
            "baseline": "DONE_SYNTHETIC",
            "late_counterevidence": "HOLD_COUNTEREVIDENCE",
            "revision_recheck": "DONE_AFTER_EXPLICIT_REVALIDATION",
            "behavior_failure": "HOLD_EXTERNAL_ORACLE",
        })
        self.assertFalse(result["external_agent_benchmark_run"])
        self.assertFalse(result["codex_api_used"])
        self.assertFalse(result["authenticated_reviewer_implemented"])
        self.assertFalse(result["ledger_enforces_advisory_state"])

    def test_positive_case_claims_verifies_reviews_then_completes(self):
        r = run_case("baseline")
        self.assertEqual(r["status"], "DONE_SYNTHETIC")
        self.assertEqual(r["work_status"], "DONE")
        self.assertEqual(r["work_revision"], "fictional-r2")
        self.assertEqual(r["generation"], 1)
        self.assertEqual(r["evidence_id"], "delivery-proof-r2")
        self.assertEqual(r["approved_by"], "reviewer-B")
        self.assertEqual(r["lease_clock"], 4)
        self.assertEqual(len(r["completion_receipt_sha256"]), 64)
        self.assertEqual(len(r["event_chain_sha256"]), 64)
        self.assertTrue(r["event_chain_valid"])
        self.assertEqual(r["evaluations"][0]["status"], READY)
        self.assertEqual(r["evaluations"][0]["authorization"], "NONE")

    def test_context_expands_worker_queue_api_with_matching_primary_body(self):
        result = investigate_and_evaluate(
            self.packets["original"], self.fixture["current_documents"], at_seq=4,
        )
        self.assertEqual(result["navigation_sectors"], ["worker", "queue", "api"])
        self.assertIn("worker-r2", result["context_source_ids"])
        self.assertIn("queue-ack-fictional-r2", result["context_source_ids"])
        self.assertIn("api-single-fictional-r2", result["context_source_ids"])
        self.assertEqual(result["preliminary_hypothesis"], "H-retry")
        self.assertEqual(result["status"], READY)
        self.assertFalse(result["independent_outcome_verified"])

    def test_historical_context_is_visible_but_not_a_current_source_proof(self):
        result = investigate_and_evaluate(
            self.packets["original"], self.fixture["current_documents"], at_seq=4,
        )
        self.assertIn("worker-r1", result["context_source_ids"])
        self.assertEqual(result["context_primary_source_sha256"],
                         self.packets["original"]["manifest"]["primary_source_sha256"])
        self.assertEqual(result["status"], READY)

    def test_late_adverse_observation_blocks_completion_after_green_technical_checks(self):
        result = run_case("late_counterevidence")
        first, late = result["evaluations"]
        self.assertEqual(first["status"], READY)
        self.assertEqual(late["status"], "HOLD_KNOWLEDGE")
        self.assertEqual(late["stage_status"]["knowledge_claim"], "HOLD_COUNTEREVIDENCE")
        for name in ("research", "problem", "cognitive"):
            self.assertEqual(first["stage_status"][name], late["stage_status"][name])
        self.assertEqual(result["status"], "HOLD_COUNTEREVIDENCE")
        self.assertEqual(result["work_status"], "VERIFIED")
        self.assertIsNone(result["completion_receipt_sha256"])
        self.assertEqual(result["approved_by"], "reviewer-B")
        self.assertFalse(result["ledger_enforces_advisory_state"])
        self.assertTrue(result["event_chain_valid"])

    def test_nonpassing_external_behavior_witness_blocks_even_after_advisory_green(self):
        result = run_case("behavior_failure")
        self.assertEqual(result["evaluations"][0]["status"], READY)
        self.assertEqual(result["status"], "HOLD_EXTERNAL_ORACLE")
        self.assertEqual(result["work_status"], "CLAIMED")
        self.assertIsNone(result["evidence_id"])
        self.assertIsNone(result["approved_by"])
        self.assertIsNone(result["completion_receipt_sha256"])
        self.assertEqual(result["lease_clock"], 1)
        self.assertTrue(result["event_chain_valid"])

    def test_revision_change_revokes_old_proof_review_and_requires_r3(self):
        r = run_case("revision_recheck")
        self.assertEqual(r["status"], "DONE_AFTER_EXPLICIT_REVALIDATION")
        self.assertEqual(r["work_status"], "DONE")
        self.assertEqual(r["work_revision"], "fictional-r3")
        self.assertEqual(r["generation"], 1)
        self.assertEqual(r["evidence_id"], "delivery-proof-r3")
        self.assertEqual(r["approved_by"], "reviewer-B")
        self.assertEqual(r["lease_clock"], 6)
        self.assertEqual([x["status"] for x in r["evaluations"]],
                         [READY, "HOLD_REASSESS_REVISION", READY])
        self.assertEqual(r["evaluations"][2]["source_revision"], "fictional-r3")
        self.assertTrue(r["event_chain_valid"])

    def test_revision_change_stale_check_cannot_carry_forward(self):
        stale = evaluate_vertical(
            self.packets["stale"], at_seq=self.fixture["stale_revision_cut"],
        )
        self.assertEqual(stale["status"], "HOLD_REASSESS_REVISION")
        self.assertTrue(stale["source_epoch_drift"])
        self.assertEqual(stale["source_revision"], "fictional-r2")
        fresh = evaluate_vertical(
            self.packets["fresh"], at_seq=self.fixture["rechecked_cut"],
        )
        self.assertEqual(fresh["status"], READY)
        self.assertNotEqual(stale["checkpoint_sha256"], fresh["checkpoint_sha256"])
        self.assertEqual(fresh["source_revision"], "fictional-r3")

    def test_new_recheck_keeps_old_genealogy_and_requires_explicit_new_review(self):
        actions = self.packets["fresh"]["knowledge_actions"]
        self.assertEqual(len(actions), 8)
        self.assertEqual([action["kind"] for action in actions[-4:]], [
            "SOURCE_ADD", "SOURCE_SUPERSEDE", "OBSERVATION_ADD", "REVIEW_ACCEPT",
        ])
        self.assertEqual(
            evaluate_vertical(self.packets["fresh"], at_seq=7)["status"],
            "HOLD_KNOWLEDGE",
        )
        self.assertEqual(
            evaluate_vertical(self.packets["fresh"], at_seq=8)["status"], READY
        )

    def test_recheck_without_new_explicit_knowledge_review_must_not_finish(self):
        p = deepcopy(self.packets["fresh"])
        p["knowledge_actions"].pop()
        r = run_case("revision_recheck", fresh_packet=p)
        self.assertEqual(r["status"], "HOLD_RECHECK_NOT_ADMISSIBLE")
        self.assertEqual(r["work_revision"], "fictional-r3")
        self.assertEqual(r["work_status"], "CLAIMED")
        self.assertIsNone(r["approved_by"])
        self.assertIsNone(r["completion_receipt_sha256"])

    def test_rechecked_source_body_corruption_rejected_before_new_proof(self):
        docs = deepcopy(self.fixture["rechecked_documents"])
        target = next(x for x in docs if x["id"] == "worker-r3")
        target["body"] = "Changed primary source body without digest update."
        with self.assertRaises(CycleInputError):
            run_case("revision_recheck", fresh_documents=docs)

    def test_modified_initial_source_body_fails_closed(self):
        fixture = deepcopy(self.fixture)
        doc = next(x for x in fixture["current_documents"] if x["id"] == "worker-r2")
        doc["body"] = "A modified observation with no shared source digest."
        with self.assertRaises(CycleInputError):
            run_case("baseline", fixture=fixture)

    def test_unread_primary_source_cannot_count_as_reviewed(self):
        fixture = deepcopy(self.fixture)
        fixture["current_documents"] = [
            x for x in fixture["current_documents"] if x["id"] != "worker-r2"
        ]
        with self.assertRaises(CycleInputError):
            run_case("baseline", fixture=fixture)

    def test_unrelated_packet_cannot_be_stitched_to_ledger(self):
        fixture = deepcopy(self.fixture)
        fixture["work_id"] = "unrelated-ticket"
        with self.assertRaises(CycleInputError):
            run_case("baseline", fixture=fixture)

    def test_altered_revised_issue_rejected_by_original_contract(self):
        p = deepcopy(self.packets["fresh"])
        p["problem"]["problem"]["id"] = "unrelated"
        with self.assertRaises(VerticalInputError):
            run_case("revision_recheck", fresh_packet=p)

    def test_risk_perspective_unresolved_counterproof_stays_blocked(self):
        p = deepcopy(self.packets["fresh"])
        p["cognitive"]["reviews"][0]["counterevidence_ids"] = ["unit-idempotency-r3"]
        r = run_case("revision_recheck", fresh_packet=p)
        self.assertEqual(r["status"], "HOLD_RECHECK_NOT_ADMISSIBLE")
        self.assertEqual(r["evaluations"][-1]["stage_status"]["cognitive"],
                         "HOLD_UNRESOLVED_COUNTEREVIDENCE")
        self.assertIsNone(r["completion_receipt_sha256"])

    def test_host_injected_clock_ignores_exaggerated_actor_times(self):
        r = run_case("baseline")
        self.assertEqual(r["lease_clock"], 4)
        self.assertLess(r["lease_clock"], 12345678)
        self.assertTrue(r["event_chain_valid"])

    def test_unsupported_mode_does_not_execute_any_work(self):
        with self.assertRaises(CycleInputError):
            run_case("freeform-agent-execution")

    def test_outputs_are_deterministic_without_raw_secret_or_source(self):
        one, two = run_suite(), run_suite()
        self.assertEqual(one, two)
        visible = json.dumps(one, sort_keys=True)
        self.assertNotIn(FIXTURE_TEST_KEY.decode("utf-8"), visible)
        self.assertNotIn(self.fixture["current_documents"][0]["body"], visible)
        self.assertEqual(one["fixture_sha256"],
                         hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
        self.assertFalse(one["source_authenticity_verified"])
        self.assertFalse(one["final_world_outcome_verified"])

    def test_no_independent_identity_or_real_world_claim(self):
        for mode in ("baseline", "late_counterevidence",
                     "revision_recheck", "behavior_failure"):
            r = run_case(mode)
            self.assertFalse(r["external_reviewer_authenticated"])
            self.assertFalse(r["ledger_enforces_advisory_state"])
            self.assertFalse(r["real_agent_used"])
            self.assertFalse(r["real_world_outcome_verified"])
            self.assertEqual(r["production_authorization"], "NONE")

    def test_revision_change_in_claimed_submitted_verified_states(self):
        for pre in ("CLAIMED", "SUBMITTED", "VERIFIED"):
            with self.subTest(pre=pre):
                db = Ledger(verification_key=FIXTURE_TEST_KEY)
                try:
                    db.create("case", "r2", authority="REVIEW_REQUIRED")
                    gen = db.claim("case", "owner", now=1, ttl=20)
                    if pre in ("SUBMITTED", "VERIFIED"):
                        receipt = issue_delivery_attestation(
                            FIXTURE_TEST_KEY, "proof-r2", "case", "r2",
                            ["e", "e"], ["e"],
                        )
                        db.record_attested_evidence(receipt)
                        db.submit("case", "owner", gen, 2, "proof-r2")
                    if pre == "VERIFIED":
                        db.verify("case", "owner", gen, 3)
                        db.approve("case", "reviewer")
                    db.change_revision("case", "r3")
                    work = db.get("case")
                    self.assertEqual(work["status"], "CLAIMED")
                    self.assertEqual(work["revision"], "r3")
                    self.assertEqual(work["generation"], gen)
                    self.assertIsNone(work["approved_by"])
                    self.assertIsNone(work["evidence_id"])
                    self.assertIsNone(work["receipt"])
                    self.assertTrue(db.verify_event_chain())
                finally:
                    db.close()

    def test_old_proof_and_old_approval_cannot_complete_revised_work(self):
        db = Ledger(verification_key=FIXTURE_TEST_KEY)
        try:
            db.create("case", "r2", authority="REVIEW_REQUIRED")
            g = db.claim("case", "owner", 1, 20)
            receipt = issue_delivery_attestation(
                FIXTURE_TEST_KEY, "proof-r2", "case", "r2", ["e", "e"], ["e"],
            )
            db.record_attested_evidence(receipt)
            db.submit("case", "owner", g, 2, "proof-r2")
            db.verify("case", "owner", g, 3)
            db.approve("case", "reviewer")
            db.change_revision("case", "r3")
            count = db.event_count()
            with self.assertRaises(GateError):
                db.complete("case", "owner", g, 4)
            with self.assertRaises(GateError):
                db.submit("case", "owner", g, 4, "proof-r2")
            self.assertEqual(db.event_count(), count)
            new = issue_delivery_attestation(
                FIXTURE_TEST_KEY, "proof-r3", "case", "r3", ["e", "e"], ["e"],
            )
            db.record_attested_evidence(new)
            db.submit("case", "owner", g, 4, "proof-r3")
            db.verify("case", "owner", g, 5)
            with self.assertRaises(GateError):
                db.complete("case", "owner", g, 6)
            db.approve("case", "reviewer")
            self.assertTrue(db.complete("case", "owner", g, 6))
            self.assertTrue(db.verify_event_chain())
        finally:
            db.close()

    def test_attempted_second_owner_cannot_fence_first_owner(self):
        db = Ledger(verification_key=FIXTURE_TEST_KEY,
                    time_source=lambda: 1)
        try:
            db.create("case", "r2")
            g = db.claim("case", "worker-A", 999999, 20)
            event_count = db.event_count()
            with self.assertRaises(GateError):
                db.claim("case", "worker-B", 888888, 20)
            self.assertEqual(db.get("case")["generation"], g)
            self.assertEqual(db.event_count(), event_count)
        finally:
            db.close()

    def test_unrelated_genealogy_change_does_not_induce_spurious_hold(self):
        catalog, _ = __import__(
            "workcoord_lab.vertical_integration_suite",
            fromlist=["load_catalog"],
        ).load_catalog()
        case = next(x for x in catalog["cases"] if x["id"] == "VI12")
        from workcoord_lab.vertical_integration_suite import materialize_case
        unrelated = materialize_case(catalog, case)
        self.assertEqual(evaluate_vertical(unrelated, at_seq=7)["status"], READY)

    def test_replay_of_completed_revision_is_idempotent(self):
        db = Ledger(verification_key=FIXTURE_TEST_KEY)
        try:
            db.create("case", "r2")
            gen = db.claim("case", "owner", 1, 20)
            db.record_attested_evidence(issue_delivery_attestation(
                FIXTURE_TEST_KEY, "proof", "case", "r2", ["e", "e"], ["e"],
            ))
            db.submit("case", "owner", gen, 2, "proof")
            db.verify("case", "owner", gen, 3)
            result = db.complete("case", "owner", gen, 4)
            count = db.event_count()
            self.assertEqual(db.complete("case", "owner", gen, 5), result)
            self.assertEqual(db.event_count(), count)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
