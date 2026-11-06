"""Fixed three-arm comparison over openly synthetic context-navigation fixtures.

This is a deterministic retrieval and hand-annotated decision *proxy*. No LLM
is invoked. The oracle is published development data, not secret held-out
evaluation. Read cost means exact unique source-body characters, not tokens.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from .intelligence import ContextNavigator, NavigationError


SCHEMA = "workcoord.synthetic-context-comparison/v0"
STRATEGIES = ("full_corpus", "local_sector", "dependency_expand")
ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "examples" / "flowdesk-context.json"
CASES = ROOT / "evals" / "context_cases_v0.json"
ORACLE = ROOT / "evals" / "context_oracle_v0.json"


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_public_development_inputs():
    fixture, cases, oracle = (_read_json(p) for p in (FIXTURE, CASES, ORACLE))
    if fixture.get("schema") != "workcoord.synthetic-context/v1":
        raise ValueError("unexpected synthetic source-fixture schema")
    if cases.get("schema") != "workcoord.context-retrieval-cases/v0":
        raise ValueError("unexpected synthetic case schema")
    if oracle.get("schema") != "workcoord.context-retrieval-oracle/v0":
        raise ValueError("unexpected synthetic evaluator schema")
    ids = [d["id"] for d in fixture["documents"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate source ids")
    cids = [c["id"] for c in cases["cases"]]
    oids = [c["id"] for c in oracle["cases"]]
    if len(cids) != len(set(cids)) or len(oids) != len(set(oids)) or set(cids) != set(oids):
        raise ValueError("the case and evaluator IDs must match uniquely")
    if tuple(cases["strategies"]) != STRATEGIES:
        raise ValueError("unexpected comparison strategies")
    for entry in oracle["cases"]:
        decisive = entry["decisive_sources"]
        counter = entry["counterevidence_sources"]
        if not decisive or not counter or not set(decisive + counter).issubset(ids):
            raise ValueError("evaluator requires existing source IDs")
        if entry["expected_provisional_hypothesis"] not in fixture["hypotheses"]:
            raise ValueError("unknown synthetic expected hypothesis")
    for case in cases["cases"]:
        if not set(case["remove_dependencies_from"]).issubset(ids):
            raise ValueError("unknown dependency removal target")
        if type(case["max_chars"]) is not int or case["max_chars"] < 1:
            raise ValueError("invalid comparable character budget")
        if type(case["expansion"]["max_hops"]) is not int or case["expansion"]["max_hops"] < 0:
            raise ValueError("invalid dependency depth")
    return fixture, cases, oracle


def _case_documents(fixture, case):
    """Same modified, fictional source pool supplied to all three arms."""
    docs = deepcopy(fixture["documents"])
    for doc in docs:
        if doc["id"] in case["remove_dependencies_from"]:
            doc["depends_on"] = []
    return docs


def select_context(documents, fixture, case, strategy):
    """Selection stage has no oracle argument and never reads evaluator files."""
    if strategy not in STRATEGIES:
        raise ValueError("unknown comparison arm")
    budget = case["max_chars"]
    if strategy == "full_corpus":
        sources = sorted(documents, key=lambda doc: doc["id"])
        chars = sum(len(doc["body"]) for doc in sources)
        if chars > budget:
            # The full baseline cannot quietly violate the common cap or be
            # misrepresented as complete after truncation.
            raise NavigationError("full corpus exceeds the equal run budget")
        return {
            "source_ids": [doc["id"] for doc in sources],
            "source_records": sources,
            "read_characters": chars,
            "nav_steps": [{
                "sector": "ALL", "perspective": "ALL", "depth": "deep",
                "reason": "Unfiltered, full source-pool baseline",
                "new_sources": [doc["id"] for doc in sources],
                "new_chars": chars,
            }],
            "unread_due_to_budget": [],
            "unvisited_dependency_sectors": [],
        }

    nav = ContextNavigator(
        documents, current_revision=fixture["current_revision"],
        issue_tags=fixture["issue_tags"], max_chars=budget,
    )
    start = case["start"]
    first = nav.navigate(
        sector=start["sector"], perspective=start["perspective"], depth=start["depth"],
        reason="Predeclared initial context request; no evaluator labels supplied.",
    )
    if strategy == "dependency_expand":
        # Follow only the dependencies exposed by ALREADY SELECTED sources.
        # Never use the oracle's decisive source IDs to choose a sector.
        for _ in range(case["expansion"]["max_hops"]):
            linked = nav.steps[-1]["gaps"]["dependency_sectors_not_visited"]
            if not linked:
                break
            nav.navigate(
                sector=linked[0], perspective=start["perspective"],
                depth=case["expansion"]["depth"],
                reason="Follow the first declared but unvisited dependency sector.",
            )
    doc_by_id = {doc["id"]: doc for doc in documents}
    selected = [deepcopy(doc_by_id[item["id"]]) for item in nav.context()]
    gaps = sorted({
        source_id for step in nav.steps
        for source_id in step["gaps"]["unread_due_to_budget"]
    })
    return {
        "source_ids": [doc["id"] for doc in selected],
        "source_records": selected,
        "read_characters": nav.total_chars(),
        "nav_steps": deepcopy(nav.steps),
        "unread_due_to_budget": gaps,
        "unvisited_dependency_sectors": sorted(
            set(nav.steps[-1]["gaps"]["dependency_sectors_not_visited"])
        ),
    }


def common_annotated_reader(sources, hypotheses, current_revision):
    """Exactly the same intentionally weak, human-tagged reader for each arm.

    Crucially, expected answers and required evidence IDs are NOT inputs.
    It can be wrong even with all relevant sources, and is not an AI model.
    """
    scores = {hyp: 0 for hyp in hypotheses}
    for doc in sources:
        weight = (3 if doc["maturity"] == "validated"
                  else 2 if doc["maturity"] == "observed" else 1)
        if doc["revision"] != current_revision:
            weight = 1
        for hyp, stance in doc["signals"].items():
            if hyp not in scores:
                continue
            scores[hyp] += weight if stance == "supports" else -weight
    highest = max(scores.values())
    leaders = [hyp for hyp, score in scores.items() if score == highest]
    proposed = leaders[0] if highest > 0 and len(leaders) == 1 else None
    return {
        "provisional_hypothesis": proposed, "annotated_heuristic_scores": scores,
        "decision_status": "PROVISIONAL_REQUIRES_EXTERNAL_TEST",
    }


def evaluate_selected(case, gold, selected, reader):
    """Common published development oracle; never part of source selection."""
    ids = set(selected["source_ids"])
    decisive = set(gold["decisive_sources"])
    counter = set(gold["counterevidence_sources"])
    if not decisive or not counter:
        raise ValueError("cannot grade empty evidence rubric")
    recalled_decisive = sorted(decisive & ids)
    recalled_counter = sorted(counter & ids)
    matches = reader["provisional_hypothesis"] == gold["expected_provisional_hypothesis"]
    complete = len(recalled_decisive) == len(decisive)
    return {
        "case_id": case["id"],
        "expected_provisional_hypothesis": gold["expected_provisional_hypothesis"],
        "decisive_sources_recovered": recalled_decisive,
        "decisive_sources_missing": sorted(decisive - ids),
        "decisive_recall": round(len(recalled_decisive) / len(decisive), 6),
        "counterevidence_sources_recovered": recalled_counter,
        "counterevidence_sources_missing": sorted(counter - ids),
        "counterevidence_recall": round(len(recalled_counter) / len(counter), 6),
        "provisional_label_matches_fixture": matches,
        "complete_decisive_evidence_available": complete,
        "evidence_supported_provisional_label": bool(matches and complete),
        "correct_sounding_but_incomplete_evidence": bool(matches and not complete),
        "invalid_final_completion_assessed": False,
        "actual_agent_decision_quality_measured": False,
    }


def run_case(fixture, case, gold, strategy):
    documents = _case_documents(fixture, case)
    selected = select_context(documents, fixture, case, strategy)
    reader = common_annotated_reader(
        selected["source_records"], fixture["hypotheses"], fixture["current_revision"],
    )
    metrics = evaluate_selected(case, gold, selected, reader)
    return {
        "case_id": case["id"], "strategy": strategy,
        "selection": {
            "source_ids": selected["source_ids"],
            "read_characters": selected["read_characters"],
            "source_count": len(selected["source_ids"]),
            "nav_steps": selected["nav_steps"],
            "unread_due_to_budget": selected["unread_due_to_budget"],
            "unvisited_dependency_sectors": selected["unvisited_dependency_sectors"],
            "budget_characters": case["max_chars"],
        },
        "reader": reader,
        "external_development_rubric": metrics,
    }


def _aggregate(results, strategy):
    rows = [row for row in results if row["strategy"] == strategy]
    return {
        "strategy": strategy,
        "cases": len(rows),
        "total_source_body_characters_read": sum(
            x["selection"]["read_characters"] for x in rows),
        "total_selected_sources": sum(x["selection"]["source_count"] for x in rows),
        "mean_decisive_evidence_recall": round(sum(
            x["external_development_rubric"]["decisive_recall"] for x in rows
        ) / len(rows), 6),
        "mean_counterevidence_recall": round(sum(
            x["external_development_rubric"]["counterevidence_recall"] for x in rows
        ) / len(rows), 6),
        "provisional_fixture_label_matches": sum(
            x["external_development_rubric"]["provisional_label_matches_fixture"] for x in rows),
        "evidence_supported_provisional_labels": sum(
            x["external_development_rubric"]["evidence_supported_provisional_label"] for x in rows),
        "correct_sounding_with_incomplete_evidence": sum(
            x["external_development_rubric"]["correct_sounding_but_incomplete_evidence"] for x in rows),
    }


def run_comparison(fixture=None, cases=None, oracle=None):
    if fixture is None or cases is None or oracle is None:
        fixture, cases, oracle = load_public_development_inputs()
    gold_by_id = {entry["id"]: entry for entry in oracle["cases"]}
    results = [
        run_case(fixture, case, gold_by_id[case["id"]], strategy)
        for case in cases["cases"] for strategy in STRATEGIES
    ]
    return {
        "schema": SCHEMA,
        "status": "DETERMINISTIC_PUBLIC_FIXTURE_NO_LLM",
        "scope": "synthetic_retrieval_coverage_and_annotated_reader_proxy",
        "no_real_agent_quality_or_token_savings_claim": True,
        "public_oracle_not_held_out": True,
        "source_identity_sha256": {
            "source_fixture": _file_digest(FIXTURE),
            "case_definitions": _file_digest(CASES),
            "development_oracle": _file_digest(ORACLE),
        },
        "strategies": list(STRATEGIES),
        "case_count": len(cases["cases"]),
        "results": results,
        "summary": [_aggregate(results, strategy) for strategy in STRATEGIES],
        "interpretation": (
            "Only source availability and a fixed hand-annotated diagnosis proxy "
            "were compared. Character counts exclude metadata, tool overhead, "
            "retrieval computation, tokenization and model inference. "
            "No independent hidden agent evaluation was performed."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="Write deterministic JSON receipt to this local path")
    args = parser.parse_args(argv)
    result = run_comparison()
    content = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(json.dumps({
            "schema": result["schema"], "status": result["status"],
            "case_count": result["case_count"], "summary": result["summary"],
            "output_path": str(target),
        }, indent=2, sort_keys=True))
    else:
        print(content, end="")


if __name__ == "__main__":
    main()
