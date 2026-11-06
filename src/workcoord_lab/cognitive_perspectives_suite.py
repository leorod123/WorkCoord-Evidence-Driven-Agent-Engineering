"""Reproducible public development cases for consultative cognitive lenses.

The fixture, labels, reviews and source stances are all published, authored
toy data. They are NOT held out from a repository-reading model.
"""
import argparse
import hashlib
import json
from pathlib import Path

from .cognitive_perspectives import evaluate_perspectives

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "examples" / "cognitive-perspective-cases-v0.json"


def run_suite():
    raw = CATALOG.read_bytes()
    data = json.loads(raw)
    if data.get("schema") != "workcoord.cognitive-perspective-cases/v0":
        raise ValueError("unknown public development catalog")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("empty development catalog")
    ids = [item["id"] for item in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate development case id")
    rows = []
    for case in cases:
        checkpoint = evaluate_perspectives(case["packet"])
        marker = case.get("expected_marker", "")
        matches = checkpoint["status"] == case["expected_status"]
        if marker == "has_support_challenge_conflict":
            matches &= checkpoint["has_support_challenge_conflict"]
        elif marker == "missing_perspectives":
            matches &= bool(checkpoint["missing_perspectives"])
        elif marker == "stale_perspectives":
            matches &= bool(checkpoint["stale_perspectives"])
        elif marker:
            matches &= any(gap["code"] == marker for gap in checkpoint["source_gaps"])
        rows.append({
            "case_id": case["id"],
            "label": case["label"],
            "result_status": checkpoint["status"],
            "checkpoint_sha256": checkpoint["checkpoint_sha256"],
            "received_perspectives": checkpoint["received_perspectives"],
            "missing_perspectives": checkpoint["missing_perspectives"],
            "has_support_challenge_conflict": checkpoint["has_support_challenge_conflict"],
            "reported_review_units": checkpoint["total_declared_review_units"],
            "source_body_characters": checkpoint["unique_cited_source_body_characters"],
            "development_expectation_met": bool(matches),
            "execution_authority": checkpoint["execution_authority"],
        })
    return {
        "schema": "workcoord.cognitive-perspective-results/v0",
        "status": "SYNTHETIC_PUBLIC_DEVELOPMENT_NOT_REAL_AGENT_EVALUATION",
        "catalog_sha256": hashlib.sha256(raw).hexdigest(),
        "case_count": len(rows),
        "expectations_met": sum(x["development_expectation_met"] for x in rows),
        "case_results": rows,
        "independent_agents_executed": 0,
        "authenticated_external_evidence": False,
        "measured_efficiency_gain": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="Write deterministic JSON receipt")
    args = parser.parse_args(argv)
    report = run_suite()
    body = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        print(json.dumps({
            "case_count": report["case_count"],
            "expectations_met": report["expectations_met"],
            "output": str(path),
        }, sort_keys=True))
    else:
        print(body, end="")


if __name__ == "__main__":
    main()
