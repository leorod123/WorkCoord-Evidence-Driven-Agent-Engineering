"""Four-strategy, seven-case public *development* evaluation of adaptive reading.

Separate phases:
  1. Prepare identical permitted source views for all strategies.
  2. Select/decide without access to gold labels.
  3. Apply a separately loaded public evaluator after all decisions.

This is intentionally NOT a held-out, blinded or real-agent benchmark.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from .adaptive_evaluator import (
    grade_public_development_trace, validate_counterfactual_pair, visible_sources,
)
from .adaptive_policy import run_adaptive_policy
from .context_comparison import common_annotated_reader, select_context
from .intelligence import DEPTH, NavigationError


ROOT = Path(__file__).resolve().parents[2]
FLOWS = ROOT / "examples" / "flowdesk-context.json"
PAIRED = ROOT / "examples" / "adaptive-paired-worlds-v0.json"
CASES = ROOT / "evals" / "adaptive-cases-v0.json"
ORACLE = ROOT / "evals" / "adaptive-oracle-v0.json"
STRATEGIES = ("full_corpus", "local_sector", "dependency_expand", "adaptive_policy")
SCHEMA = "workcoord.adaptive-development-evaluation/v0"


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_development_inputs():
    flow, paired, cases, oracle = [_read(p) for p in (FLOWS, PAIRED, CASES, ORACLE)]
    expected = (
        ("workcoord.synthetic-context/v1", flow),
        ("workcoord.adaptive-paired-worlds/v0", paired),
        ("workcoord.adaptive-cases/v0", cases),
        ("workcoord.adaptive-oracle/v0", oracle),
    )
    if any(doc.get("schema") != name for name, doc in expected):
        raise ValueError("unsupported public development fixture schema")
    if tuple(cases.get("strategies", ())) != STRATEGIES:
        raise ValueError("comparison arms changed unexpectedly")
    case_ids = [c["id"] for c in cases["cases"]]
    gold_ids = [o["id"] for o in oracle["cases"]]
    if len(case_ids) != len(set(case_ids)) or len(gold_ids) != len(set(gold_ids)):
        raise ValueError("case or evaluator IDs are not unique")
    if set(case_ids) != set(gold_ids):
        raise ValueError("no exact one-to-one case/evaluator alignment")
    world_ids = [w["id"] for w in paired["worlds"]]
    if len(world_ids) != len(set(world_ids)):
        raise ValueError("duplicate paired world id")
    if {w["true_cause"] for w in paired["worlds"]} != set(paired["hypotheses"]):
        raise ValueError("paired worlds must disagree on the hidden cause")
    _validate_pair(flow, paired, cases, oracle)
    return flow, paired, cases, oracle


def _case_pool(flow, paired, case):
    if case["world"] == "flowdesk":
        root = flow
        documents = deepcopy(flow["documents"])
    else:
        worlds = {w["id"]: w for w in paired["worlds"]}
        if case["world"] not in worlds:
            raise ValueError("unknown synthetic world")
        root = paired
        documents = deepcopy(paired["shared_visible_documents"])
        documents.append(deepcopy(worlds[case["world"]]["hidden_deep_document"]))
    by_id = {doc["id"] for doc in documents}
    if len(by_id) != len(documents):
        raise ValueError("duplicate source id in synthetic case")
    if not set(case["remove_dependencies_from"]).issubset(by_id):
        raise ValueError("cannot remove dependency for unknown source")
    for doc in documents:
        if doc["id"] in case["remove_dependencies_from"]:
            doc["depends_on"] = []
    if case["max_access_depth"] not in DEPTH:
        raise ValueError("invalid access cap")
    permitted = visible_sources(documents, case["max_access_depth"], DEPTH)
    info = {
        "current_revision": root["current_revision"],
        "issue_tags": list(root["issue_tags"]),
        "hypotheses": list(root["hypotheses"]),
    }
    return permitted, documents, info


def _validate_pair(flow, paired, cases, oracle):
    keyed = {case["id"]: case for case in cases["cases"]}
    gold = {item["id"]: item for item in oracle["cases"]}
    left, right = keyed["AD05A"], keyed["AD05B"]
    permitted_left, full_left, info_left = _case_pool(flow, paired, left)
    permitted_right, full_right, info_right = _case_pool(flow, paired, right)
    validate_counterfactual_pair(
        permitted_left, permitted_right,
        gold["AD05A"]["expected_label"], gold["AD05B"]["expected_label"],
    )
    if info_left != info_right or left["start"] != right["start"]:
        raise ValueError("paired study changes accessible task information")
    if set([left["max_chars"], right["max_chars"]]) != {left["max_chars"]}:
        raise ValueError("paired budget mismatch")
    if full_left == full_right:
        raise ValueError("indistinguishable worlds need different inaccessible ground truth")
    for item in oracle["cases"]:
        case = keyed[item["id"]]
        _, full, info = _case_pool(flow, paired, case)
        ids = {doc["id"] for doc in full}
        if not set(item["required_sources"]).issubset(ids):
            raise ValueError("gold source not present in public synthetic world")
        if item["expected_label"] not in info["hypotheses"]:
            raise ValueError("unknown public development gold hypothesis")
    return True


def _policy_args(case):
    """Whitelist task parameters: do not pass world, case ID, cause or gold."""
    keys = (
        "risk_tier", "start", "max_access_depth", "max_chars",
        "max_hops", "max_actions", "expansion_depth",
    )
    return {key: deepcopy(case[key]) for key in keys}


def _fixed_decision(permitted, info, case, strategy):
    fixed_case = {
        "max_chars": case["max_chars"],
        "start": deepcopy(case["start"]),
        "expansion": {
            "depth": case["expansion_depth"],
            "max_hops": case["max_hops"],
        },
    }
    try:
        output = select_context(permitted, info, fixed_case, strategy)
    except NavigationError as exc:
        if strategy != "full_corpus":
            raise
        return {
            "decision": "BUDGET_INFEASIBLE",
            "reason": "Complete permitted source pool does not fit the common cap",
            "provisional_hypothesis": None,
            "selected_source_ids": [],
            "read_characters": 0,
            "budget_characters": case["max_chars"],
            "trace": [{"action": "BUDGET_INFEASIBLE", "reason": str(exc)}],
            "state": "NOT_AN_EXTERNAL_DIAGNOSIS",
        }
    reader = common_annotated_reader(
        output["source_records"], info["hypotheses"], info["current_revision"],
    )
    proposal = reader["provisional_hypothesis"]
    return {
        "decision": "PROVISIONAL" if proposal is not None else "HOLD",
        "reason": ("FIXED_HEURISTIC_PROVISIONAL_WITHOUT_COMPLETENESS_CHECK"
                   if proposal else "FIXED_HEURISTIC_NO_UNIQUE_LEADER"),
        "provisional_hypothesis": proposal,
        "selected_source_ids": output["source_ids"],
        "read_characters": output["read_characters"],
        "budget_characters": case["max_chars"],
        "trace": deepcopy(output["nav_steps"]),
        "state": "NOT_AN_EXTERNAL_DIAGNOSIS",
    }


def run_case(flow, paired, case, strategy):
    if strategy not in STRATEGIES:
        raise ValueError("unknown strategy")
    permitted, _, info = _case_pool(flow, paired, case)
    if strategy == "adaptive_policy":
        decision = run_adaptive_policy(
            permitted, issue_tags=info["issue_tags"],
            hypotheses=info["hypotheses"],
            current_revision=info["current_revision"], case=_policy_args(case),
        )
    else:
        decision = _fixed_decision(permitted, info, case, strategy)
    if decision["read_characters"] > case["max_chars"]:
        raise ValueError("arm violated shared source-body budget")
    return {
        "case_id": case["id"],
        "strategy": strategy,
        "permitted_source_ids": sorted(doc["id"] for doc in permitted),
        "decision": decision["decision"],
        "reason": decision["reason"],
        "provisional_hypothesis": decision["provisional_hypothesis"],
        "selected_source_ids": decision["selected_source_ids"],
        "read_characters": decision["read_characters"],
        "budget_characters": case["max_chars"],
        "trace": decision["trace"],
        "metadata_catalog_entries": decision.get("source_metadata_catalog_entries", 0),
        "not_a_production_result": True,
    }


def _summary(rows, strategy):
    records = [x for x in rows if x["strategy"] == strategy]
    categories = sorted({r["development_grade"]["category"] for r in records})
    return {
        "strategy": strategy,
        "cases": len(records),
        "total_selected_body_characters": sum(x["read_characters"] for x in records),
        "mean_decisive_recall": round(sum(
            x["development_grade"]["decisive_recall"] for x in records
        ) / len(records), 6),
        "grade_counts": {
            category: sum(x["development_grade"]["category"] == category
                          for x in records)
            for category in categories
        },
        "supported_provisional_count": sum(
            r["development_grade"]["category"] == "SUPPORTED_PROVISIONAL"
            for r in records
        ),
        "justified_access_limited_holds": sum(
            r["development_grade"]["category"] ==
            "JUSTIFIED_HOLD_UNDER_DECLARED_ACCESS" for r in records
        ),
        "avoided_assumptions": sum(
            r["development_grade"]["category"] in (
                "JUSTIFIED_HOLD_UNDER_DECLARED_ACCESS",
                "RESOURCE_LIMITED_HOLD_NOT_SCORED_SUCCESS",
            ) for r in records
        ),
        "unsupported_proposals": sum(
            r["development_grade"]["category"] == "UNSUPPORTED_PROVISIONAL"
            for r in records
        ),
        "avoidable_holds": sum(
            r["development_grade"]["category"] == "AVOIDABLE_HOLD"
            for r in records
        ),
    }


def evaluate_public_development():
    flow, paired, cases, oracle = load_development_inputs()
    # Phase 1: every candidate decision is collected BEFORE accessing oracle
    # labels. This is source-level separation, not a protected secret boundary.
    decisions = [
        run_case(flow, paired, case, strategy)
        for case in cases["cases"] for strategy in STRATEGIES
    ]
    # Phase 2: one common published evaluation contract grades all candidate
    # traces. The selector has no evaluator argument.
    gold_by_id = {x["id"]: x for x in oracle["cases"]}
    for row in decisions:
        row["development_grade"] = grade_public_development_trace(
            row, gold_by_id[row["case_id"]],
        )
    return {
        "schema": SCHEMA,
        "status": "PUBLIC_SYNTHETIC_EVAL_NO_LLM_NOT_HELD_OUT",
        "scope": "adaptive_action_trace_and_source_coverage_only",
        "input_sha256": {
            "flowdesk": _digest(FLOWS),
            "paired_worlds": _digest(PAIRED),
            "case_manifest": _digest(CASES),
            "development_oracle": _digest(ORACLE),
        },
        "case_count": len(cases["cases"]),
        "strategies": list(STRATEGIES),
        "results": decisions,
        "summary": [_summary(decisions, strategy) for strategy in STRATEGIES],
        "counterfactual_access_pair_validated": True,
        "limitations": [
            "Source stances are hand annotated; not independent external evidence.",
            "Public evaluator is separate from selectors but visible in the repository.",
            "Body-character counts omit indexing, metadata, reasoning, tokens and time.",
            "Provisional label agreement is not causal correctness or a verified repair.",
            "The fixed strategies and adaptive policy follow deliberately simplistic rules.",
            "No real LLM/agent experimental runs or statistically valid outcome comparison.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="Write the full reproducible JSON receipt")
    args = parser.parse_args(argv)
    result = evaluate_public_development()
    content = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(json.dumps({
            "schema": result["schema"], "case_count": result["case_count"],
            "summary": result["summary"], "output_path": str(target),
        }, indent=2, sort_keys=True))
    else:
        print(content, end="")


if __name__ == "__main__":
    main()
