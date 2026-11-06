"""Adversarial stdlib tests for public, fictional source and claim genealogy.

No real data, independent model/agent study, or production permissions.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from workcoord_lab.knowledge_genealogy import (
    CURRENT, GenealogyError, ZERO_HASH, evaluate_actions, replay_events,
    seal_actions, verify_chain,
)
from workcoord_lab.knowledge_genealogy_suite import run_suite

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "examples" / "knowledge-genealogy-cases-v0.json"


class KnowledgeGenealogyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.cases = {case["case_id"]: case for case in catalog["cases"]}

    def actions(self, case_id="KG01"):
        return deepcopy(self.cases[case_id]["actions"])

    def checkpoint(self, case_id="KG01", at_seq=None):
        return evaluate_actions(self.actions(case_id), at_seq=at_seq)

    def statuses(self, case_id, at_seq=None):
        return {item["id"]: item["status"]
                for item in self.checkpoint(case_id, at_seq)["claims"]}

    def add(self, actions, kind, data, *, tick=None, name=None):
        number = len(actions) + 1
        actions.append({
            "id": name if name is not None else "e" + str(number).zfill(2),
            "tick": number if tick is None else tick,
            "kind": kind, "data": data,
        })
        return actions

    def test_public_synthetic_catalog_and_sha_receipt(self):
        receipt = run_suite()
        self.assertEqual(receipt["case_count"], 19)
        self.assertEqual(receipt["expectations_met"], 19)
        self.assertEqual(len(receipt["catalog_sha256"]), 64)
        self.assertFalse(receipt["real_world_source_authentication"])
        self.assertFalse(receipt["real_agent_learning_measured"])
        self.assertFalse(receipt["external_causal_validation"])
        self.assertEqual(json.dumps(receipt, sort_keys=True),
                         json.dumps(run_suite(), sort_keys=True))

    def test_every_published_case_matches_declared_development_labels(self):
        self.assertEqual(len(self.cases), 19)
        for case_id, case in self.cases.items():
            with self.subTest(case=case_id):
                self.assertEqual(self.statuses(case_id),
                                 case["expected_status_by_claim"])
                for cut in case["at_seq_checks"]:
                    self.assertEqual(self.statuses(case_id, cut["at_seq"]),
                                     cut["status_by_claim"])

    def test_initial_fictional_review_is_advisory_only(self):
        r = self.checkpoint("KG01")
        self.assertEqual(self.statuses("KG01"), {"cause": CURRENT})
        self.assertEqual(r["knowledge_promotion"], "NOT_GRANTED")
        self.assertFalse(r["independent_scientific_validation"])
        self.assertFalse(r["external_source_authenticity_verified"])
        self.assertEqual(r["work_ownership"], "NOT_ASSIGNED")
        self.assertEqual(r["execution_authority"], "NONE")
        self.assertFalse(r["model_learning_or_training_performed"])

    def test_original_status_can_be_reconstructed_at_historical_cut(self):
        self.assertEqual(self.statuses("KG02", 4), {"cause": CURRENT})
        self.assertEqual(self.statuses("KG02", 6),
                         {"cause": "HOLD_STALE_BASIS"})
        self.assertEqual(self.checkpoint("KG02", 4)["event_count"], 4)
        self.assertNotEqual(self.checkpoint("KG02", 4)["prefix_head_sha256"],
                            self.checkpoint("KG02", 6)["prefix_head_sha256"])

    def test_new_registration_alone_does_not_supersede(self):
        r = self.checkpoint("KG12")
        self.assertEqual(r["claims"][0]["status"], CURRENT)
        versions = r["lineages"][0]["versions"]
        self.assertEqual([v["state"] for v in versions],
                         ["ACTIVE", "STAGED"])
        self.assertEqual(r["lineages"][0]["active_source_id"], "worker-r1")

    def test_supersession_invalidates_review_even_when_same_content(self):
        stale = self.checkpoint("KG15")
        self.assertEqual(stale["claims"][0]["status"], "HOLD_STALE_BASIS")
        versions = stale["lineages"][0]["versions"]
        self.assertEqual(versions[0]["body_sha256"],
                         versions[1]["body_sha256"])
        self.assertNotEqual(versions[0]["revision"], versions[1]["revision"])
        self.assertEqual([s["state"] for s in versions],
                         ["SUPERSEDED", "ACTIVE"])

    def test_old_source_is_retained_and_stale_review_explicit(self):
        r = self.checkpoint("KG02")
        self.assertEqual(len(r["observations"]), 1)
        self.assertEqual(r["observations"][0]["source_id"], "worker-r1")
        self.assertFalse(r["observations"][0]["currently_applicable"])
        self.assertIn("worker-support",
                      r["claims"][0]["current_review_basis_ids"])

    def test_new_support_without_explicit_review_never_restores(self):
        self.assertEqual(self.statuses("KG18"),
                         {"cause": "HOLD_STALE_BASIS"})
        self.assertEqual(self.statuses("KG03", 7),
                         {"cause": "HOLD_STALE_BASIS"})

    def test_fresh_bounded_rereview_restores_advisory_not_validation(self):
        r = self.checkpoint("KG03")
        self.assertEqual(self.statuses("KG03"), {"cause": CURRENT})
        self.assertEqual(r["claims"][0]["current_review_basis_ids"],
                         ["worker-new-support"])
        self.assertFalse(r["independent_scientific_validation"])
        self.assertEqual(len(r["observations"]), 2)
        self.assertFalse(r["observations"][0]["currently_applicable"])

    def test_current_challenge_prevents_majority_based_acceptance(self):
        self.assertEqual(self.statuses("KG04"),
                         {"cause": "HOLD_COUNTEREVIDENCE"})
        a = self.actions("KG04")
        self.add(a, "REVIEW_ACCEPT", {
            "claim_id": "cause", "basis_ids": ["worker-support"],
            "review_note": "Ignore the adverse observation (must fail).",
        })
        with self.assertRaises(GenealogyError):
            evaluate_actions(a)

    def test_retraction_does_not_automatically_reactivate_acceptance(self):
        self.assertEqual(self.statuses("KG05"),
                         {"cause": "HOLD_REVIEW_REQUIRED"})
        neg = next(x for x in self.checkpoint("KG05")["observations"]
                   if x["id"] == "negative-current")
        self.assertEqual(neg["retracted_seq"], 6)
        self.assertFalse(neg["currently_applicable"])
        self.assertTrue(neg["retraction_reason"])

    def test_retraction_plus_explicit_review_restores_and_keeps_negative(self):
        r = self.checkpoint("KG06")
        self.assertEqual(self.statuses("KG06"), {"cause": CURRENT})
        self.assertEqual(len(r["observations"]), 2)
        neg = next(x for x in r["observations"]
                   if x["id"] == "negative-current")
        self.assertEqual(neg["stance"], "CHALLENGE")
        self.assertEqual(neg["retracted_seq"], 6)
        self.assertTrue(neg["retraction_reason"])
        self.assertFalse(neg["currently_applicable"])

    def test_new_positive_observation_also_demands_reassessment(self):
        self.assertEqual(self.statuses("KG10"),
                         {"cause": "HOLD_REVIEW_REQUIRED"})

    def test_explicit_support_retraction_breaks_review_basis(self):
        self.assertEqual(self.statuses("KG11"),
                         {"cause": "HOLD_RETRACTED_BASIS"})

    def test_downstream_claim_is_blocked_when_parent_invalidated(self):
        r = self.checkpoint("KG07")
        self.assertEqual({c["id"]: c["status"] for c in r["claims"]},
                         {"cause": "HOLD_STALE_BASIS", "outcome": "HOLD_UPSTREAM"})
        self.assertEqual(self.statuses("KG07", 8),
                         {"cause": CURRENT, "outcome": CURRENT})

    def test_parent_restoration_does_not_silently_restore_child(self):
        self.assertEqual(self.statuses("KG08"),
                         {"cause": CURRENT, "outcome": "HOLD_UPSTREAM_REVIEW_CHANGED"})
        child = next(c for c in self.checkpoint("KG08")["claims"]
                     if c["id"] == "outcome")
        self.assertEqual(child["current_review_basis_ids"],
                         ["delivery-support"])

    def test_child_explicit_review_restores_only_after_new_parent_review(self):
        self.assertEqual(self.statuses("KG09", 12),
                         {"cause": CURRENT, "outcome": "HOLD_UPSTREAM_REVIEW_CHANGED"})
        self.assertEqual(self.statuses("KG09"),
                         {"cause": CURRENT, "outcome": CURRENT})

    def test_unrelated_source_update_leaves_other_claim_current(self):
        self.assertEqual(self.statuses("KG13"), {"cause": CURRENT})
        self.assertEqual(self.statuses("KG17"),
                         {"cause": "HOLD_STALE_BASIS", "other": CURRENT})

    def test_external_negative_observation_cannot_be_outvoted(self):
        r = self.checkpoint("KG14")
        self.assertEqual(r["claims"][0]["status"], "HOLD_COUNTEREVIDENCE")
        self.assertEqual(len(r["observations"]), 2)
        self.assertEqual({x["stance"] for x in r["observations"]},
                         {"SUPPORT", "CHALLENGE"})
        self.assertFalse(r["independent_scientific_validation"])

    def test_historical_retracted_counterevidence_never_disappears(self):
        r = self.checkpoint("KG19")
        self.assertEqual(len(r["observations"]), 2)
        neg = next(x for x in r["observations"]
                   if x["id"] == "negative-current")
        self.assertIsNotNone(neg["retracted_seq"])
        self.assertIn("worker-r1",
                      [v["source_id"] for v in r["lineages"][0]["versions"]])

    def test_unreviewed_claim_is_never_validated(self):
        self.assertEqual(self.statuses("KG16"),
                         {"cause": "HOLD_UNREVIEWED"})

    def test_transitions_record_invalidations_and_restorations(self):
        r = self.checkpoint("KG03")
        transitions = [x for x in r["transitions"] if x["claim_id"] == "cause"]
        self.assertEqual([x["to"] for x in transitions],
                         ["HOLD_UNREVIEWED", CURRENT, "HOLD_STALE_BASIS", CURRENT])
        self.assertEqual([x["seq"] for x in transitions], [2, 4, 6, 8])
        self.assertEqual(transitions[2]["from"], CURRENT)
        self.assertEqual(transitions[-1]["cause_event_id"], "e08")

    def test_chain_verifies_exact_sha_and_is_repeatable(self):
        actions = self.actions("KG03")
        a, b = seal_actions(actions), seal_actions(actions)
        self.assertEqual(a, b)
        self.assertEqual(verify_chain(a), a[-1]["event_sha256"])
        self.assertEqual(replay_events(a), replay_events(b))
        self.assertEqual(len(a[-1]["event_sha256"]), 64)

    def test_tampering_a_historical_event_breaks_hash_chain(self):
        sealed = seal_actions(self.actions("KG03"))
        tampered = deepcopy(sealed)
        tampered[0]["data"]["body"] = "Rewritten input without resealing."
        with self.assertRaises(GenealogyError):
            replay_events(tampered)

    def test_reordering_or_dropping_a_middle_event_rejected(self):
        sealed = seal_actions(self.actions("KG03"))
        swapped = deepcopy(sealed)
        swapped[2], swapped[3] = swapped[3], swapped[2]
        with self.assertRaises(GenealogyError):
            replay_events(swapped)
        with self.assertRaises(GenealogyError):
            replay_events(sealed[:2] + sealed[3:])

    def test_without_independent_head_anchor_tail_truncation_is_not_detectable(self):
        sealed = seal_actions(self.actions("KG03"))
        full = verify_chain(sealed)
        prefix = verify_chain(sealed[:-1])
        self.assertNotEqual(full, prefix)
        self.assertEqual(prefix, sealed[-2]["event_sha256"])
        self.assertFalse(self.checkpoint("KG03")["external_source_authenticity_verified"])

    def test_typed_contiguous_unique_events_required(self):
        actions = self.actions("KG01")
        actions[1]["tick"] = 0
        with self.assertRaises(GenealogyError):
            evaluate_actions(actions)
        actions = self.actions("KG01")
        actions[1]["id"] = actions[0]["id"]
        with self.assertRaises(GenealogyError):
            evaluate_actions(actions)
        actions = self.actions("KG01")
        actions[0]["kind"] = "AUTO_VALIDATE"
        with self.assertRaises(GenealogyError):
            evaluate_actions(actions)

    def test_source_available_time_cannot_follow_registration(self):
        actions = self.actions("KG01")
        actions[0]["data"]["available_tick"] = 99
        with self.assertRaises(GenealogyError):
            evaluate_actions(actions)

    def test_future_source_registration_rejected_even_if_unreferenced(self):
        actions = self.actions("KG01")[:1]
        actions[0]["data"]["available_tick"] = 99
        with self.assertRaises(GenealogyError):
            evaluate_actions(actions)

    def test_cannot_supersede_across_unrelated_lineages(self):
        actions = self.actions("KG13")
        actions[-1]["data"]["old_source_id"] = "worker-r1"
        with self.assertRaises(GenealogyError):
            evaluate_actions(actions)

    def test_staged_revision_cannot_be_used_as_current_observation(self):
        actions = self.actions("KG12")
        self.add(actions, "OBSERVATION_ADD", {
            "observation_id": "stage-ineligible", "claim_id": "cause",
            "source_id": "worker-r2", "stance": "SUPPORT",
            "finding": "A staged file is not the current reference.",
        })
        with self.assertRaises(GenealogyError):
            evaluate_actions(actions)

    def test_superseded_revision_cannot_be_used_as_fresh_evidence(self):
        actions = self.actions("KG02")
        self.add(actions, "OBSERVATION_ADD", {
            "observation_id": "old-ineligible", "claim_id": "cause",
            "source_id": "worker-r1", "stance": "SUPPORT",
            "finding": "Historical notes are not current proof.",
        })
        with self.assertRaises(GenealogyError):
            evaluate_actions(actions)

    def test_duplicate_source_revision_and_source_id_rejected(self):
        for field, value in (
            ("source_id", "worker-r1"), ("revision", "r1")
        ):
            actions = self.actions("KG12")
            actions[-1]["data"][field] = value
            with self.subTest(field=field), self.assertRaises(GenealogyError):
                evaluate_actions(actions)

    def test_dependency_must_reference_preexisting_claim(self):
        actions = self.actions("KG16")
        actions[1]["data"]["depends_on"] = ["not-yet-open"]
        with self.assertRaises(GenealogyError):
            evaluate_actions(actions)
        actions = self.actions("KG16")
        actions[1]["data"]["depends_on"] = ["cause"]
        with self.assertRaises(GenealogyError):
            evaluate_actions(actions)

    def test_duplicate_claim_identifier_is_rejected(self):
        actions = self.actions("KG01")
        self.add(actions, "CLAIM_OPEN", {
            "claim_id": "cause", "statement": "Not a distinct claim.",
            "depends_on": [],
        })
        with self.assertRaises(GenealogyError):
            evaluate_actions(actions)

    def test_review_cannot_omit_a_current_supporting_observation(self):
        actions = self.actions("KG10")
        self.add(actions, "REVIEW_ACCEPT", {
            "claim_id": "cause", "basis_ids": ["worker-support"],
            "review_note": "Attempt to ignore newly selected active evidence.",
        })
        with self.assertRaises(GenealogyError):
            evaluate_actions(actions)

    def test_downstream_review_blocked_by_unreviewed_parent(self):
        actions = self.actions("KG07")[:8]
        # Add a current challenge to the parent before a new child review.
        self.add(actions, "OBSERVATION_ADD", {
            "observation_id": "new-challenge", "claim_id": "cause",
            "source_id": "worker-r1", "stance": "CHALLENGE",
            "finding": "The upstream is now contradicted.",
        })
        self.add(actions, "REVIEW_ACCEPT", {
            "claim_id": "outcome", "basis_ids": ["delivery-support"],
            "review_note": "Attempt to ignore upstream contradiction.",
        })
        with self.assertRaises(GenealogyError):
            evaluate_actions(actions)

    def test_retraction_of_same_finding_cannot_be_replayed_twice(self):
        actions = self.actions("KG05")
        self.add(actions, "OBSERVATION_RETRACT", {
            "observation_id": "negative-current",
            "reason": "Duplicate retraction must fail.",
        })
        with self.assertRaises(GenealogyError):
            evaluate_actions(actions)

    def test_reviewer_cannot_accept_empty_basis(self):
        actions = self.actions("KG16")
        self.add(actions, "REVIEW_ACCEPT", {
            "claim_id": "cause", "basis_ids": [],
            "review_note": "Attempted proof with no evidence.",
        })
        with self.assertRaises(GenealogyError):
            evaluate_actions(actions)

    def test_unexpected_event_fields_do_not_silently_gain_authority(self):
        actions = self.actions("KG01")
        actions[0]["data"]["execution_authorization"] = "APPROVED"
        with self.assertRaises(GenealogyError):
            evaluate_actions(actions)

    def test_malformed_values_fail_closed(self):
        for field, value in (("tick", True), ("tick", -1),
                             ("data", []), ("kind", ["SOURCE_ADD"])):
            actions = self.actions("KG01")
            actions[0][field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaises(GenealogyError):
                    evaluate_actions(actions)
        with self.assertRaises(GenealogyError):
            replay_events(seal_actions(self.actions("KG01")), at_seq=True)

    def test_status_is_never_equivalent_to_production_approval(self):
        checkpoint = self.checkpoint("KG09")
        self.assertEqual(checkpoint["execution_authority"], "NONE")
        self.assertEqual(checkpoint["knowledge_promotion"], "NOT_GRANTED")
        self.assertFalse(checkpoint["independent_scientific_validation"])
        self.assertFalse(checkpoint["model_learning_or_training_performed"])

    def test_unchanged_action_inputs_and_no_gold_oracle_access(self):
        actions = self.actions("KG03")
        untouched = deepcopy(actions)
        first = evaluate_actions(actions)
        self.assertEqual(actions, untouched)
        self.assertEqual(first, evaluate_actions(actions))
        case = self.cases["KG03"]
        fake_label = deepcopy(case)
        fake_label["expected_status_by_claim"] = {"cause": "HOLD_COUNTEREVIDENCE"}
        self.assertEqual(evaluate_actions(fake_label["actions"]), first)


if __name__ == "__main__":
    unittest.main()
