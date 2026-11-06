"""Sector/perspective/depth navigation with explicit provenance and negative cases."""
import copy
import unittest
from workcoord_lab.intelligence import ContextNavigator, NavigationError
from workcoord_lab.intelligence_demo import fixture, run


class IntelligenceNavigationTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()

    def nav(self, max_chars=1600):
        return ContextNavigator(self.data["documents"],
                                current_revision=self.data["current_revision"],
                                issue_tags=self.data["issue_tags"], max_chars=max_chars)

    def test_initial_stale_validated_note_is_not_current_authority(self):
        nav = self.nav()
        step = nav.navigate(sector="worker", perspective="reliability", depth="overview",
                            reason="investigate first sector")
        self.assertEqual(step["new_sources"], ["worker-guide-r0"])
        first = nav.assess(self.data["hypotheses"])
        self.assertEqual(first["leading_hypothesis"], "producer-duplicates")
        self.assertEqual(first["status"], "PROVISIONAL_INVESTIGATION_ONLY")
        self.assertIn("worker-guide-r0", first["old_revision_sources"])
        self.assertFalse(nav.context()[0]["validated_for_current_revision"])
        self.assertIn("queue", step["gaps"]["dependency_sectors_not_visited"])

    def test_cross_sector_contradiction_revises_investigation(self):
        result = run()
        first = result["initial"]["assessment"]
        revised = result["after_queue_expansion"]["assessment"]
        final = result["after_api_crosscheck"]["assessment"]
        self.assertEqual(first["leading_hypothesis"], "producer-duplicates")
        self.assertEqual(revised["leading_hypothesis"], "ack-retry")
        self.assertEqual(final["leading_hypothesis"], "ack-retry")
        self.assertTrue(any(c["hypothesis"] == "producer-duplicates"
                            for c in final["conflicts"]))
        conflict = next(c for c in final["conflicts"]
                        if c["hypothesis"] == "producer-duplicates")
        self.assertIn("worker-guide-r0", conflict["supports"])
        self.assertIn("queue-ack-r2", conflict["contradicts"])
        self.assertIn("api-events-r2", conflict["contradicts"])
        self.assertIn("worker-guide-r0", final["source_ids"])
        self.assertEqual(result["resolution"], "HOLD_FOR_INDEPENDENT_TEST")
        self.assertFalse(result["external_validation_performed"])

    def test_observed_current_evidence_is_retrievable_not_promoted(self):
        nav = self.nav()
        nav.navigate(sector="queue", perspective="reliability", depth="focused",
                     reason="source check")
        context = {x["id"]: x for x in nav.context()}
        current = context["queue-ack-r2"]
        self.assertEqual(current["maturity"], "observed")
        self.assertTrue(current["current_revision"])
        self.assertFalse(current["validated_for_current_revision"])
        self.assertEqual(current["source_role"], "investigation_only")

    def test_perspective_changes_selected_sources(self):
        nav = self.nav()
        perf = nav.navigate(sector="worker", perspective="performance", depth="overview",
                            reason="performance question")
        self.assertEqual(perf["new_sources"], ["worker-throughput-r2"])
        reliability = nav.navigate(sector="worker", perspective="reliability",
                                   depth="overview", reason="reliability question")
        self.assertEqual(reliability["new_sources"], ["worker-guide-r0"])
        self.assertNotEqual(perf["new_sources"], reliability["new_sources"])

    def test_depth_controls_specificity(self):
        nav = self.nav()
        shallow = nav.navigate(sector="queue", perspective="reliability", depth="overview",
                               reason="overview")
        self.assertNotIn("queue-ack-r2", shallow["new_sources"])
        self.assertNotIn("queue-deep-r2", shallow["new_sources"])
        focused = nav.navigate(sector="queue", perspective="reliability", depth="focused",
                               reason="need direct trace")
        self.assertIn("queue-ack-r2", focused["new_sources"])
        self.assertNotIn("queue-deep-r2", focused["new_sources"])
        deep = nav.navigate(sector="queue", perspective="reliability", depth="deep",
                            reason="deep trace check")
        self.assertIn("queue-deep-r2", deep["new_sources"])

    def test_dependencies_are_suggestions_not_automatic_injections(self):
        nav = self.nav()
        step = nav.navigate(sector="worker", perspective="reliability",
                            depth="overview", reason="start")
        self.assertEqual(len(nav.context()), 1)
        self.assertIn("queue", step["gaps"]["dependency_sectors_not_visited"])
        self.assertNotIn("queue-ack-r2", step["new_sources"])

    def test_budget_exclusions_explicitly_include_contradictions(self):
        nav = self.nav(max_chars=1)
        step = nav.navigate(sector="queue", perspective="reliability", depth="focused",
                            reason="tiny budget")
        self.assertEqual(step["new_sources"], [])
        self.assertIn("queue-ack-r2", step["gaps"]["unread_due_to_budget"])
        self.assertIn("queue-ack-r2",
                      step["gaps"]["potential_counterevidence_unread"])
        self.assertEqual(step["cumulative_unique_chars"], 0)

    def test_source_costs_measured_in_characters_not_tokens(self):
        result = run()
        ctx = result["source_manifest"]
        self.assertEqual(result["unique_source_chars"], sum(
            len(x["body"]) for x in ctx
        ))
        self.assertGreater(result["relevant_corpus_chars"], result["unique_source_chars"])
        self.assertLessEqual(result["unique_source_chars"], 1600)
        self.assertEqual(result["remaining_budget_chars"],
                         1600 - result["unique_source_chars"])

    def test_repeat_navigation_does_not_double_count(self):
        nav = self.nav()
        nav.navigate(sector="worker", perspective="reliability", depth="overview",
                     reason="first")
        initial = nav.total_chars()
        second = nav.navigate(sector="worker", perspective="reliability", depth="overview",
                              reason="repeat")
        self.assertEqual(second["new_sources"], [])
        self.assertEqual(second["already_read"], ["worker-guide-r0"])
        self.assertEqual(nav.total_chars(), initial)

    def test_order_is_independent_of_input_order(self):
        nav1 = self.nav()
        data = copy.deepcopy(self.data["documents"])
        data.reverse()
        nav2 = ContextNavigator(data, current_revision="demo-r2",
                                issue_tags=["duplicate-notification"], max_chars=1600)
        a = nav1.navigate(sector="queue", perspective="reliability", depth="deep",
                          reason="replay")
        b = nav2.navigate(sector="queue", perspective="reliability", depth="deep",
                          reason="replay")
        self.assertEqual(a["new_sources"], b["new_sources"])

    def test_corpus_is_immutable_after_init(self):
        docs = copy.deepcopy(self.data["documents"])
        nav = ContextNavigator(docs, current_revision="demo-r2",
                               issue_tags=["duplicate-notification"], max_chars=1600)
        docs[0]["body"] = "tampered caller input"
        nav.navigate(sector="worker", perspective="reliability", depth="overview",
                     reason="protect snapshot")
        self.assertNotEqual(nav.context()[0]["body"], "tampered caller input")
        returned = nav.context()
        returned[0]["signals"]["producer-duplicates"] = "contradicts"
        self.assertEqual(nav.context()[0]["signals"]["producer-duplicates"], "supports")

    def test_irrelevant_issue_tag_never_selected(self):
        nav = self.nav()
        nav.navigate(sector="worker", perspective="reliability", depth="overview",
                     reason="ignore unrelated")
        self.assertNotIn("unrelated-worker-r2", [x["id"] for x in nav.context()])

    def test_no_matching_source_is_an_explicit_gap(self):
        nav = self.nav()
        x = nav.navigate(sector="fictional-missing", perspective="reliability",
                         depth="overview", reason="probe missing sector")
        self.assertTrue(x["gaps"]["no_matching_source"])
        self.assertEqual(x["new_sources"], [])

    def test_unknown_hypotheses_cannot_be_verified(self):
        nav = self.nav()
        x = nav.assess(["not-in-data"])
        self.assertIsNone(x["leading_hypothesis"])
        self.assertTrue(x["requires_independent_test"])
        self.assertEqual(x["status"], "PROVISIONAL_INVESTIGATION_ONLY")

    def test_rejects_duplicate_sources(self):
        docs = list(self.data["documents"]) + [copy.deepcopy(self.data["documents"][0])]
        with self.assertRaises(NavigationError):
            ContextNavigator(docs, current_revision="demo-r2",
                             issue_tags=["duplicate-notification"])

    def test_invalid_budget_and_input_are_rejected(self):
        for budget in (True, 0, -1):
            with self.subTest(budget=budget), self.assertRaises(NavigationError):
                self.nav(max_chars=budget)
        doc = copy.deepcopy(self.data["documents"][0])
        doc["maturity"] = "automatically_truthful"
        with self.assertRaises(NavigationError):
            ContextNavigator([doc], current_revision="demo-r2",
                             issue_tags=["duplicate-notification"])
        nav = self.nav()
        with self.assertRaises(NavigationError):
            nav.navigate(sector="queue", perspective="reliability", depth="ultra",
                         reason="unknown depth")

    def test_current_validated_is_marked_only_if_revision_matches(self):
        docs = copy.deepcopy(self.data["documents"])
        docs[0]["revision"] = "demo-r2"
        nav = ContextNavigator(docs, current_revision="demo-r2",
                               issue_tags=["duplicate-notification"], max_chars=1600)
        nav.navigate(sector="worker", perspective="reliability",
                     depth="overview", reason="test revision")
        current = {x["id"]: x for x in nav.context()}
        self.assertTrue(current["worker-guide-r0"]["validated_for_current_revision"])
        self.assertFalse(current["worker-guide-r0"]["source_role"] == "authorization")


if __name__ == "__main__":
    unittest.main()
