"""Public fictional Problem & Decision scenarios; not a held-out evaluator.

The fixture's labels are published and hand-authored. Results are
advisory-only and do not validate the truth of behavioral evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path

from .problem_decision import evaluate_problem_decision

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "examples" / "problem-decision-cases-v0.json"


def run_suite():
    raw = CATALOG.read_bytes()
    catalog = json.loads(raw)
    if catalog.get("schema") != "workcoord.problem-decision-cases/v0":
        raise ValueError("unsupported synthetic case catalog")
    cases = catalog.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("empty catalog")
    case_ids = [c["id"] for c in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("case ids must be unique")
    rows = []
    for item in cases:
        result = evaluate_problem_decision(item["packet"])
        checks = [
            result["status"] == item["expected_status"],
            result["required_open_node_ids"] == sorted(item["expected_open_nodes"]),
            set(item["expected_decision_issues"]).issubset(result["decision_issues"]),
            not result["semantic_closure_granted"],
            result["execution_authority"] == "NONE",
        ]
        rows.append({
            "id": item["id"],
            "scenario": item["label"],
            "status": result["status"],
            "required_open_node_ids": result["required_open_node_ids"],
            "decision_issues": result["decision_issues"],
            "declared_technical_tests_green": result["reported_technical_tests_green"],
            "estimated_costs": result["estimated_alternatives"],
            "development_expectation_met": all(checks),
        })
    return {
        "schema": "workcoord.problem-decision-results/v0",
        "status": "SYNTHETIC_PUBLIC_DEVELOPMENT_NOT_REAL_AGENT_EVALUATION",
        "catalog_sha256": hashlib.sha256(raw).hexdigest(),
        "case_count": len(rows),
        "expectations_met": sum(r["development_expectation_met"] for r in rows),
        "results": rows,
        "no_external_validation_or_software_fix_claim": True,
        "limitations": (
            "All evidence outcomes, costs and case expectations are declared in "
            "public fictional inputs; readiness is not independent acceptance, "
            "knowledge validation, execution authorization or measured efficiency."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="Write deterministic JSON results to a local path")
    args = parser.parse_args(argv)
    result = run_suite()
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded, encoding="utf-8")
        print(json.dumps({
            "case_count": result["case_count"],
            "expectations_met": result["expectations_met"],
            "receipt_path": str(path),
        }, sort_keys=True))
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
