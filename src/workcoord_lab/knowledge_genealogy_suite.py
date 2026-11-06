"""Deterministic public development fixture for source and claim genealogy.

Expected labels live in the same file as the fictional events; this is NOT
independently scored or secret. The evaluator itself has no gold-case input.
"""
import argparse
import hashlib
import json
from pathlib import Path

from .knowledge_genealogy import evaluate_actions, seal_actions, verify_chain

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "examples" / "knowledge-genealogy-cases-v0.json"


def run_suite() -> dict:
    raw = CATALOG.read_bytes()
    catalog = json.loads(raw)
    if catalog.get("schema") != "workcoord.knowledge-genealogy-cases/v0":
        raise ValueError("unexpected fictional case catalog")
    cases = catalog.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("missing fictional development cases")
    ids = [item["case_id"] for item in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate development case identifier")
    rows = []
    for case in cases:
        records = seal_actions(case["actions"])
        verified = verify_chain(records)
        checkpoint = evaluate_actions(case["actions"])
        actual = {c["id"]: c["status"] for c in checkpoint["claims"]}
        matches = actual == case["expected_status_by_claim"]
        cut_rows = []
        for cut in case.get("at_seq_checks", []):
            before = evaluate_actions(case["actions"], at_seq=cut["at_seq"])
            historical = {c["id"]: c["status"] for c in before["claims"]}
            cut_match = historical == cut["status_by_claim"]
            matches &= cut_match
            cut_rows.append({
                "at_seq": cut["at_seq"],
                "checkpoint_prefix_sha256": before["prefix_head_sha256"],
                "declared_expected_match": cut_match,
            })
        rows.append({
            "case_id": case["case_id"],
            "source_history_count": len(checkpoint["lineages"]),
            "observation_history_count": len(checkpoint["observations"]),
            "event_count": checkpoint["event_count"],
            "event_head_sha256": verified,
            "claim_statuses": actual,
            "historical_cuts": cut_rows,
            "transition_count": len(checkpoint["transitions"]),
            "development_expectation_met": bool(matches),
            "knowledge_promotion": checkpoint["knowledge_promotion"],
            "execution_authority": checkpoint["execution_authority"],
        })
    return {
        "schema": "workcoord.knowledge-genealogy-results/v0",
        "status": "PUBLIC_SYNTHETIC_DEVELOPMENT_NOT_HELD_OUT",
        "catalog_sha256": hashlib.sha256(raw).hexdigest(),
        "case_count": len(rows),
        "expectations_met": sum(r["development_expectation_met"] for r in rows),
        "results": rows,
        "real_world_source_authentication": False,
        "real_agent_learning_measured": False,
        "external_causal_validation": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="Write deterministic JSON receipt")
    args = parser.parse_args(argv)
    result = run_suite()
    body = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        print(json.dumps({
            "cases": result["case_count"],
            "expectations_met": result["expectations_met"],
            "receipt": str(target),
        }, sort_keys=True))
    else:
        print(body, end="")


if __name__ == "__main__":
    main()
