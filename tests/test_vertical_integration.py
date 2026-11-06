"""Adversarial end-to-end checks of the *existing* public advisory contracts.

These are authored synthetic fixtures, not empirical agent successes.
The crucial test checks a late negative source against a previously green
technical and four-perspective advisory review.
"""
from copy import deepcopy
import hashlib
import json
import unittest

from workcoord_lab.vertical_integration import (
    VerticalInputError, evaluate_vertical,
)
from workcoord_lab.vertical_integration_suite import (
    load_catalog, materialize_case, run_suite,
)


class VerticalEvidenceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, cls.catalog_sha = load_catalog()
        cls.cases = {
            item["id"]: item
            for item in cls.catalog["cases"] + cls.catalog["malformed"]
        }

    def packet(self, id="VI01"):
        return materialize_case(self.catalog, self.cases[id])

    def result(self, id="VI01", cut=4):
        return evaluate_vertical(self.packet(id), at_seq=cut)

    def test_all_compact_public_cases_and_negative_bindings_are_executed(self):
        receipt = run_suite()
        self.assertEqual(receipt["case_count"], 14)
        self.assertEqual(receipt["positive_fixture_expectations_met"], 14)
        self.assertEqual(receipt["malformed_case_count"], 4)
        self.assertEqual(receipt["malformed_cases_rejected"], 4)
        self.assertEqual(receipt["catalog_sha256"], self.catalog_sha)
        self.assertFalse(receipt["scientific_truth_verified"])
        self.assertFalse(receipt["real_agent_learning_measured"])

    def test_all_published_case_phase_expectations_match(self):
        for case in self.catalog["cases"]:
            for phase in case["phases"]:
                with self.subTest(id=case["id"], cut=phase["at_seq"]):
                    result = self.result(case["id"], phase["at_seq"])
                    self.assertEqual(result["status"], phase["expected_status"])
                    self.assertEqual(result["authorization"], "NONE")
                    self.assertEqual(result["knowledge_promotion"], "NOT_GRANTED")
                    self.assertFalse(result["independent_outcome_verified"])
        for case in self.catalog["malformed"]:
            with self.subTest(id=case["id"]):
                with self.assertRaises(VerticalInputError):
                    self.result(case["id"], case["at_seq"])

    def test_earlier_positive_four_stage_candidate_remains_only_advisory(self):
        a = self.result("VI01", 4)
        self.assertEqual(a["status"],
                         "ADVISORY_CANDIDATE_FOR_EXTERNAL_ACCEPTANCE")
        self.assertEqual(a["stage_status"], {
            "research": "DESIGN_ADMISSIBLE",
            "problem": "CANDIDATE_FOR_EXTERNAL_ACCEPTANCE",
            "cognitive": "ADVISORY_READY",
            "knowledge_claim": "ADVISORY_CURRENT",
        })
        self.assertTrue(a["technical_tests_declared_green"])
        self.assertEqual(a["mandatory_open_nodes"], [])
        self.assertEqual(a["reason_codes"], [])
        self.assertFalse(a["independent_outcome_verified"])
        self.assertEqual(a["authorization"], "NONE")

    def test_late_counterevidence_blocks_even_when_all_earlier_checks_green(self):
        a = self.result("VI01", 4)
        b = self.result("VI01", 6)
        self.assertEqual(b["status"], "HOLD_KNOWLEDGE")
        self.assertEqual(b["stage_status"]["knowledge_claim"],
                         "HOLD_COUNTEREVIDENCE")
        self.assertTrue(b["technical_tests_declared_green"])
        for stage in ("research", "problem", "cognitive"):
            self.assertEqual(b["stage_status"][stage], a["stage_status"][stage])
            self.assertEqual(b["upstream_receipt_sha256"][stage],
                             a["upstream_receipt_sha256"][stage])
        self.assertIn("GENEALOGY_HOLD_COUNTEREVIDENCE", b["reason_codes"])
        self.assertNotEqual(a["knowledge_prefix_head_sha256"],
                            b["knowledge_prefix_head_sha256"])
        self.assertGreater(b["historical_observation_count"],
                           a["historical_observation_count"])
        self.assertNotEqual(a["checkpoint_sha256"], b["checkpoint_sha256"])

    def test_no_lookahead_from_future_evidence_at_earlier_cut(self):
        p = self.packet("VI01")
        self.assertEqual(evaluate_vertical(p, at_seq=4)["status"],
                         "ADVISORY_CANDIDATE_FOR_EXTERNAL_ACCEPTANCE")
        self.assertEqual(evaluate_vertical(p, at_seq=5)["status"],
                         "ADVISORY_CANDIDATE_FOR_EXTERNAL_ACCEPTANCE")
        self.assertEqual(evaluate_vertical(p, at_seq=6)["status"], "HOLD_KNOWLEDGE")

    def test_retracted_contradiction_does_not_silently_restore_old_review(self):
        self.assertEqual(self.result("VI02", 6)["status"], "HOLD_KNOWLEDGE")
        after_retract = self.result("VI02", 7)
        self.assertEqual(after_retract["status"], "HOLD_KNOWLEDGE")
        self.assertEqual(after_retract["stage_status"]["knowledge_claim"],
                         "HOLD_REVIEW_REQUIRED")
        self.assertIn("GENEALOGY_HOLD_REVIEW_REQUIRED",
                      after_retract["reason_codes"])

    def test_new_explicit_review_restores_advisory_while_history_preserved(self):
        last = self.result("VI02", 8)
        self.assertEqual(last["status"],
                         "ADVISORY_CANDIDATE_FOR_EXTERNAL_ACCEPTANCE")
        self.assertEqual(last["historical_observation_count"], 2)
        self.assertEqual(last["authorization"], "NONE")
        self.assertFalse(last["independent_outcome_verified"])

    def test_source_supersession_rejects_old_four_stage_epoch(self):
        p = self.packet("VI03")
        before = evaluate_vertical(p, at_seq=4)
        after = evaluate_vertical(p, at_seq=6)
        self.assertEqual(before["status"],
                         "ADVISORY_CANDIDATE_FOR_EXTERNAL_ACCEPTANCE")
        self.assertEqual(after["status"], "HOLD_REASSESS_REVISION")
        self.assertTrue(after["source_epoch_drift"])
        self.assertEqual(after["active_source_id"], "worker-r3")
        self.assertIn("SOURCE_EPOCH_CHANGED_REASSESS_ALL_STAGES",
                      after["reason_codes"])

    def test_new_genealogy_review_alone_cannot_reuse_stale_research_and_tests(self):
        result = self.result("VI04", 8)
        self.assertEqual(result["stage_status"]["knowledge_claim"],
                         "ADVISORY_CURRENT")
        self.assertTrue(result["source_epoch_drift"])
        self.assertEqual(result["status"], "HOLD_REASSESS_REVISION")
        self.assertEqual(result["authorization"], "NONE")

    def test_green_technical_tests_do_not_close_missing_behavior(self):
        result = self.result("VI05")
        self.assertEqual(result["status"], "HOLD_PROBLEM")
        self.assertTrue(result["technical_tests_declared_green"])
        self.assertEqual(result["mandatory_open_nodes"], ["delivery"])
        self.assertIn("PROBLEM_HOLD_REQUIRED_PROBLEM_OPEN",
                      result["reason_codes"])

    def test_research_falsifier_gap_not_bypassed_by_green_downstream(self):
        result = self.result("VI06")
        self.assertEqual(result["status"], "HOLD_RESEARCH")
        self.assertEqual(result["stage_status"]["research"], "NEEDS_RESEARCH")
        self.assertEqual(result["stage_status"]["problem"],
                         "CANDIDATE_FOR_EXTERNAL_ACCEPTANCE")

    def test_research_outcome_peeking_stays_blocked(self):
        result = self.result("VI07")
        self.assertEqual(result["status"], "HOLD_RESEARCH")
        self.assertIn("RESEARCH_NEEDS_RESEARCH", result["reason_codes"])

    def test_efficiency_uncertainty_is_not_fabricated_consensus(self):
        result = self.result("VI08")
        self.assertEqual(result["status"], "HOLD_COGNITIVE")
        self.assertEqual(result["stage_status"]["cognitive"],
                         "HOLD_UNRESOLVED_UNCERTAINTY")

    def test_missing_risk_perspective_remains_a_blocker(self):
        result = self.result("VI09")
        self.assertEqual(result["status"], "HOLD_COGNITIVE")
        self.assertEqual(result["stage_status"]["cognitive"],
                         "HOLD_MISSING_PERSPECTIVE")

    def test_quick_low_risk_path_does_not_require_four_lenses(self):
        result = self.result("VI10")
        self.assertEqual(result["status"],
                         "ADVISORY_CANDIDATE_FOR_EXTERNAL_ACCEPTANCE")
        self.assertEqual(result["assumed_review_effort_units"], 1)
        self.assertEqual(result["mandatory_open_nodes"], [])
        self.assertEqual(result["stage_status"]["cognitive"], "ADVISORY_READY")
        self.assertEqual(result["assumed_remedy_cost_table"], [])
        self.assertEqual(result["authorization"], "NONE")

    def test_critical_study_requires_external_review_despite_unanimity(self):
        result = self.result("VI11")
        self.assertEqual(result["status"], "REQUIRES_EXTERNAL_REVIEW")
        self.assertEqual(result["stage_status"]["research"],
                         "REQUIRES_EXTERNAL_REVIEW")
        self.assertEqual(result["stage_status"]["problem"],
                         "REQUIRES_EXTERNAL_REVIEW")
        self.assertEqual(result["stage_status"]["cognitive"],
                         "REQUIRES_EXTERNAL_REVIEW")
        self.assertEqual(result["authorization"], "NONE")

    def test_unrelated_revision_does_not_create_spurious_hold(self):
        self.assertEqual(self.result("VI12", 4)["status"],
                         "ADVISORY_CANDIDATE_FOR_EXTERNAL_ACCEPTANCE")
        after = self.result("VI12", 7)
        self.assertEqual(after["status"],
                         "ADVISORY_CANDIDATE_FOR_EXTERNAL_ACCEPTANCE")
        self.assertFalse(after["source_epoch_drift"])
        self.assertEqual(after["active_source_id"], "worker-r2")

    def test_new_supporting_observation_still_requires_fresh_review(self):
        after = self.result("VI13", 5)
        self.assertEqual(after["status"], "HOLD_KNOWLEDGE")
        self.assertEqual(after["stage_status"]["knowledge_claim"],
                         "HOLD_REVIEW_REQUIRED")

    def test_preexisting_risk_challenge_cannot_be_outvoted(self):
        early = self.result("VI14", 4)
        late = self.result("VI14", 6)
        self.assertEqual(early["status"], "HOLD_COGNITIVE")
        self.assertEqual(late["status"], "HOLD_KNOWLEDGE")
        self.assertEqual(late["cognitive_challenges"], ["RISK"])
        self.assertIn("COGNITIVE_HOLD_CONTRADICTION", late["reason_codes"])
        self.assertIn("GENEALOGY_HOLD_COUNTEREVIDENCE", late["reason_codes"])

    def test_cross_issue_stitching_is_rejected(self):
        with self.assertRaises(VerticalInputError):
            self.result("VI15", 4)

    def test_same_length_changed_primary_source_body_is_rejected(self):
        p = self.packet("VI16")
        changed = next(s for s in p["cognitive"]["sources"]
                       if s["id"] == p["manifest"]["primary_observation_id"])
        source = self.packet()["cognitive"]["sources"][0]
        self.assertEqual(len(changed["finding"]), len(source["finding"]))
        with self.assertRaises(VerticalInputError):
            evaluate_vertical(p, at_seq=4)

    def test_selected_remedy_must_be_the_reviewed_proposal(self):
        with self.assertRaises(VerticalInputError):
            self.result("VI17")

    def test_unrecognized_claim_of_authorization_rejected(self):
        with self.assertRaises(VerticalInputError):
            self.result("VI18")

    def test_research_source_identity_and_revision_are_fenced(self):
        for field, replacement in (("id", "unrelated-source"),
                                   ("revision", "fictional-r3")):
            p = self.packet()
            p["research"]["source"][field] = replacement
            with self.subTest(field=field), self.assertRaises(VerticalInputError):
                evaluate_vertical(p, at_seq=4)

    def test_shared_hypothesis_and_genealogy_claim_must_be_same(self):
        p = self.packet()
        p["research"]["hypotheses"][0]["claim"] = "A completely different explanation."
        with self.assertRaises(VerticalInputError):
            evaluate_vertical(p, at_seq=4)

    def test_wrong_primary_source_lineage_is_rejected(self):
        p = self.packet()
        p["manifest"]["source_lineage"] = "nonmatching-lineage"
        with self.assertRaises(VerticalInputError):
            evaluate_vertical(p, at_seq=4)

    def test_unshared_cognitive_evidence_does_not_count_as_integration(self):
        p = self.packet()
        shared = p["manifest"]["primary_observation_id"]
        for review in p["cognitive"]["reviews"]:
            review["source_ids"] = [x for x in review["source_ids"] if x != shared]
        with self.assertRaises(VerticalInputError):
            evaluate_vertical(p, at_seq=4)

    def test_unshared_problem_witness_cannot_be_stitched_into_flow(self):
        p = self.packet()
        shared = p["manifest"]["primary_observation_id"]
        p["problem"]["evidence"] = [w for w in p["problem"]["evidence"]
                                   if w["id"] != shared]
        with self.assertRaises(VerticalInputError):
            evaluate_vertical(p, at_seq=4)

    def test_inconsistent_source_observation_provenance_fails_closed(self):
        p = self.packet()
        p["knowledge_actions"][2]["data"]["source_id"] = "other-source"
        with self.assertRaises(VerticalInputError):
            evaluate_vertical(p, at_seq=4)

    def test_risk_tier_cannot_be_lowered_in_only_one_layer(self):
        p = self.packet()
        p["research"]["risk"] = "QUICK"
        with self.assertRaises(VerticalInputError):
            evaluate_vertical(p, at_seq=4)

    def test_zero_boolean_and_future_historical_cuts_are_rejected(self):
        p = self.packet()
        for cut in (True, None, 0, -1, len(p["knowledge_actions"]) + 1):
            with self.subTest(cut=cut), self.assertRaises(VerticalInputError):
                evaluate_vertical(p, at_seq=cut)

    def test_no_oracle_field_changes_a_decision_through_an_inner_stage(self):
        p = self.packet()
        a = evaluate_vertical(p, at_seq=4)
        p["research"]["gold_label"] = "false"
        p["problem"]["private_oracle"] = "wrong"
        p["cognitive"]["gold_label"] = "unknown"
        self.assertEqual(a, evaluate_vertical(p, at_seq=4))

    def test_no_source_or_agent_secret_appears_in_checkpoint(self):
        result = self.result()
        s = json.dumps(result, sort_keys=True)
        p = self.packet()
        finding = p["research"]["evidence"][0]["finding"]
        self.assertNotIn(finding, s)
        self.assertIn(p["manifest"]["primary_source_sha256"], s)
        self.assertFalse(result["source_authenticity_verified"])
        self.assertFalse(result["model_learning_performed"])

    def test_fingerprint_of_checkpoint_recomputes_independently(self):
        result = self.result("VI01", 6)
        digest = result.pop("checkpoint_sha256")
        material = json.dumps(result, sort_keys=True, ensure_ascii=True,
                              allow_nan=False, separators=(",", ":")).encode("utf-8")
        self.assertEqual(digest, hashlib.sha256(material).hexdigest())

    def test_fixture_compaction_preserves_per_case_replay_determinism(self):
        first = self.packet()
        self.assertEqual(first, self.packet())
        copy = deepcopy(first)
        evaluate_vertical(first, at_seq=4)
        self.assertEqual(copy, first)
        self.assertEqual(run_suite(), run_suite())

    def test_patches_refuse_commands_unknown_operations_and_bad_paths(self):
        baseline = {"patches": [{"op": "run", "path": ["research"],
                                 "value": "ls /"}]}
        with self.assertRaises(VerticalInputError):
            materialize_case(self.catalog, baseline)
        for path in (["problem", "missing", "x"],
                     ["research", "hypotheses", 999],
                     ["manifest", True]):
            with self.subTest(path=path), self.assertRaises(VerticalInputError):
                materialize_case(self.catalog, {
                    "patches": [{"op": "set", "path": path, "value": 1}]
                })

    def test_invalid_manifest_digest_and_unknown_top_field_rejected(self):
        p = self.packet()
        p["manifest"]["primary_source_sha256"] = "not-a-hash"
        with self.assertRaises(VerticalInputError):
            evaluate_vertical(p, at_seq=4)
        p = self.packet()
        p["directly_approve_execution"] = True
        with self.assertRaises(VerticalInputError):
            evaluate_vertical(p, at_seq=4)

    def test_every_result_preserves_all_authority_separations(self):
        for case in self.catalog["cases"]:
            for phase in case["phases"]:
                r = self.result(case["id"], phase["at_seq"])
                self.assertEqual(r["authorization"], "NONE")
                self.assertEqual(r["knowledge_promotion"], "NOT_GRANTED")
                self.assertEqual(r["work_ownership"], "NOT_ASSIGNED")
                self.assertFalse(r["independent_outcome_verified"])
                self.assertFalse(r["model_learning_performed"])


if __name__ == "__main__":
    unittest.main()
