"""Deterministic adversarial tests for the public cognitive-lens checkpoint.

Four distinct perspectives share ONE fictional issue and proposal; they are
neither four autonomous agents nor independent source verifiers.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from workcoord_lab.cognitive_perspectives import (
    LENSES, InvalidPerspectivePacket, evaluate_perspectives,
)
from workcoord_lab.cognitive_perspectives_suite import run_suite


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "examples" / "cognitive-perspective-cases-v0.json"


class CognitivePerspectivesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cases = json.loads(CATALOG.read_text(encoding="utf-8"))["cases"]
        cls.cases = {case["id"]: case for case in cases}

    def packet(self, case_id="CP01"):
        return deepcopy(self.cases[case_id]["packet"])

    def result(self, case_id="CP01"):
        return evaluate_perspectives(self.packet(case_id))

    def test_development_catalog_and_receipt(self):
        result = run_suite()
        self.assertEqual(result["case_count"], 19)
        self.assertEqual(result["expectations_met"], 19)
        self.assertEqual(len(result["catalog_sha256"]), 64)
        self.assertEqual(result["independent_agents_executed"], 0)
        self.assertFalse(result["authenticated_external_evidence"])
        self.assertFalse(result["measured_efficiency_gain"])

    def test_each_public_case_reproduces_its_expected_status(self):
        for case_id, case in self.cases.items():
            with self.subTest(case_id=case_id):
                result = self.result(case_id)
                self.assertEqual(result["status"], case["expected_status"])
                self.assertEqual(result["execution_authority"], "NONE")
                self.assertEqual(result["knowledge_promotion"], "NOT_GRANTED")
                self.assertFalse(result["external_problem_acceptance_verified"])
                self.assertFalse(result["source_independence_authenticated"])
                self.assertFalse(result["real_agent_efficiency_measured"])

    def test_four_lenses_distinct_from_technical_sectors(self):
        r = self.result("CP01")
        self.assertEqual(r["required_perspectives"], list(LENSES))
        self.assertEqual(r["received_perspectives"], list(LENSES))
        self.assertEqual(len(r["notes"]), 4)
        self.assertGreater(len({x["technical_sector"] for x in
                                r["cited_source_manifest"]}), 1)
        self.assertEqual({x["perspective"] for x in r["notes"]}, set(LENSES))
        self.assertNotIn("WORKER", LENSES)

    def test_consensus_is_only_advisory_ready_not_evidence_validity(self):
        r = self.result("CP01")
        self.assertEqual(r["status"], "ADVISORY_READY")
        self.assertEqual(r["recommended_next_step"], "REQUEST_EXTERNAL_ACCEPTANCE")
        self.assertEqual(r["execution_authority"], "NONE")
        self.assertFalse(r["external_problem_acceptance_verified"])

    def test_risk_challenge_cannot_be_outvoted_by_three_supporters(self):
        r = self.result("CP02")
        self.assertEqual(r["status"], "HOLD_CONTRADICTION")
        self.assertEqual(r["supporting_perspectives"],
                         ["EFFICIENCY", "ENGINEERING", "RESEARCH"])
        self.assertEqual(r["challenging_perspectives"], ["RISK"])
        self.assertTrue(r["has_support_challenge_conflict"])
        self.assertIn("delivery-repeat", r["counterevidence_ids"])
        self.assertIn("delivery-repeat", [x["id"] for x in
                                         r["cited_source_manifest"]])
        self.assertEqual(r["recommended_next_step"], "INVESTIGATE_OR_REVISE")

    def test_counterevidence_is_preserved_in_checkpoint_not_overwritten(self):
        r = self.result("CP02")
        self.assertEqual(len(r["notes"]), 4)
        risk = next(x for x in r["notes"] if x["perspective"] == "RISK")
        self.assertEqual(risk["stance"], "CHALLENGE")
        self.assertIn("delivery-repeat", risk["counterevidence_ids"])
        self.assertIn("unit-green", [x["id"] for x in r["cited_source_manifest"]])

    def test_efficiency_uncertainty_stops_automatic_recommendation(self):
        r = self.result("CP03")
        self.assertEqual(r["status"], "HOLD_UNRESOLVED_UNCERTAINTY")
        self.assertIn("EFFICIENCY", r["uncertain_perspectives"])
        self.assertTrue(next(x for x in r["notes"]
                             if x["perspective"] == "EFFICIENCY")["open_question"])

    def test_missing_risk_lens_blocks_structured_admission(self):
        r = self.result("CP04")
        self.assertIn("RISK", r["missing_perspectives"])
        self.assertEqual(r["status"], "HOLD_MISSING_PERSPECTIVE")

    def test_stale_review_must_not_be_silent(self):
        r = self.result("CP05")
        self.assertEqual(r["status"], "HOLD_STALE_PERSPECTIVE")
        self.assertIn("RISK", r["stale_perspectives"])

    def test_old_source_revision_exposes_coverage_gap(self):
        r = self.result("CP06")
        self.assertEqual(r["status"], "HOLD_SOURCE_GAP")
        self.assertIn("SOURCE_REVISION_NOT_CURRENT",
                      {gap["code"] for gap in r["source_gaps"]})

    def test_critical_consensus_still_requires_external_review(self):
        r = self.result("CP07")
        self.assertEqual(r["status"], "REQUIRES_EXTERNAL_REVIEW")
        self.assertEqual(r["recommended_next_step"], "REFER_FOR_EXTERNAL_REVIEW")
        self.assertEqual(r["execution_authority"], "NONE")
        self.assertEqual(r["knowledge_promotion"], "NOT_GRANTED")

    def test_quick_single_lens_path_has_lower_declared_overhead(self):
        quick = self.result("CP08")
        full = self.result("CP01")
        self.assertEqual(quick["required_perspectives"], ["ENGINEERING"])
        self.assertEqual(quick["received_perspectives"], ["ENGINEERING"])
        self.assertEqual(quick["status"], "ADVISORY_READY")
        self.assertEqual(quick["total_declared_review_units"], 1)
        self.assertGreater(full["total_declared_review_units"],
                           quick["total_declared_review_units"])
        self.assertLess(quick["unique_cited_source_body_characters"],
                        full["unique_cited_source_body_characters"])

    def test_quick_optional_challenge_is_not_ignored(self):
        r = self.result("CP09")
        self.assertEqual(r["required_perspectives"], ["ENGINEERING"])
        self.assertEqual(r["status"], "HOLD_CONTRADICTION")
        self.assertEqual(r["challenging_perspectives"], ["RISK"])
        self.assertIn("delivery-repeat", r["counterevidence_ids"])

    def test_causal_source_available_after_review_causes_hold(self):
        r = self.result("CP10")
        self.assertEqual(r["status"], "HOLD_SOURCE_GAP")
        self.assertIn("SOURCE_UNAVAILABLE_AT_REVIEW",
                      {gap["code"] for gap in r["source_gaps"]})

    def test_same_declared_group_is_not_authenticated_independence(self):
        r = self.result("CP11")
        self.assertEqual(r["status"], "ADVISORY_READY")
        self.assertEqual(r["source_independence_authenticated"], False)
        self.assertLess(len(r["declared_origin_groups"]),
                        len(r["cited_source_manifest"]))

    def test_high_self_reported_review_cost_is_not_efficacy(self):
        r = self.result("CP12")
        self.assertEqual(r["status"], "ADVISORY_READY")
        self.assertEqual(r["total_declared_review_units"], 400)
        self.assertFalse(r["real_agent_efficiency_measured"])

    def test_challenge_without_support_remains_unresolved(self):
        r = self.result("CP13")
        self.assertEqual(r["status"], "HOLD_UNRESOLVED_CHALLENGE")
        self.assertFalse(r["has_support_challenge_conflict"])
        self.assertEqual(len(r["challenging_perspectives"]), 4)

    def test_unknown_source_is_reported_not_hallucinated(self):
        r = self.result("CP14")
        self.assertEqual(r["status"], "HOLD_SOURCE_GAP")
        self.assertIn("UNKNOWN_SOURCE_REFERENCE",
                      {gap["code"] for gap in r["source_gaps"]})

    def test_no_cited_evidence_is_an_explicit_gap(self):
        r = self.result("CP15")
        self.assertEqual(r["status"], "HOLD_SOURCE_GAP")
        self.assertIn("NO_CITED_EVIDENCE",
                      {gap["code"] for gap in r["source_gaps"]})

    def test_review_written_after_decision_cannot_be_causal(self):
        r = self.result("CP16")
        self.assertEqual(r["status"], "HOLD_SOURCE_GAP")
        self.assertIn("REVIEW_AFTER_DECISION",
                      {gap["code"] for gap in r["source_gaps"]})

    def test_quick_doubt_does_not_need_four_lenses_to_hold(self):
        r = self.result("CP17")
        self.assertEqual(r["status"], "HOLD_UNRESOLVED_UNCERTAINTY")
        self.assertEqual(r["received_perspectives"], ["ENGINEERING"])

    def test_missing_lens_does_not_hide_existing_conflict(self):
        r = self.result("CP18")
        self.assertEqual(r["status"], "HOLD_MISSING_PERSPECTIVE")
        self.assertTrue(r["has_support_challenge_conflict"])
        self.assertIn("ENGINEERING", r["missing_perspectives"])
        self.assertIn("RISK", r["challenging_perspectives"])

    def test_technical_sector_change_not_new_cognitive_perspective(self):
        r = self.result("CP19")
        self.assertEqual(r["required_perspectives"], list(LENSES))
        self.assertEqual(r["status"], "ADVISORY_READY")
        self.assertEqual(len(r["notes"]), 4)

    def test_review_order_is_canonical_and_checkpoint_deterministic(self):
        packet = self.packet()
        a = evaluate_perspectives(packet)
        packet["reviews"].reverse()
        packet["sources"].reverse()
        b = evaluate_perspectives(packet)
        self.assertEqual(a, b)
        self.assertEqual(a["received_perspectives"], list(LENSES))
        self.assertEqual(a["checkpoint_sha256"], b["checkpoint_sha256"])

    def test_checkpoint_sha_can_be_independently_recomputed(self):
        result = self.result("CP02")
        digest = result.pop("checkpoint_sha256")
        encoded = json.dumps(result, ensure_ascii=True, sort_keys=True,
                             separators=(",", ":")).encode("utf-8")
        self.assertEqual(digest, hashlib.sha256(encoded).hexdigest())

    def test_cited_source_content_change_invalidates_checkpoint_even_same_length(self):
        p = self.packet()
        original = evaluate_perspectives(p)
        source = next(x for x in p["sources"] if x["id"] == "unit-green")
        before = source["finding"]
        source["finding"] = "X" + before[1:]
        self.assertEqual(len(source["finding"]), len(before))
        changed = evaluate_perspectives(p)
        self.assertNotEqual(original["checkpoint_sha256"],
                            changed["checkpoint_sha256"])
        original_manifest = {x["id"]: x for x in original["cited_source_manifest"]}
        new_manifest = {x["id"]: x for x in changed["cited_source_manifest"]}
        self.assertNotEqual(original_manifest["unit-green"]["finding_sha256"],
                            new_manifest["unit-green"]["finding_sha256"])

    def test_unreferenced_input_source_does_not_expand_read_context(self):
        p = self.packet()
        original = evaluate_perspectives(p)
        p["sources"].append({
            "id": "unrelated", "source_revision": "fictional-r2",
            "technical_sector": "database", "origin_group": "misc",
            "available_tick": 1, "finding": "Not cited by any current review.",
        })
        result = evaluate_perspectives(p)
        self.assertEqual(result, original)

    def test_source_cost_counts_cited_documents_only_once(self):
        r = self.result("CP01")
        cited_ids = {item["id"] for item in r["cited_source_manifest"]}
        original = self.packet()
        by_id = {item["id"]: item for item in original["sources"]}
        expected = sum(len(by_id[item]["finding"]) for item in cited_ids)
        self.assertEqual(r["unique_cited_source_body_characters"], expected)
        self.assertEqual(len(cited_ids), 3)
        self.assertEqual(r["total_declared_review_units"], 8)

    def test_input_is_unchanged_by_evaluation(self):
        p = self.packet()
        original = deepcopy(p)
        evaluate_perspectives(p)
        self.assertEqual(p, original)

    def test_altering_private_gold_label_has_no_impact(self):
        p = self.packet()
        a = evaluate_perspectives(p)
        p["true_cause"] = "opposite-to-fictional-label"
        p["hidden_correct_answer"] = "unknown"
        self.assertEqual(a, evaluate_perspectives(p))

    def test_duplicate_lens_rejected_instead_of_counting_twice(self):
        p = self.packet()
        p["reviews"].append(deepcopy(p["reviews"][0]))
        with self.assertRaises(InvalidPerspectivePacket):
            evaluate_perspectives(p)

    def test_review_must_target_same_issue_and_proposal(self):
        for key in ("issue_id", "proposal_id"):
            p = self.packet()
            p["reviews"][0][key] = "another-problem"
            with self.subTest(key=key), self.assertRaises(InvalidPerspectivePacket):
                evaluate_perspectives(p)

    def test_counterevidence_must_be_among_citations(self):
        p = self.packet()
        p["reviews"][3]["counterevidence_ids"] = ["delivery-repeat"]
        with self.assertRaises(InvalidPerspectivePacket):
            evaluate_perspectives(p)

    def test_unknown_lens_and_stance_rejected(self):
        p = self.packet()
        p["reviews"][0]["perspective"] = "DATABASE"
        with self.assertRaises(InvalidPerspectivePacket):
            evaluate_perspectives(p)
        p = self.packet()
        p["reviews"][0]["stance"] = "AUTO_APPROVE"
        with self.assertRaises(InvalidPerspectivePacket):
            evaluate_perspectives(p)

    def test_missing_open_question_is_invalid_for_challenge(self):
        p = self.packet()
        p["reviews"][3]["stance"] = "CHALLENGE"
        p["reviews"][3]["open_question"] = ""
        with self.assertRaises(InvalidPerspectivePacket):
            evaluate_perspectives(p)

    def test_typed_ticks_do_not_accept_bools_or_negative_numbers(self):
        for target, key in (("issue", "decision_tick"),
                            ("review", "review_tick"),
                            ("review", "estimated_review_units"),
                            ("source", "available_tick")):
            for invalid in (True, -1, "10", None, []):
                p = self.packet()
                selected = (p["issue"] if target == "issue" else
                            p["reviews"][0] if target == "review" else
                            p["sources"][0])
                selected[key] = invalid
                with self.subTest(target=target, key=key, invalid=str(invalid)):
                    with self.assertRaises(InvalidPerspectivePacket):
                        evaluate_perspectives(p)

    def test_duplicate_source_ids_and_bad_reference_types_rejected(self):
        p = self.packet()
        p["sources"].append(deepcopy(p["sources"][0]))
        with self.assertRaises(InvalidPerspectivePacket):
            evaluate_perspectives(p)
        p = self.packet()
        p["reviews"][0]["source_ids"] = [["unit-green"]]
        with self.assertRaises(InvalidPerspectivePacket):
            evaluate_perspectives(p)

    def test_malformed_packet_and_risk_fail_closed(self):
        for raw in (None, [], {"schema": "other"}, "literal"):
            with self.subTest(raw=str(raw)), self.assertRaises(InvalidPerspectivePacket):
                evaluate_perspectives(raw)
        p = self.packet()
        p["issue"]["risk"] = ["STRUCTURED"]
        with self.assertRaises(InvalidPerspectivePacket):
            evaluate_perspectives(p)

    def test_no_work_or_source_authorization_even_with_full_consensus(self):
        r = self.result("CP01")
        self.assertEqual(r["work_ownership"], "NOT_ASSIGNED")
        self.assertEqual(r["execution_authority"], "NONE")
        self.assertEqual(r["knowledge_promotion"], "NOT_GRANTED")
        self.assertFalse(r["external_problem_acceptance_verified"])


if __name__ == "__main__":
    unittest.main()
