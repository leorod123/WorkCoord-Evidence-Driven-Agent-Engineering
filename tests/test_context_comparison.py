"""Regression tests for three retrieval arms and public development rubric.

This is not an LLM benchmark, a sealed oracle or a token-cost measurement.
"""
from copy import deepcopy
import json
import unittest

from workcoord_lab.context_comparison import (
    STRATEGIES, _case_documents, common_annotated_reader, evaluate_selected,
    load_public_development_inputs, run_case, run_comparison, select_context,
)
from workcoord_lab.intelligence import ContextNavigator, NavigationError


class ContextComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture, cls.cases, cls.oracle = load_public_development_inputs()
        cls.cases_by_id = {x["id"]: x for x in cls.cases["cases"]}
        cls.gold_by_id = {x["id"]: x for x in cls.oracle["cases"]}

    def row(self, case_id, arm):
        return run_case(self.fixture, self.cases_by_id[case_id],
                        self.gold_by_id[case_id], arm)

    def test_equal_three_arms_and_four_cases(self):
        result = run_comparison()
        self.assertEqual(STRATEGIES,
                         ("full_corpus", "local_sector", "dependency_expand"))
        self.assertEqual(set(self.cases_by_id), {"CTX01", "CTX02", "CTX03", "CTX04"})
        self.assertEqual(result["case_count"], 4)
        self.assertEqual(len(result["results"]), 12)
        self.assertTrue(result["public_oracle_not_held_out"])

    def test_full_baseline_sees_every_source_under_common_budget(self):
        for case_id, case in self.cases_by_id.items():
            with self.subTest(case_id=case_id):
                result = self.row(case_id, "full_corpus")
                documents = _case_documents(self.fixture, case)
                self.assertEqual(set(result["selection"]["source_ids"]),
                                 {doc["id"] for doc in documents})
                self.assertEqual(result["selection"]["read_characters"],
                                 sum(len(doc["body"]) for doc in documents))
                self.assertLessEqual(result["selection"]["read_characters"],
                                     case["max_chars"])
                self.assertEqual(
                    result["external_development_rubric"]["decisive_recall"], 1.0)

    def test_local_evidence_saves_characters_without_missing_gold(self):
        local = self.row("CTX01", "local_sector")
        full = self.row("CTX01", "full_corpus")
        self.assertEqual(local["external_development_rubric"]["decisive_recall"], 1.0)
        self.assertTrue(local["external_development_rubric"]
                        ["evidence_supported_provisional_label"])
        self.assertLess(local["selection"]["read_characters"],
                        full["selection"]["read_characters"])

    def test_expansion_recovers_linked_counterevidence(self):
        local = self.row("CTX02", "local_sector")
        expanded = self.row("CTX02", "dependency_expand")
        full = self.row("CTX02", "full_corpus")
        self.assertEqual(local["external_development_rubric"]["decisive_recall"], 0.0)
        self.assertEqual(expanded["external_development_rubric"]["decisive_recall"], 1.0)
        self.assertIn("queue-ack-r2", expanded["selection"]["source_ids"])
        self.assertIn("api-events-r2", expanded["selection"]["source_ids"])
        self.assertEqual(local["reader"]["provisional_hypothesis"], "producer-duplicates")
        self.assertEqual(expanded["reader"]["provisional_hypothesis"], "ack-retry")
        self.assertLess(expanded["selection"]["read_characters"],
                        full["selection"]["read_characters"])

    def test_missing_link_is_a_counterexample_to_expansion(self):
        local = self.row("CTX03", "local_sector")
        expanded = self.row("CTX03", "dependency_expand")
        full = self.row("CTX03", "full_corpus")
        self.assertEqual(local["selection"]["source_ids"],
                         expanded["selection"]["source_ids"])
        self.assertEqual(len(expanded["selection"]["nav_steps"]), 1)
        self.assertEqual(expanded["external_development_rubric"]["decisive_recall"], 0.0)
        self.assertEqual(full["external_development_rubric"]["decisive_recall"], 1.0)
        self.assertFalse(expanded["external_development_rubric"]
                         ["evidence_supported_provisional_label"])

    def test_depth_bottleneck_can_look_correct_but_lack_evidence(self):
        expanded = self.row("CTX04", "dependency_expand")
        full = self.row("CTX04", "full_corpus")
        self.assertNotIn("queue-deep-r2", expanded["selection"]["source_ids"])
        self.assertTrue(expanded["external_development_rubric"]
                        ["provisional_label_matches_fixture"])
        self.assertTrue(expanded["external_development_rubric"]
                        ["correct_sounding_but_incomplete_evidence"])
        self.assertFalse(expanded["external_development_rubric"]
                         ["evidence_supported_provisional_label"])
        self.assertTrue(full["external_development_rubric"]
                        ["evidence_supported_provisional_label"])

    def test_equal_per_case_budget_and_exact_character_measure(self):
        for case_id, case in self.cases_by_id.items():
            documents = _case_documents(self.fixture, case)
            source_by_id = {d["id"]: d for d in documents}
            for arm in STRATEGIES:
                with self.subTest(case_id=case_id, arm=arm):
                    selected = self.row(case_id, arm)["selection"]
                    self.assertEqual(selected["budget_characters"], case["max_chars"])
                    self.assertLessEqual(selected["read_characters"], case["max_chars"])
                    self.assertEqual(selected["read_characters"], sum(
                        len(source_by_id[k]["body"]) for k in selected["source_ids"]
                    ))
                    self.assertEqual(selected["source_count"], len(
                        set(selected["source_ids"])
                    ))

    def test_oracle_changes_grading_not_retrieval(self):
        case = self.cases_by_id["CTX02"]
        documents = _case_documents(self.fixture, case)
        selected = select_context(documents, self.fixture, case, "dependency_expand")
        copied = deepcopy(self.gold_by_id["CTX02"])
        copied["expected_provisional_hypothesis"] = "producer-duplicates"
        copied["decisive_sources"] = ["worker-guide-r0"]
        again = select_context(documents, self.fixture, case, "dependency_expand")
        self.assertEqual(selected["source_ids"], again["source_ids"])
        reader = common_annotated_reader(
            selected["source_records"], self.fixture["hypotheses"],
            self.fixture["current_revision"],
        )
        first = evaluate_selected(case, self.gold_by_id["CTX02"], selected, reader)
        altered = evaluate_selected(case, copied, again, reader)
        self.assertNotEqual(first["provisional_label_matches_fixture"],
                            altered["provisional_label_matches_fixture"])

    def test_common_reader_matches_original_toy_ranking(self):
        case = self.cases_by_id["CTX01"]
        documents = _case_documents(self.fixture, case)
        nav = ContextNavigator(
            documents, current_revision=self.fixture["current_revision"],
            issue_tags=self.fixture["issue_tags"], max_chars=case["max_chars"],
        )
        nav.navigate(sector="worker", perspective="reliability",
                     depth="focused", reason="comparison parity")
        reader = common_annotated_reader(
            [nav.documents[x["id"]] for x in nav.context()],
            self.fixture["hypotheses"], self.fixture["current_revision"],
        )
        original = nav.assess(self.fixture["hypotheses"])
        self.assertEqual(reader["annotated_heuristic_scores"],
                         original["illustrative_scores"])
        self.assertEqual(reader["provisional_hypothesis"],
                         original["leading_hypothesis"])

    def test_provisional_proxy_not_final_agent_grade(self):
        for row in run_comparison()["results"]:
            self.assertEqual(row["reader"]["decision_status"],
                             "PROVISIONAL_REQUIRES_EXTERNAL_TEST")
            self.assertFalse(row["external_development_rubric"]
                             ["actual_agent_decision_quality_measured"])
            self.assertFalse(row["external_development_rubric"]
                             ["invalid_final_completion_assessed"])

    def test_determinism_and_input_digests(self):
        first = json.dumps(run_comparison(), sort_keys=True)
        second = json.dumps(run_comparison(), sort_keys=True)
        self.assertEqual(first, second)
        hashes = run_comparison()["source_identity_sha256"]
        self.assertEqual(len(hashes), 3)
        for value in hashes.values():
            self.assertEqual(len(value), 64)
            self.assertTrue(all(char in "0123456789abcdef" for char in value))

    def test_full_corpus_refuses_oversized_budget_without_truncation(self):
        case = deepcopy(self.cases_by_id["CTX02"])
        case["max_chars"] = 10
        docs = _case_documents(self.fixture, case)
        with self.assertRaises(NavigationError):
            select_context(docs, self.fixture, case, "full_corpus")
        partial = select_context(docs, self.fixture, case, "local_sector")
        self.assertEqual(partial["read_characters"], 0)

    def test_unknown_arm_is_rejected(self):
        case = self.cases_by_id["CTX02"]
        with self.assertRaises(ValueError):
            select_context(self.fixture["documents"], self.fixture, case,
                           "oracle-guided")

    def test_results_report_chars_not_tokens_or_llm_productivity(self):
        output = run_comparison()
        self.assertTrue(output["no_real_agent_quality_or_token_savings_claim"])
        self.assertIn("exclude metadata", output["interpretation"])
        for row in output["summary"]:
            self.assertIn("total_source_body_characters_read", row)
            self.assertNotIn("tokens_saved", row)
            self.assertNotIn("agent_valid_completion_rate", row)

    def test_source_order_does_not_change_results(self):
        fixture = deepcopy(self.fixture)
        fixture["documents"].reverse()
        a = run_comparison()
        b = run_comparison(fixture, self.cases, self.oracle)
        for x, y in zip(a["results"], b["results"]):
            self.assertEqual(x["selection"]["source_ids"],
                             y["selection"]["source_ids"])
            self.assertEqual(x["external_development_rubric"],
                             y["external_development_rubric"])

    def test_missing_dependency_variation_is_shared_by_arms(self):
        case = self.cases_by_id["CTX03"]
        documents = _case_documents(self.fixture, case)
        worker = next(d for d in documents if d["id"] == "worker-guide-r0")
        self.assertEqual(worker["depends_on"], [])
        for arm in STRATEGIES:
            self.assertIn("worker-guide-r0",
                          select_context(documents, self.fixture, case, arm)["source_ids"])

    def test_public_oracle_is_not_a_hidden_real_agent_benchmark(self):
        result = run_comparison()
        self.assertEqual(result["status"], "DETERMINISTIC_PUBLIC_FIXTURE_NO_LLM")
        self.assertTrue(result["public_oracle_not_held_out"])
        self.assertEqual(result["scope"],
                         "synthetic_retrieval_coverage_and_annotated_reader_proxy")


if __name__ == "__main__":
    unittest.main()
