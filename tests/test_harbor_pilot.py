"""Deterministic gates for a planned Harbor experiment, not a benchmark run."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from workcoord_lab.harbor_pilot import (
    DEFAULT_PATH, ProtocolError, task_fingerprint, validate_protocol,
    summarize_trials,
)


def frozen() -> dict:
    p = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
    p["status"] = "FROZEN"
    p["benchmark"]["harbor_git_commit"] = "a" * 40
    p["benchmark"]["dataset_git_commit"] = "b" * 40
    p["benchmark"]["task_splits"] = {
        "smoke": ["example/smoke"],
        "exploratory": ["example/t1", "example/t2"],
        "confirmatory": ["example/confirm"],
    }
    p["execution"]["common_model_id"] = "example/model-id"
    p["execution"]["agent_adapter_commits"] = {
        "A": "c" * 40, "B": "d" * 40, "C": "e" * 40,
    }
    p["execution"]["total_cost_ceiling_usd"] = 100.0
    p["execution"]["per_trial_cost_ceiling_usd"] = 10.0
    p["publication"]["human_ip_and_confidentiality_review_approved"] = True
    p["publication"]["license_decided"] = True
    p["benchmark"]["task_manifest_sha256"] = task_fingerprint(p)
    return p


def row(task_id, arm, verifier, cost, *,
        end="DONE", invalid=0, blocked=0, avoidable=0,
        adjudicated=True) -> dict:
    return {
        "task_id": task_id, "arm": arm, "attempt": 1,
        "verifier_status": verifier, "agent_end_status": end,
        "cost_usd": cost, "wall_seconds": 100.0,
        "input_tokens": 1000, "output_tokens": 100,
        "invalid_completion_attempts": invalid if adjudicated else None,
        "gate_blocked_invalid_attempts": blocked if adjudicated else None,
        "avoidable_holds": avoidable if adjudicated else None,
        "independent_adjudication": adjudicated,
    }


def sample_rows() -> list:
    return [
        row("example/t1", "A", "PASS", 1.0),
        row("example/t2", "A", "FAIL", 2.0, invalid=1),
        row("example/t1", "B", "PASS", 2.0),
        row("example/t2", "B", "PASS", 2.0),
        row("example/t1", "C", "PASS", 3.0),
        row("example/t2", "C", "NOT_RUN", 3.0, end="HOLD",
            invalid=1, blocked=1, avoidable=1),
    ]


class HarborPilotProtocolTests(unittest.TestCase):
    def test_public_protocol_is_draft_and_does_not_claim_real_runs(self):
        p = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        result = validate_protocol(p)
        self.assertEqual(result["status"], "DRAFT_UNFROZEN")
        self.assertFalse(result["ready_for_model_execution"])
        self.assertEqual(result["task_counts"], {
            "smoke": 0, "exploratory": 0, "confirmatory": 0,
        })
        self.assertFalse(p["publication"]["merge_approved"])
        self.assertFalse(p["publication"]["benchmark_confirmatory_results_present"])

    def test_draft_cannot_contain_unsealed_tasks(self):
        p = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        p["benchmark"]["task_splits"]["exploratory"].append("example/t1")
        with self.assertRaises(ProtocolError):
            validate_protocol(p)

    def test_frozen_contract_requires_all_three_arms_and_same_limits(self):
        p = frozen()
        self.assertTrue(validate_protocol(p)["ready_for_model_execution"])
        self.assertEqual([x["agent_count"] for x in p["arms"]], [1, 2, 2])
        self.assertEqual([x["governance"] for x in p["arms"]],
                         ["none", "basic", "workcoord"])
        self.assertTrue(all(p["parity"].values()))

    def test_tampered_manifest_detected(self):
        p = frozen()
        p["benchmark"]["task_splits"]["exploratory"][1] = "example/changed"
        with self.assertRaises(ProtocolError):
            validate_protocol(p)

    def test_missing_frozen_dataset_or_harness_commit_rejected(self):
        for field in ("dataset_git_commit", "harbor_git_commit"):
            p = frozen()
            p["benchmark"][field] = None
            with self.subTest(field=field), self.assertRaises(ProtocolError):
                validate_protocol(p)

    def test_unreviewed_or_unlicensed_protocol_cannot_freeze(self):
        for key in ("human_ip_and_confidentiality_review_approved",
                    "license_decided"):
            p = frozen()
            p["publication"][key] = False
            with self.subTest(key=key), self.assertRaises(ProtocolError):
                validate_protocol(p)

    def test_empty_confirmatory_or_smoke_split_rejected(self):
        for split in ("smoke", "exploratory", "confirmatory"):
            p = frozen()
            p["benchmark"]["task_splits"][split] = []
            p["benchmark"]["task_manifest_sha256"] = task_fingerprint(p)
            with self.subTest(split=split), self.assertRaises(ProtocolError):
                validate_protocol(p)

    def test_wildcard_glob_or_cross_split_duplicate_rejected(self):
        p = frozen()
        p["benchmark"]["task_splits"]["exploratory"] = ["example/*"]
        p["benchmark"]["task_manifest_sha256"] = task_fingerprint(p)
        with self.assertRaises(ProtocolError):
            validate_protocol(p)
        p = frozen()
        p["benchmark"]["task_splits"]["confirmatory"] = ["example/t1"]
        p["benchmark"]["task_manifest_sha256"] = task_fingerprint(p)
        with self.assertRaises(ProtocolError):
            validate_protocol(p)

    def test_parity_must_be_declared_for_external_scoring(self):
        p = frozen()
        p["parity"]["same_external_verifier"] = False
        with self.assertRaises(ProtocolError):
            validate_protocol(p)

    def test_second_arm_cannot_silently_become_one_agent(self):
        p = frozen()
        p["arms"][1]["agent_count"] = 1
        with self.assertRaises(ProtocolError):
            validate_protocol(p)

    def test_freeze_requires_model_adapter_commits_and_spending_caps(self):
        mutations = [
            ("common_model_id", None),
            ("total_cost_ceiling_usd", None),
            ("per_trial_cost_ceiling_usd", 1000.0),
            ("max_concurrent_trials", 0),
        ]
        for key, value in mutations:
            p = frozen()
            p["execution"][key] = value
            with self.subTest(key=key), self.assertRaises(ProtocolError):
                validate_protocol(p)

    def test_unfrozen_protocol_cannot_be_scored_as_real_data(self):
        p = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        with self.assertRaises(ProtocolError):
            summarize_trials(p, [])

    def test_gate_block_rejection_not_success(self):
        summary = summarize_trials(frozen(), sample_rows())
        self.assertEqual(summary["per_arm"]["C"]["externally_verified_successes"], 1)
        self.assertEqual(summary["per_arm"]["C"]["intention_to_treat_success_rate"], 0.5)
        self.assertEqual(
            summary["per_arm"]["C"]["independently_adjudicated_blocked_invalid_attempts"],
            1,
        )
        self.assertEqual(summary["per_arm"]["C"]["independently_adjudicated_invalid_attempts"], 1)
        self.assertEqual(summary["per_arm"]["C"]["independently_adjudicated_avoidable_holds"], 1)

    def test_synthetic_counterexample_governance_carries_net_overhead(self):
        s = summarize_trials(frozen(), sample_rows())["per_arm"]
        self.assertEqual(s["B"]["externally_verified_successes"], 2)
        self.assertEqual(s["C"]["externally_verified_successes"], 1)
        self.assertEqual(s["B"]["cost_per_external_success_usd"], 2.0)
        self.assertEqual(s["C"]["cost_per_external_success_usd"], 6.0)
        self.assertGreater(s["C"]["cost_per_external_success_usd"],
                           s["B"]["cost_per_external_success_usd"])

    def test_failed_attempt_costs_included(self):
        s = summarize_trials(frozen(), sample_rows())["per_arm"]
        self.assertEqual(s["A"]["total_observed_cost_usd"], 3.0)
        self.assertEqual(s["A"]["cost_per_external_success_usd"], 3.0)
        self.assertEqual(s["C"]["total_observed_cost_usd"], 6.0)

    def test_harness_errors_counted_as_nonsuccess(self):
        data = sample_rows()
        target = next(x for x in data if x["arm"] == "A" and x["task_id"] == "example/t2")
        target["verifier_status"] = "HARNESS_ERROR"
        target["agent_end_status"] = "NO_RESULT"
        s = summarize_trials(frozen(), data)["per_arm"]["A"]
        self.assertEqual(s["assigned_attempts"], 2)
        self.assertEqual(s["harness_errors_counted_as_nonsuccess"], 1)
        self.assertEqual(s["externally_verified_successes"], 1)
        self.assertEqual(s["intention_to_treat_success_rate"], 0.5)

    def test_missing_rows_not_success(self):
        data = [r for r in sample_rows()
                if not (r["arm"] == "A" and r["task_id"] == "example/t2")]
        s = summarize_trials(frozen(), data)["per_arm"]["A"]
        self.assertEqual(s["missing_attempts_counted_as_nonsuccess"], 1)
        self.assertEqual(s["assigned_attempts"], 2)
        self.assertEqual(s["externally_verified_successes"], 1)
        self.assertEqual(s["intention_to_treat_success_rate"], 0.5)
        self.assertIsNone(s["total_observed_cost_usd"])
        self.assertIsNone(s["cost_per_external_success_usd"])

    def test_unknown_cost_does_not_imply_zero(self):
        data = sample_rows()
        data[0]["cost_usd"] = None
        s = summarize_trials(frozen(), data)["per_arm"]["A"]
        self.assertFalse(s["cost_coverage_complete"])
        self.assertIsNone(s["total_observed_cost_usd"])
        self.assertIsNone(s["cost_per_external_success_usd"])

    def test_zero_success_never_produces_cost_per_success(self):
        data = sample_rows()
        for r in data:
            if r["arm"] == "C":
                r["verifier_status"] = "FAIL"
        s = summarize_trials(frozen(), data)["per_arm"]["C"]
        self.assertEqual(s["externally_verified_successes"], 0)
        self.assertEqual(s["total_observed_cost_usd"], 6.0)
        self.assertIsNone(s["cost_per_external_success_usd"])

    def test_no_adjudication_does_not_look_like_no_false_completion(self):
        data = sample_rows()
        for r in data:
            if r["arm"] == "B":
                r["independent_adjudication"] = False
                for k in ("invalid_completion_attempts",
                          "gate_blocked_invalid_attempts", "avoidable_holds"):
                    r[k] = None
        result = summarize_trials(frozen(), data)["per_arm"]["B"]
        self.assertFalse(result["independent_adjudication_complete"])
        self.assertIsNone(result["independently_adjudicated_invalid_attempts"])
        self.assertIsNone(result["independently_adjudicated_avoidable_holds"])

    def test_raw_trajectory_and_secrets_rejected(self):
        rows = sample_rows()
        rows[0]["OPENAI_API_KEY"] = "SECRET_VALUE_NOT_REAL"
        with self.assertRaises(ProtocolError):
            summarize_trials(frozen(), rows)

    def test_duplicate_normalized_trial_rejected(self):
        rows = sample_rows()
        rows.append(deepcopy(rows[0]))
        with self.assertRaises(ProtocolError):
            summarize_trials(frozen(), rows)

    def test_wrong_split_or_unknown_task_rejected(self):
        rows = sample_rows()
        rows[0]["task_id"] = "example/private-unknown"
        with self.assertRaises(ProtocolError):
            summarize_trials(frozen(), rows)

    def test_wrong_external_verifier_and_agent_end_separated(self):
        rows = sample_rows()
        rows[0]["verifier_status"] = "APPROVED_BY_WORKCOORD"
        with self.assertRaises(ProtocolError):
            summarize_trials(frozen(), rows)

    def test_blocked_invalid_attempts_cannot_exceed_invalid_claims(self):
        rows = sample_rows()
        rows[-1]["invalid_completion_attempts"] = 0
        with self.assertRaises(ProtocolError):
            summarize_trials(frozen(), rows)

    def test_summary_is_deterministic_and_does_not_claim_actual_data(self):
        p, rows = frozen(), sample_rows()
        first, again = summarize_trials(p, rows), summarize_trials(p, deepcopy(rows))
        self.assertEqual(first, again)
        self.assertEqual(first["schema"], "workcoord.harbor-pilot-scoring/v0")
        self.assertFalse(first["real_world_outcomes_authenticated_by_this_code"])
        self.assertEqual(first["task_manifest_sha256"],
                         p["benchmark"]["task_manifest_sha256"])


if __name__ == "__main__":
    unittest.main()
