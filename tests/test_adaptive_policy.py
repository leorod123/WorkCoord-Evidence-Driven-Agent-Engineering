"""Adversarial tests for adaptive escalation and the common development rubric."""
from copy import deepcopy
import json
import unittest

from workcoord_lab.adaptive_eval import (
    _case_pool, _policy_args, evaluate_public_development,
    load_development_inputs, run_case,
)
from workcoord_lab.adaptive_policy import PolicyError, run_adaptive_policy
from workcoord_lab.adaptive_evaluator import (
    grade_public_development_trace, validate_counterfactual_pair,
)


class AdaptiveEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flow, cls.paired, cls.cases, cls.oracle = load_development_inputs()
        cls.by_case = {item["id"]: item for item in cls.cases["cases"]}
        cls.gold = {item["id"]: item for item in cls.oracle["cases"]}

    def outcome(self, case_id, strategy="adaptive_policy"):
        row = run_case(self.flow, self.paired, self.by_case[case_id], strategy)
        row["development_grade"] = grade_public_development_trace(
            row, self.gold[case_id],
        )
        return row

    def test_seven_new_cases_four_arms_separate_from_prior_demo(self):
        result = evaluate_public_development()
        self.assertEqual(result["case_count"], 7)
        self.assertEqual(len(result["results"]), 28)
        self.assertEqual(len(result["summary"]), 4)
        self.assertTrue(result["counterfactual_access_pair_validated"])
        self.assertTrue(result["status"].startswith("PUBLIC_SYNTHETIC_EVAL"))

    def test_low_risk_local_policy_stays_with_current_evidence(self):
        row = self.outcome("AD01")
        actions = [x["action"] for x in row["trace"]]
        self.assertEqual(actions, ["START", "STAY"])
        self.assertEqual(row["decision"], "PROVISIONAL")
        self.assertEqual(row["provisional_hypothesis"], "ack-retry")
        self.assertEqual(row["development_grade"]["category"],
                         "SUPPORTED_PROVISIONAL")
        self.assertLess(row["read_characters"],
                        self.outcome("AD01", "full_corpus")["read_characters"])

    def test_high_risk_cross_sector_expands_and_preserves_sources(self):
        row = self.outcome("AD02")
        actions = [x["action"] for x in row["trace"]]
        self.assertGreaterEqual(actions.count("EXPAND"), 2)
        self.assertIn("queue-ack-r2", row["selected_source_ids"])
        self.assertIn("api-events-r2", row["selected_source_ids"])
        self.assertEqual(row["decision"], "PROVISIONAL")
        self.assertEqual(row["development_grade"]["category"],
                         "SUPPORTED_PROVISIONAL")
        self.assertEqual(row["trace"][-1]["action"], "STAY")

    def test_missing_dependency_causes_avoidable_hold_not_success(self):
        row = self.outcome("AD03")
        self.assertEqual(row["decision"], "HOLD")
        self.assertIn("INSUFFICIENT", row["reason"])
        self.assertNotIn("api-events-r2", row["selected_source_ids"])
        self.assertFalse(any(t["action"] == "EXPAND" for t in row["trace"]))
        self.assertEqual(row["development_grade"]["category"], "AVOIDABLE_HOLD")
        self.assertEqual(self.outcome("AD03", "full_corpus")
                         ["development_grade"]["category"],
                         "SUPPORTED_PROVISIONAL")

    def test_permitted_depth_escalation_finds_deep_required_source(self):
        row = self.outcome("AD04")
        self.assertIn("DEEPEN", [item["action"] for item in row["trace"]])
        self.assertIn("queue-deep-r2", row["selected_source_ids"])
        self.assertEqual(row["development_grade"]["category"],
                         "SUPPORTED_PROVISIONAL")
        self.assertLessEqual(row["read_characters"], row["budget_characters"])

    def test_ambiguous_visible_pair_remains_equal_and_both_hold(self):
        left = self.outcome("AD05A")
        right = self.outcome("AD05B")
        self.assertEqual(left["selected_source_ids"], right["selected_source_ids"])
        self.assertEqual(left["read_characters"], right["read_characters"])
        self.assertEqual(left["trace"], right["trace"])
        self.assertEqual(left["decision"], "HOLD")
        self.assertEqual(right["decision"], "HOLD")
        for row in (left, right):
            self.assertEqual(row["development_grade"]["category"],
                             "JUSTIFIED_HOLD_UNDER_DECLARED_ACCESS")
            self.assertNotIn("paired-deep-test", row["selected_source_ids"])
        self.assertNotEqual(self.gold["AD05A"]["expected_label"],
                            self.gold["AD05B"]["expected_label"])

    def test_full_baseline_cannot_read_pair_hidden_depth(self):
        for case_id in ("AD05A", "AD05B"):
            row = self.outcome(case_id, "full_corpus")
            self.assertEqual(row["decision"], "HOLD")
            self.assertNotIn("paired-deep-test", row["selected_source_ids"])
            self.assertEqual(row["development_grade"]["category"],
                             "JUSTIFIED_HOLD_UNDER_DECLARED_ACCESS")

    def test_pair_validator_rejects_visible_leakage(self):
        original = [{"id": "visible", "signals": {}}]
        altered = [{"id": "visible", "signals": {"secret": "supports"}}]
        with self.assertRaises(ValueError):
            validate_counterfactual_pair(original, altered,
                                         "producer-duplicates", "ack-retry")
        with self.assertRaises(ValueError):
            validate_counterfactual_pair(original, original, "ack-retry", "ack-retry")

    def test_budget_limited_hold_is_not_scored_as_valid_success(self):
        row = self.outcome("AD06")
        self.assertEqual(row["decision"], "HOLD")
        self.assertIn("BUDGET", row["reason"])
        self.assertLessEqual(row["read_characters"], 210)
        self.assertEqual(row["development_grade"]["category"],
                         "RESOURCE_LIMITED_HOLD_NOT_SCORED_SUCCESS")
        full = self.outcome("AD06", "full_corpus")
        self.assertEqual(full["development_grade"]["category"],
                         "COMPARATOR_INFEASIBLE_UNDER_EQUAL_CAP")

    def test_same_case_material_and_budget_for_all_arms(self):
        for case_id, case in self.by_case.items():
            permitted, _, _ = _case_pool(self.flow, self.paired, case)
            permissible = {doc["id"] for doc in permitted}
            for arm in self.cases["strategies"]:
                with self.subTest(case_id=case_id, arm=arm):
                    row = self.outcome(case_id, arm)
                    self.assertEqual(row["budget_characters"], case["max_chars"])
                    self.assertLessEqual(row["read_characters"], case["max_chars"])
                    self.assertTrue(set(row["selected_source_ids"]).issubset(permissible))
                    self.assertEqual(len(row["selected_source_ids"]),
                                     len(set(row["selected_source_ids"])))

    def test_selected_body_characters_recomputed_not_asserted(self):
        for case_id, case in self.by_case.items():
            permitted, _, _ = _case_pool(self.flow, self.paired, case)
            by_id = {doc["id"]: doc for doc in permitted}
            for arm in self.cases["strategies"]:
                row = self.outcome(case_id, arm)
                expected = sum(len(by_id[source_id]["body"])
                               for source_id in row["selected_source_ids"])
                self.assertEqual(row["read_characters"], expected)

    def test_policy_receives_task_data_not_case_or_gold_identity(self):
        for case in self.by_case.values():
            args = _policy_args(case)
            self.assertNotIn("world", args)
            self.assertNotIn("purpose", args)
            self.assertNotIn("id", args)
            self.assertNotIn("expected_label", args)
            self.assertEqual(args["max_chars"], case["max_chars"])

    def test_changing_oracle_only_changes_grade_after_selection(self):
        row = self.outcome("AD02")
        gold = deepcopy(self.gold["AD02"])
        gold["expected_label"] = "producer-duplicates"
        graded = grade_public_development_trace(row, gold)
        self.assertEqual(row["development_grade"]["category"],
                         "SUPPORTED_PROVISIONAL")
        self.assertEqual(graded["category"], "UNSUPPORTED_PROVISIONAL")
        self.assertEqual(row["decision"], "PROVISIONAL")

    def test_incomplete_evidence_is_never_supported_by_lucky_label(self):
        row = self.outcome("AD04", "dependency_expand")
        self.assertEqual(row["provisional_hypothesis"], "ack-retry")
        self.assertNotIn("queue-deep-r2", row["selected_source_ids"])
        self.assertEqual(row["development_grade"]["category"],
                         "UNSUPPORTED_PROVISIONAL")

    def test_an_arbitrary_hold_does_not_gain_credit(self):
        row = self.outcome("AD02")
        guessed_hold = deepcopy(row)
        guessed_hold["decision"] = "HOLD"
        guessed_hold["provisional_hypothesis"] = None
        grade = grade_public_development_trace(guessed_hold, self.gold["AD02"])
        self.assertEqual(grade["category"], "AVOIDABLE_HOLD")

    def test_raw_policy_never_returns_verified_or_authorized(self):
        case = self.by_case["AD02"]
        documents, _, info = _case_pool(self.flow, self.paired, case)
        policy = run_adaptive_policy(
            documents, issue_tags=info["issue_tags"],
            hypotheses=info["hypotheses"],
            current_revision=info["current_revision"], case=_policy_args(case),
        )
        self.assertEqual(policy["state"], "INVESTIGATION_ONLY_NOT_APPROVED")
        self.assertIn(policy["decision"], ("PROVISIONAL", "HOLD"))
        self.assertNotIn("execution_authorization", policy)

    def test_invalid_policy_risk_and_action_caps_are_rejected(self):
        case = deepcopy(self.by_case["AD01"])
        documents, _, info = _case_pool(self.flow, self.paired, case)
        for key, bad in (("risk_tier", "guaranteed"), ("max_actions", 0),
                         ("max_hops", -1), ("max_chars", True)):
            args = _policy_args(case)
            args[key] = bad
            with self.subTest(key=key), self.assertRaises(PolicyError):
                run_adaptive_policy(
                    documents, issue_tags=info["issue_tags"],
                    hypotheses=info["hypotheses"],
                    current_revision=info["current_revision"], case=args,
                )

    def test_action_limit_causes_hold_not_unearned_resolution(self):
        case = deepcopy(self.by_case["AD02"])
        documents, _, info = _case_pool(self.flow, self.paired, case)
        args = _policy_args(case)
        args["max_actions"] = 1
        policy = run_adaptive_policy(
            documents, issue_tags=info["issue_tags"],
            hypotheses=info["hypotheses"],
            current_revision=info["current_revision"], case=args,
        )
        self.assertEqual(policy["decision"], "HOLD")
        self.assertEqual(policy["reason"], "ACTION_BUDGET_EXHAUSTED")

    def test_deterministic_receipt_and_input_hashes(self):
        first = evaluate_public_development()
        second = evaluate_public_development()
        self.assertEqual(json.dumps(first, sort_keys=True),
                         json.dumps(second, sort_keys=True))
        self.assertEqual(len(first["input_sha256"]), 4)
        self.assertTrue(all(len(item) == 64 for item in first["input_sha256"].values()))

    def test_comparison_reports_failures_not_just_successful_candidates(self):
        report = evaluate_public_development()
        policy = next(x for x in report["summary"]
                      if x["strategy"] == "adaptive_policy")
        self.assertGreaterEqual(policy["avoidable_holds"], 1)
        self.assertGreaterEqual(policy["justified_access_limited_holds"], 2)
        self.assertTrue(any(
            r["development_grade"]["category"] == "UNSUPPORTED_PROVISIONAL"
            for r in report["results"]
        ))

    def test_source_order_metarmorphic_invariance(self):
        flow = deepcopy(self.flow)
        flow["documents"].reverse()
        first = evaluate_public_development()
        for case_id in ("AD01", "AD02", "AD03", "AD04"):
            case = self.by_case[case_id]
            # Action selection is deterministic and insensitive to file order.
            a = run_case(self.flow, self.paired, case, "adaptive_policy")
            b = run_case(flow, self.paired, case, "adaptive_policy")
            self.assertEqual(a["selected_source_ids"], b["selected_source_ids"])
            self.assertEqual(a["decision"], b["decision"])
        self.assertEqual(first["case_count"], 7)


if __name__ == "__main__":
    unittest.main()
