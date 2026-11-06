"""Synthetic sectorized navigation walkthrough, not an AI model benchmark."""
import json
from pathlib import Path
from .intelligence import ContextNavigator


def fixture():
    path = Path(__file__).resolve().parents[2] / "examples" / "flowdesk-context.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["schema"] != "workcoord.synthetic-context/v1":
        raise ValueError("unsupported fictional fixture schema")
    return data


def run():
    data = fixture()
    nav = ContextNavigator(
        data["documents"],
        current_revision=data["current_revision"],
        issue_tags=data["issue_tags"], max_chars=1600,
    )
    initial = nav.navigate(
        sector="worker", perspective="reliability", depth="overview",
        reason="Start with the worker's reliability overview.",
    )
    first = nav.assess(data["hypotheses"])
    if "queue" not in initial["gaps"]["dependency_sectors_not_visited"]:
        raise RuntimeError("synthetic dependency expansion cue is missing")
    expanded = nav.navigate(
        sector="queue", perspective="reliability", depth="focused",
        reason="Follow the explicit worker-to-queue dependency; inspect current observations.",
    )
    revised = nav.assess(data["hypotheses"])
    if first["leading_hypothesis"] == revised["leading_hypothesis"]:
        raise RuntimeError("the synthetic fixture did not revise its investigation target")
    corroboration = nav.navigate(
        sector="api", perspective="reliability", depth="focused",
        reason="Seek independent-looking counterevidence; do not presume source independence.",
    )
    final = nav.assess(data["hypotheses"])
    return {
        "schema": "workcoord.intelligence-walkthrough/v1",
        "disclaimer": "Deterministic, human-annotated synthetic fixture; no LLM or causal efficacy measurement.",
        "initial": {"navigation": initial, "assessment": first},
        "after_queue_expansion": {"navigation": expanded, "assessment": revised},
        "after_api_crosscheck": {"navigation": corroboration, "assessment": final},
        "source_manifest": nav.context(),
        "unique_source_chars": nav.total_chars(),
        "relevant_corpus_chars": nav.relevant_corpus_chars(),
        "remaining_budget_chars": nav.max_chars - nav.total_chars(),
        "resolution": "HOLD_FOR_INDEPENDENT_TEST",
        "external_validation_performed": False,
    }


def main():
    print(json.dumps(run(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
