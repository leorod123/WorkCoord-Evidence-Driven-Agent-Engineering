"""Public compact synthetic scenarios for the minimal four-stage vertical chain.

Only explicit, typed JSON patch operations on a published *fictional* base
packet. This fixture is not a held-out oracle and must never be used to
measure agent generalization. No eval, imports, commands or network calls.
"""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path

from .vertical_integration import VerticalInputError, evaluate_vertical

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "examples" / "vertical-integration-cases-v0.json"


def _locate(root, path):
    if not isinstance(path, list):
        raise VerticalInputError("patch.path: list required")
    node = root
    for key in path:
        if isinstance(node, dict):
            if type(key) is not str or key not in node:
                raise VerticalInputError("patch references missing dictionary key")
            node = node[key]
        elif isinstance(node, list):
            if type(key) is not int or not 0 <= key < len(node):
                raise VerticalInputError("patch references invalid list index")
            node = node[key]
        else:
            raise VerticalInputError("patch references scalar")
    return node


def materialize_case(catalog, case):
    root = deepcopy(catalog["base_packet"])
    for patch in case["patches"]:
        if not isinstance(patch, dict):
            raise VerticalInputError("patch: object required")
        op = patch.get("op")
        path = patch.get("path")
        if not isinstance(path, list) or not path:
            raise VerticalInputError("patch path must be nonempty")
        if op in ("append", "truncate"):
            target = _locate(root, path)
            if not isinstance(target, list):
                raise VerticalInputError("array patch applied to non-array")
            if op == "append":
                if set(patch) != {"op", "path", "value"}:
                    raise VerticalInputError("append fields")
                target.append(deepcopy(patch["value"]))
            else:
                if set(patch) != {"op", "path", "length"}:
                    raise VerticalInputError("truncate fields")
                count = patch["length"]
                if type(count) is not int or not 0 <= count <= len(target):
                    raise VerticalInputError("truncate cannot extend or use invalid length")
                del target[count:]
        elif op in ("set", "remove"):
            expected = {"op", "path", "value"} if op == "set" else {"op", "path"}
            if set(patch) != expected:
                raise VerticalInputError("set/remove fields")
            parent = _locate(root, path[:-1])
            key = path[-1]
            if isinstance(parent, dict):
                if type(key) is not str:
                    raise VerticalInputError("nonstring object key")
                if op == "remove":
                    if key not in parent:
                        raise VerticalInputError("remove unknown dictionary key")
                    del parent[key]
                else:
                    parent[key] = deepcopy(patch["value"])
            elif isinstance(parent, list):
                if op == "remove" or type(key) is not int or not 0 <= key < len(parent):
                    raise VerticalInputError("list set index invalid")
                parent[key] = deepcopy(patch["value"])
            else:
                raise VerticalInputError("set/remove at scalar")
        else:
            raise VerticalInputError("unknown fixture patch operation")
    return root


def load_catalog():
    raw = CATALOG.read_bytes()
    catalog = json.loads(raw)
    if catalog.get("schema") != "workcoord.vertical-development-cases/v0":
        raise ValueError("unknown public vertical catalog")
    cases = catalog.get("cases", []) + catalog.get("malformed", [])
    ids = [case["id"] for case in cases]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("missing or duplicate vertical case IDs")
    return catalog, hashlib.sha256(raw).hexdigest()


def run_suite():
    catalog, sha = load_catalog()
    rows = []
    for case in catalog["cases"]:
        packet = materialize_case(catalog, case)
        phase_results = []
        matches = True
        for phase in case["phases"]:
            result = evaluate_vertical(packet, at_seq=phase["at_seq"])
            ok = result["status"] == phase["expected_status"]
            matches &= ok and result["authorization"] == "NONE"
            phase_results.append({
                "at_seq": phase["at_seq"],
                "status": result["status"],
                "expected_status": phase["expected_status"],
                "expectation_met": bool(ok),
                "checkpoint_sha256": result["checkpoint_sha256"],
                "knowledge_prefix_head_sha256": result["knowledge_prefix_head_sha256"],
                "stage_status": result["stage_status"],
            })
        rows.append({
            "case_id": case["id"],
            "label": case["label"],
            "phases": phase_results,
            "expectations_met": bool(matches),
        })
    negative_rows = []
    for case in catalog["malformed"]:
        packet = materialize_case(catalog, case)
        rejected = False
        try:
            evaluate_vertical(packet, at_seq=case["at_seq"])
        except VerticalInputError:
            rejected = True
        negative_rows.append({
            "case_id": case["id"],
            "input_mismatch_rejected": rejected,
        })
    return {
        "schema": "workcoord.vertical-development-results/v0",
        "status": "PUBLIC_SYNTHETIC_DEVELOPMENT_NOT_REAL_AGENT_BENCHMARK",
        "catalog_sha256": sha,
        "case_count": len(rows),
        "positive_fixture_expectations_met": sum(x["expectations_met"] for x in rows),
        "malformed_case_count": len(negative_rows),
        "malformed_cases_rejected": sum(x["input_mismatch_rejected"] for x in negative_rows),
        "cases": rows,
        "malformed_cases": negative_rows,
        "independent_source_authentication": False,
        "scientific_truth_verified": False,
        "real_agent_learning_measured": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="Write deterministic public results receipt")
    args = parser.parse_args(argv)
    result = run_suite()
    text = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(json.dumps({
            "cases": result["case_count"],
            "matched": result["positive_fixture_expectations_met"],
            "invalid_cases_rejected": result["malformed_cases_rejected"],
            "receipt": str(path),
        }, sort_keys=True))
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
