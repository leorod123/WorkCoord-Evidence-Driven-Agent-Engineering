"""Adversarial, public development tests for Problem & Decision admission.

All case labels, costs and witnesses are fictional and visible in the catalog.
These tests prove local contract behavior, not independent correctness.
"""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from workcoord_lab.problem_decision import (
    ProblemInputError, evaluate_problem_decision,
)
from workcoord_lab.problem_decision_suite import run_suite


CATALOG = Path(__file__).resolve().parents[1] / "examples" / "problem-decision-cases-v0.json"


class ProblemDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.cases = {case["id"]: case for case in catalog["cases"]}

    def packet(self, case_id="PD03"):
        return deepcopy(self.cases[case_id]["packet"])

    def result(self, case_id="PD03"):
        return evaluate_problem_decision(self.packet(case_id))

    def test_public_synthetic_catalog_and_receipt(self):
        receipt = run_suite()
        self.assertEqual(receipt["case_count"], 21)
        self.assertEqual(receipt["expectations_met"], 21)
        self.assertEqual(len(receipt["catalog_sha256"]), 64)
        self.assertTrue(receipt["no_external_validation_or_software_fix_claim"])
        self.assertEqual(json.dumps(receipt, sort_keys=True),
                         json.dumps(run_suite(), sort_keys=True))

    def test_all_expected_synthetic_fixture_outcomes(self):
        tally = {}
        for key, case in self.cases.items():
            with self.subTest(case=key):
                result = self.result(key)
                self.assertEqual(result["status"], case["expected_status"])
                self.assertEqual(result["required_open_node_ids"],
                                 sorted(case["expected_open_nodes"]))
                self.assertTrue(set(case["expected_decision_issues"]).issubset(
                    result["decision_issues"]
                ))
                self.assertFalse(result["semantic_closure_granted"])
                self.assertFalse(result["independent_source_validation"])
                self.assertEqual(result["execution_authority"], "NONE")
                self.assertEqual(result["knowledge_promotion"], "NOT_GRANTED")
                tally[result["status"]] = tally.get(result["status"], 0) + 1
        self.assertEqual(tally, {
            "CANDIDATE_FOR_EXTERNAL_ACCEPTANCE": 7,
            "HOLD_REQUIRED_PROBLEM_OPEN": 8,
            "HOLD_DECISION_INCOMPLETE": 5,
            "REQUIRES_EXTERNAL_REVIEW": 1,
        })

    def test_technical_green_with_missing_behavior_is_not_semantic_closure(self):
        r = self.result("PD02")
        self.assertTrue(r["reported_technical_tests_green"])
        self.assertEqual(r["status"], "HOLD_REQUIRED_PROBLEM_OPEN")
        self.assertIn("delivery", r["required_open_node_ids"])
        self.assertIn("TECHNICAL_GREEN_DOES_NOT_CLOSE_REQUIRED_OUTCOMES",
                      r["decision_issues"])
        delivery = next(x for x in r["node_results"] if x["id"] == "delivery")
        self.assertEqual(delivery["acceptance"][0]["outcome"],
                         "MISSING_REQUIRED_BEHAVIOR_WITNESS")
        self.assertFalse(r["semantic_closure_granted"])

    def test_green_and_all_declared_witnesses_only_candidate_for_review(self):
        r = self.result("PD03")
        self.assertTrue(r["reported_technical_tests_green"])
        self.assertEqual(r["required_open_node_ids"], [])
        self.assertEqual(r["status"], "CANDIDATE_FOR_EXTERNAL_ACCEPTANCE")
        self.assertFalse(r["semantic_closure_granted"])
        self.assertFalse(r["real_world_cost_measured"])

    def test_quick_simple_work_needs_no_heavy_alternative_matrix(self):
        r = self.result("PD01")
        self.assertEqual(r["decision_status"], "LIGHTWEIGHT_ROUTE")
        self.assertEqual(r["estimated_alternatives"], [])
        self.assertEqual(r["status"], "CANDIDATE_FOR_EXTERNAL_ACCEPTANCE")
        self.assertEqual(r["required_leaf_ids"], ["small"])

    def test_quick_still_cannot_skip_its_only_acceptance(self):
        r = self.result("PD21")
        self.assertEqual(r["status"], "HOLD_REQUIRED_PROBLEM_OPEN")
        self.assertIn("small", r["required_open_node_ids"])

    def test_child_required_obligation_blocks_parent_readiness(self):
        r = self.result("PD02")
        self.assertEqual(r["root_id"], "incident")
        self.assertIn("delivery", r["required_open_node_ids"])
        self.assertNotIn("incident", r["required_open_node_ids"])
        self.assertEqual(r["status"], "HOLD_REQUIRED_PROBLEM_OPEN")
        root = next(x for x in r["node_results"] if x["id"] == "incident")
        self.assertEqual(root["subtree_readiness"], "BLOCKED_BY_REQUIRED_DESCENDANTS")
        self.assertEqual(root["blocked_by_required_descendants"], ["delivery"])

    def test_missing_root_acceptance_blocks_even_when_children_are_green(self):
        r = self.result("PD17")
        self.assertIn("incident", r["required_open_node_ids"])
        self.assertEqual(r["status"], "HOLD_REQUIRED_PROBLEM_OPEN")

    def test_optional_open_node_is_visible_but_not_a_closure_gate(self):
        for case_id in ("PD04", "PD20"):
            with self.subTest(case_id=case_id):
                r = self.result(case_id)
                self.assertEqual(r["status"], "CANDIDATE_FOR_EXTERNAL_ACCEPTANCE")
                self.assertNotIn("telemetry", r["required_open_node_ids"])
                optional = next(x for x in r["node_results"] if x["id"] == "telemetry")
                self.assertEqual(optional["readiness"], "OPTIONAL_NOT_A_CLOSURE_GATE")
                self.assertIn("OPTIONAL_NODE_NOT_KNOWN", optional["issues"])

    def test_required_root_with_only_optional_child_is_mandatory_leaf(self):
        r = self.result("PD15")
        self.assertEqual(r["required_leaf_ids"], ["incident"])
        self.assertEqual(r["status"], "CANDIDATE_FOR_EXTERNAL_ACCEPTANCE")
        self.assertEqual(r["required_open_node_ids"], [])

    def test_knowledge_unknown_is_not_fixed_by_a_green_test(self):
        r = self.result("PD18")
        self.assertIn("delivery", r["required_open_node_ids"])
        self.assertIn("REQUIRED_NODE_NOT_KNOWN",
                      next(x for x in r["node_results"] if x["id"] == "delivery")["issues"])

    def test_stale_witness_never_counts_as_current_pass(self):
        r = self.result("PD05")
        target = next(x for x in r["node_results"] if x["id"] == "delivery")
        self.assertEqual(target["acceptance"][0]["declared_current_pass_ids"], [])
        self.assertIn("STALE_EVIDENCE_PRESENT", target["issues"])
        self.assertIn("MISSING_REQUIRED_BEHAVIOR_WITNESS", target["issues"])
        self.assertEqual(r["status"], "HOLD_REQUIRED_PROBLEM_OPEN")

    def test_technical_witness_cannot_substitute_for_behavior_probe(self):
        r = self.result("PD16")
        target = next(x for x in r["node_results"] if x["id"] == "delivery")
        self.assertEqual(target["acceptance"][0]["declared_current_pass_ids"], [])
        self.assertIn("WRONG_EVIDENCE_KIND_PRESENT", target["issues"])
        self.assertEqual(r["status"], "HOLD_REQUIRED_PROBLEM_OPEN")

    def test_current_negative_probe_cannot_be_outvoted_by_positive_probe(self):
        r = self.result("PD06")
        target = next(x for x in r["node_results"] if x["id"] == "delivery")
        self.assertEqual(target["acceptance"][0]["outcome"], "CONTRADICTED")
        self.assertEqual(target["acceptance"][0]["declared_current_fail_ids"],
                         ["delivery-failed-replay"])
        self.assertEqual(r["status"], "HOLD_REQUIRED_PROBLEM_OPEN")

    def test_selected_solution_must_address_all_required_leaves(self):
        r = self.result("PD11")
        self.assertIn("REQUIRED_LEAF_NOT_ADDRESSED_BY_SELECTED_ALTERNATIVE",
                      r["decision_issues"])
        self.assertEqual(r["status"], "HOLD_DECISION_INCOMPLETE")

    def test_new_component_must_explain_cheaper_comparable_reuse(self):
        r = self.result("PD08")
        self.assertEqual(r["status"], "HOLD_DECISION_INCOMPLETE")
        self.assertIn("CHEAPER_COMPARABLE_REUSE_NOT_EXPLAINED",
                      r["decision_issues"])

    def test_documenting_reuse_rejection_still_is_not_proof_of_optimality(self):
        r = self.result("PD09")
        self.assertEqual(r["status"], "CANDIDATE_FOR_EXTERNAL_ACCEPTANCE")
        self.assertFalse(r["real_world_cost_measured"])
        self.assertFalse(r["semantic_closure_granted"])
        self.assertNotIn("CHEAPER_COMPARABLE_REUSE_NOT_EXPLAINED",
                         r["decision_issues"])

    def test_common_horizon_accounts_for_recurring_cost(self):
        r = self.result("PD10")
        costs = {x["id"]: x for x in r["estimated_alternatives"]}
        self.assertEqual(costs["reuse"]["estimated_total_units"], 11)
        self.assertEqual(costs["build"]["estimated_total_units"], 73)
        self.assertEqual(costs["reuse"]["horizon_cycles"], 24)
        self.assertEqual(costs["build"]["horizon_cycles"], 24)
        self.assertEqual(costs["reuse"]["risk_allowance_units"], 1)
        self.assertEqual(costs["build"]["recurring_units"], 3)
        self.assertLess(costs["reuse"]["estimated_total_units"],
                        costs["build"]["estimated_total_units"])

    def test_structured_decision_cannot_be_empty(self):
        r = self.result("PD12")
        self.assertIn("ALTERNATIVES_NOT_RECORDED", r["decision_issues"])
        self.assertEqual(r["status"], "HOLD_DECISION_INCOMPLETE")

    def test_defer_is_a_conscious_noncompletion(self):
        r = self.result("PD19")
        self.assertIn("DECISION_IS_DEFERRED", r["decision_issues"])
        self.assertNotEqual(r["status"], "CANDIDATE_FOR_EXTERNAL_ACCEPTANCE")

    def test_critical_ready_design_needs_external_review(self):
        r = self.result("PD13")
        self.assertEqual(r["status"], "REQUIRES_EXTERNAL_REVIEW")
        self.assertEqual(r["decision_issues"], [])
        self.assertEqual(r["execution_authority"], "NONE")

    def test_critical_missing_containment_is_not_approval(self):
        r = self.result("PD14")
        self.assertEqual(r["status"], "HOLD_DECISION_INCOMPLETE")
        self.assertIn("CRITICAL_IMPACT_CONTAINMENT_NOT_RECORDED",
                      r["decision_issues"])

    def test_selected_application_needs_steps_and_rollback_when_required(self):
        p = self.packet()
        p["decision"]["application"]["steps"] = []
        p["decision"]["application"]["rollback"] = ""
        r = evaluate_problem_decision(p)
        self.assertIn("APPLICATION_STEPS_MISSING", r["decision_issues"])
        self.assertIn("REVERSIBLE_APPLICATION_HAS_NO_ROLLBACK", r["decision_issues"])

    def test_application_mode_must_match_selected_remedy(self):
        p = self.packet("PD03")
        p["decision"]["application"]["mode"] = "new_component"
        result = evaluate_problem_decision(p)
        self.assertIn("APPLICATION_MODE_CONFLICTS_WITH_SELECTED_STRATEGY",
                      result["decision_issues"])
        self.assertEqual(result["status"], "HOLD_DECISION_INCOMPLETE")

    def test_options_require_distinct_strategies_in_structured_case(self):
        p = self.packet()
        p["decision"]["alternatives"][1]["strategy"] = "reuse"
        r = evaluate_problem_decision(p)
        self.assertIn("ALTERNATIVE_COMPARISON_INSUFFICIENT", r["decision_issues"])

    def test_no_case_or_gold_label_is_consulted_by_core(self):
        p = self.packet()
        a = evaluate_problem_decision(p)
        p["expected_status"] = "any-other-answer"
        p["gold_hidden_answer"] = "opposite-of-expected"
        self.assertEqual(a, evaluate_problem_decision(p))

    def test_output_does_not_repeat_untrusted_problem_or_witness_prose(self):
        p = self.packet()
        p["problem"]["statement"] = "FICTIONAL_UNTRUSTED_SENSITIVE_TEXT_MARKER"
        p["evidence"][0]["id"] = "renamed-evidence"
        r = evaluate_problem_decision(p)
        self.assertNotIn("FICTIONAL_UNTRUSTED_SENSITIVE_TEXT_MARKER",
                         json.dumps(r, sort_keys=True))
        self.assertEqual(r["schema"], "workcoord.problem-decision-evaluation/v0")

    def test_cycle_in_problem_hierarchy_is_rejected(self):
        p = self.packet()
        p["nodes"][1]["parent_id"] = "delivery"
        p["nodes"][2]["parent_id"] = "worker"
        with self.assertRaises(ProblemInputError):
            evaluate_problem_decision(p)

    def test_dangling_and_duplicate_nodes_are_rejected(self):
        p = self.packet()
        p["nodes"][1]["parent_id"] = "nonexistent"
        with self.assertRaises(ProblemInputError):
            evaluate_problem_decision(p)
        p = self.packet()
        p["nodes"].append(deepcopy(p["nodes"][0]))
        with self.assertRaises(ProblemInputError):
            evaluate_problem_decision(p)

    def test_required_node_under_optional_parent_is_rejected(self):
        p = self.packet()
        p["nodes"][1]["parent_id"] = "telemetry"
        with self.assertRaises(ProblemInputError):
            evaluate_problem_decision(p)

    def test_unexpected_evidence_target_is_a_malformed_fixture(self):
        p = self.packet()
        p["evidence"][0]["criterion_id"] = "not-a-criterion"
        with self.assertRaises(ProblemInputError):
            evaluate_problem_decision(p)

    def test_duplicate_evidence_ids_are_not_accepted(self):
        p = self.packet()
        p["evidence"][0]["id"] = p["evidence"][1]["id"]
        with self.assertRaises(ProblemInputError):
            evaluate_problem_decision(p)

    def test_source_revision_does_not_silently_follow_witnesses(self):
        p = self.packet()
        p["problem"]["source_revision"] = "fictional-r3"
        r = evaluate_problem_decision(p)
        self.assertEqual(set(r["required_open_node_ids"]),
                         {"incident", "worker", "delivery"})

    def test_invalid_types_fail_closed_with_specific_error(self):
        for key, value in (
            ("risk", ["STRUCTURED"]), ("nodes", {}),
            ("evidence", {}), ("implementation", []),
        ):
            p = self.packet()
            p[key] = value
            with self.subTest(key=key), self.assertRaises(ProblemInputError):
                evaluate_problem_decision(p)
        for value in ("true", 1, None, [], {}):
            p = self.packet()
            p["implementation"]["technical_tests_green"] = value
            with self.subTest(value=value), self.assertRaises(ProblemInputError):
                evaluate_problem_decision(p)

    def test_bad_cost_and_scope_values_fail_closed(self):
        for field, value in (("horizon_cycles", True), ("horizon_cycles", 0),
                             ("horizon_cycles", -5)):
            p = self.packet()
            p["decision"][field] = value
            with self.subTest(value=value), self.assertRaises(ProblemInputError):
                evaluate_problem_decision(p)
        for field, value in (("recurring_units", True), ("upfront_units", -1),
                             ("risk_allowance_units", None)):
            p = self.packet()
            p["decision"]["alternatives"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ProblemInputError):
                evaluate_problem_decision(p)
        p = self.packet()
        p["decision"]["alternatives"][0]["addresses"] = [["worker"]]
        with self.assertRaises(ProblemInputError):
            evaluate_problem_decision(p)

    def test_selected_option_must_exist(self):
        p = self.packet()
        p["decision"]["selected_id"] = "phantom-alternative"
        with self.assertRaises(ProblemInputError):
            evaluate_problem_decision(p)

    def test_all_outputs_advisory_even_with_work_status_done(self):
        p = self.packet()
        p["implementation"]["work_status"] = "DONE"
        r = evaluate_problem_decision(p)
        self.assertFalse(r["semantic_closure_granted"])
        self.assertEqual(r["knowledge_promotion"], "NOT_GRANTED")
        self.assertEqual(r["execution_authority"], "NONE")

    def test_no_real_world_cost_or_independent_evidence_is_claimed(self):
        r = self.result("PD03")
        self.assertFalse(r["real_world_cost_measured"])
        self.assertFalse(r["independent_source_validation"])
        self.assertIn("self-declared", r["disclaimer"])


if __name__ == "__main__":
    unittest.main()
