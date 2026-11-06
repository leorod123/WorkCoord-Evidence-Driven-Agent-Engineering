"""Offline, stdlib-only controls for a *planned* Harbor evaluation.

No Docker, Harbor, model/API requests or external services are started here.
The public protocol remains UNFROZEN. A future frozen manifest must seal exact
tasks, harness/dataset commits, common model and budgets before real runs.

All rows passed to summarize_trials are already NORMALIZED, sanitized, and
independently verified outside this module; it is not a Harbor result parser,
an independent oracle, an agent runner or an authorization system.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA = "workcoord.harbor-pilot-protocol/v0"
SUMMARY_SCHEMA = "workcoord.harbor-pilot-scoring/v0"
ARM_SPEC = (("A", 1, "none"), ("B", 2, "basic"),
            ("C", 2, "workcoord"))
SPLITS = ("smoke", "exploratory", "confirmatory")
STATES = ("DRAFT_UNFROZEN", "FROZEN")
VERIFIERS = {"PASS", "FAIL", "NOT_RUN", "HARNESS_ERROR"}
END_STATES = {"DONE", "HOLD", "TIMEOUT", "NO_RESULT"}
EXPECTED_ROW_FIELDS = {
    "task_id", "arm", "attempt", "verifier_status", "agent_end_status",
    "cost_usd", "wall_seconds", "input_tokens", "output_tokens",
    "invalid_completion_attempts", "gate_blocked_invalid_attempts",
    "avoidable_holds", "independent_adjudication",
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
TASK = re.compile(r"^[A-Za-z0-9_.:/-]+$")
DEFAULT_PATH = (
    Path(__file__).resolve().parents[2] / "evals" / "harbor-pilot-protocol-v0.json"
)


class ProtocolError(ValueError):
    """Fail-closed protocol state or normalized-results inconsistency."""


def _require(ok: bool, label: str) -> None:
    if not ok:
        raise ProtocolError("protocol constraint: " + label)


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def _nonneg(value: object) -> bool:
    return type(value) in (int, float) and value >= 0 and value < float("inf")


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _sha(obj: object) -> str:
    return hashlib.sha256(json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def task_fingerprint(p: dict) -> str:
    """Public manifest lock, NOT a cryptographic independent signature."""
    b = p["benchmark"]
    return _sha({
        "dataset": b["dataset"],
        "harbor_git_commit": b["harbor_git_commit"],
        "dataset_git_commit": b["dataset_git_commit"],
        "task_splits": b["task_splits"],
    })


def validate_protocol(p: dict) -> dict:
    _require(isinstance(p, dict), "object required")
    _require(set(p) == {
        "schema", "status", "claim", "benchmark", "arms", "parity",
        "execution", "analysis", "publication",
    }, "unexpected top-level protocol field")
    _require(p["schema"] == SCHEMA and p["status"] in STATES,
             "schema or state")
    _require(p["claim"] == "planned_external_evaluation_not_executed",
             "results are not implied by an experiment plan")
    b = p["benchmark"]
    _require(isinstance(b, dict) and set(b) == {
        "harness", "dataset", "environment", "harbor_git_commit",
        "dataset_git_commit", "task_manifest_sha256", "task_splits",
    }, "benchmark manifest fields")
    _require(b["harness"] == "Harbor"
             and b["dataset"] == "terminal-bench@2.0"
             and b["environment"] == "docker", "external harness and dataset")
    splits = b["task_splits"]
    _require(isinstance(splits, dict) and set(splits) == set(SPLITS),
             "smoke/exploratory/confirmatory splits")
    task_ids: list[str] = []
    for split in SPLITS:
        ids = splits[split]
        _require(isinstance(ids, list), split + " must be task IDs")
        _require(all(isinstance(x, str) and TASK.fullmatch(x)
                     and not x.startswith(("/", ".", "-")) for x in ids),
                 split + " has invalid or wildcard task ID")
        task_ids.extend(ids)
    _require(len(task_ids) == len(set(task_ids)),
             "task splits must be disjoint; no task is reused across phases")
    arms = p["arms"]
    _require(isinstance(arms, list) and len(arms) == 3, "exactly three arms")
    for row, (label, count, mode) in zip(arms, ARM_SPEC):
        _require(isinstance(row, dict) and set(row) == {
            "id", "name", "agent_count", "governance",
        }, "arm metadata fields")
        _require(row["id"] == label and type(row["agent_count"]) is int
                 and row["agent_count"] == count
                 and row["governance"] == mode
                 and _nonempty(row["name"]), "arm A/B/C design")
    parity = p["parity"]
    _require(isinstance(parity, dict) and set(parity) == {
        "same_base_model", "same_tool_access", "same_external_verifier",
        "same_assigned_task_set", "same_wall_clock_limit",
        "same_token_price_accounting",
    } and all(value is True for value in parity.values()),
             "all cross-arm comparison parity constraints must be declared")
    e = p["execution"]
    _require(isinstance(e, dict) and set(e) == {
        "common_model_id", "agent_adapter_commits", "attempts_per_task_arm",
        "wall_clock_limit_seconds", "total_cost_ceiling_usd",
        "per_trial_cost_ceiling_usd", "max_concurrent_trials",
        "task_filter_requires_exact_resolved_ids",
        "public_ci_must_not_run_agent", "allow_network_inside_tasks",
    }, "execution fields")
    _require(_positive(e["attempts_per_task_arm"])
             and _positive(e["wall_clock_limit_seconds"])
             and _positive(e["max_concurrent_trials"]),
             "attempt, clock and concurrency limits")
    _require(e["task_filter_requires_exact_resolved_ids"] is True
             and e["public_ci_must_not_run_agent"] is True
             and e["allow_network_inside_tasks"] == "must_match_dataset_rules",
             "do not permit task filter ambiguity, leaked credentials or unequal access")
    adapters = e["agent_adapter_commits"]
    _require(isinstance(adapters, dict) and set(adapters) == {"A", "B", "C"},
             "adapter lock IDs required for every arm")
    a = p["analysis"]
    _require(isinstance(a, dict) and set(a) == {
        "primary_outcome", "denominator", "cost_per_valid_outcome",
        "zero_pass_cost_per_valid_outcome", "unmeasured_cost_semantics",
        "harness_error_policy", "false_completion_attempt_policy",
        "avoidable_hold_policy", "multiple_comparisons",
    }, "analysis fields")
    _require(
        a["primary_outcome"] ==
        "externally_verified_pass_per_assigned_task_intention_to_treat"
        and a["denominator"] ==
        "every_frozen_task_arm_attempt_including_failure_timeout_hold_missing_and_harness_error"
        and a["cost_per_valid_outcome"] ==
        "all_attempt_costs_for_arm_including_failed_trials_divided_by_external_passes_only"
        and a["zero_pass_cost_per_valid_outcome"] is None
        and a["unmeasured_cost_semantics"] == "not_estimable"
        and a["harness_error_policy"] ==
        "count_as_not_pass_in_primary_and_separately_report_for_paired_sensitivity"
        and a["false_completion_attempt_policy"] ==
        "count_independently_adjudicated_attempts_even_if_workcoord_gate_blocks"
        and a["avoidable_hold_policy"] ==
        "count_only_when_independent_evaluator_labels_avoidable"
        and a["multiple_comparisons"] ==
        "exploratory_only_until_confirmatory_protocol_sealed",
        "analysis must not favor gate-only success or omit failed attempts")
    pub = p["publication"]
    _require(isinstance(pub, dict) and set(pub) == {
        "human_ip_and_confidentiality_review_approved", "license_decided",
        "merge_approved", "benchmark_confirmatory_results_present",
        "prohibit_raw_provider_traffic_or_secrets_in_git",
    } and all(type(x) is bool for x in pub.values())
             and pub["prohibit_raw_provider_traffic_or_secrets_in_git"],
             "publication and no-secrets declarations")

    if p["status"] == "DRAFT_UNFROZEN":
        _require(not task_ids and b["harbor_git_commit"] is None
                 and b["dataset_git_commit"] is None
                 and b["task_manifest_sha256"] is None
                 and e["common_model_id"] is None
                 and all(v is None for v in adapters.values())
                 and e["total_cost_ceiling_usd"] is None
                 and e["per_trial_cost_ceiling_usd"] is None,
                 "a partial benchmark setup cannot be treated as a valid draft")
        _require(not pub["benchmark_confirmatory_results_present"],
                 "unfrozen pilot cannot report confirmatory results")
    else:
        _require(all(splits[split] for split in SPLITS),
                 "frozen protocol must name nonempty, disjoint task splits")
        _require(all(isinstance(b[k], str) and HEX40.fullmatch(b[k])
                     for k in ("harbor_git_commit", "dataset_git_commit")),
                 "immutable source commits for harness and tasks")
        _require(b["task_manifest_sha256"] == task_fingerprint(p),
                 "task manifest SHA-256 must match exact task IDs and commits")
        _require(_nonempty(e["common_model_id"])
                 and not any(c.isspace() for c in e["common_model_id"]),
                 "common model must be pinned")
        _require(all(isinstance(v, str) and HEX40.fullmatch(v)
                     for v in adapters.values()),
                 "each agent adapter must pin an immutable commit")
        _require(_nonneg(e["total_cost_ceiling_usd"])
                 and e["total_cost_ceiling_usd"] > 0
                 and _nonneg(e["per_trial_cost_ceiling_usd"])
                 and e["per_trial_cost_ceiling_usd"] > 0
                 and e["per_trial_cost_ceiling_usd"] <= e["total_cost_ceiling_usd"],
                 "positive experiment and per-trial spending caps")
        _require(pub["human_ip_and_confidentiality_review_approved"]
                 and pub["license_decided"],
                 "human prepublication review and licensing block freezing")
    return {
        "schema": SCHEMA,
        "status": p["status"],
        "ready_for_model_execution": p["status"] == "FROZEN",
        "task_counts": {split: len(splits[split]) for split in SPLITS},
        "task_manifest_sha256": b["task_manifest_sha256"],
        "warning": "Protocol validation is not model execution, external result verification or public release authorization.",
    }


def _validate_trial(r: dict, allowed_tasks: set, max_attempts: int) -> None:
    _require(isinstance(r, dict) and set(r) == EXPECTED_ROW_FIELDS,
             "normalized trial must have safe allowlisted fields only")
    _require(r["task_id"] in allowed_tasks
             and r["arm"] in {"A", "B", "C"}
             and type(r["attempt"]) is int
             and 1 <= r["attempt"] <= max_attempts,
             "trial must belong to assigned task/arm/attempt")
    _require(r["verifier_status"] in VERIFIERS
             and r["agent_end_status"] in END_STATES,
             "external verdict and agent declaration are separate")
    for key in ("cost_usd", "wall_seconds", "input_tokens", "output_tokens"):
        val = r[key]
        _require(val is None or (
            _nonneg(val) if key in ("cost_usd", "wall_seconds")
            else type(val) is int and val >= 0
        ), "invalid measured trial cost/time/tokens")
    _require(type(r["independent_adjudication"]) is bool,
             "adjudication marker must be bool")
    for key in ("invalid_completion_attempts", "gate_blocked_invalid_attempts",
                "avoidable_holds"):
        val = r[key]
        _require(
            (type(val) is int and val >= 0) if r["independent_adjudication"]
            else val is None,
            "unreviewed invalid claims and avoidable HOLDs must be unknown, not zero",
        )
    if r["independent_adjudication"]:
        _require(r["gate_blocked_invalid_attempts"] <= r["invalid_completion_attempts"],
                 "gate-blocked invalid attempts cannot exceed invalid attempts")
    if r["verifier_status"] == "HARNESS_ERROR":
        _require(r["agent_end_status"] == "NO_RESULT",
                 "infrastructure errors cannot masquerade as agent outcomes")


def summarize_trials(p: dict, rows: list, *, split: str = "exploratory") -> dict:
    """Intention-to-treat; missing/error/abstaining attempts NEVER disappear.

    This is arithmetic over *externally normalized* rows, not a verifier.
    The same externally assigned task set is used for all three arms.
    """
    validate_protocol(p)
    _require(p["status"] == "FROZEN", "cannot score unfrozen or invented benchmark runs")
    _require(split in SPLITS, "unknown split")
    _require(isinstance(rows, list), "normalized rows must be an array")
    tasks = set(p["benchmark"]["task_splits"][split])
    attempts = p["execution"]["attempts_per_task_arm"]
    seen = {}
    for r in rows:
        _validate_trial(r, tasks, attempts)
        key = (r["task_id"], r["arm"], r["attempt"])
        _require(key not in seen, "duplicated task/arm/attempt trial")
        seen[key] = r

    report = {}
    for arm, _, _ in ARM_SPEC:
        assigned = len(tasks) * attempts
        observed = [r for key, r in seen.items() if key[1] == arm]
        success = sum(r["verifier_status"] == "PASS" for r in observed)
        error = sum(r["verifier_status"] == "HARNESS_ERROR" for r in observed)
        missed = assigned - len(observed)
        # A failure or HOLD is still in the denominator. Never infer
        # cost=0 for any missed or cost-unmeasured trial.
        cost_complete = not missed and all(r["cost_usd"] is not None for r in observed)
        total_cost = sum(r["cost_usd"] for r in observed) if cost_complete else None
        adjudication_complete = not missed and all(
            r["independent_adjudication"] for r in observed
        )
        report[arm] = {
            "assigned_attempts": assigned,
            "externally_verified_successes": success,
            "intention_to_treat_success_rate": success / assigned,
            "harness_errors_counted_as_nonsuccess": error,
            "missing_attempts_counted_as_nonsuccess": missed,
            "total_observed_cost_usd": total_cost,
            "cost_per_external_success_usd": (
                total_cost / success if cost_complete and success else None
            ),
            "cost_coverage_complete": cost_complete,
            "independent_adjudication_complete": adjudication_complete,
            "independently_adjudicated_invalid_attempts": (
                sum(r["invalid_completion_attempts"] for r in observed)
                if adjudication_complete else None
            ),
            "independently_adjudicated_blocked_invalid_attempts": (
                sum(r["gate_blocked_invalid_attempts"] for r in observed)
                if adjudication_complete else None
            ),
            "independently_adjudicated_avoidable_holds": (
                sum(r["avoidable_holds"] for r in observed)
                if adjudication_complete else None
            ),
        }
    return {
        "schema": SUMMARY_SCHEMA, "split": split,
        "task_count": len(tasks),
        "dataset": p["benchmark"]["dataset"],
        "task_manifest_sha256": p["benchmark"]["task_manifest_sha256"],
        "per_arm": report,
        "method": "intention-to-treat, external verifier PASS only; not gate success",
        "real_world_outcomes_authenticated_by_this_code": False,
    }


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--protocol", type=Path, default=DEFAULT_PATH)
    cli.add_argument("--normalized-results", type=Path)
    cli.add_argument("--split", choices=SPLITS, default="exploratory")
    args = cli.parse_args()
    p = json.loads(args.protocol.read_text(encoding="utf-8"))
    if args.normalized_results is None:
        result = validate_protocol(p)
    else:
        rows = json.loads(args.normalized_results.read_text(encoding="utf-8"))
        result = summarize_trials(p, rows, split=args.split)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
