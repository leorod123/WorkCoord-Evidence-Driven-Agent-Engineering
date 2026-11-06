"""Independent, public, fictional research-admissibility checks (stdlib only).

This evaluator checks whether a research packet is ready for a proposed next
investigation. It cannot authenticate external files, decide scientific truth,
or grant review, execution or publication authority.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

SCHEMA = "workcoord.research-admission/v0"
RISK = {"QUICK", "STRUCTURED", "CRITICAL"}
SOURCE_CLASSES = {"current", "historical", "synthetic"}
DRAFT_CLAIMS = {"HYPOTHESIS", "OBSERVED", "TESTED", "VALIDATED"}
FAMILIES = (
    "source_integrity", "time_of_knowledge", "chronology", "outcome_peeking",
    "metric_fit", "alternative_tests", "corroboration", "claim_boundary",
)


class InvalidResearchPacket(ValueError):
    """Strictly malformed research packet; not a negative scientific finding."""


def _require_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidResearchPacket(f"{name}: expected nonempty text")
    return value


def _require_bool(value: Any, name: str) -> bool:
    if type(value) is not bool:
        raise InvalidResearchPacket(f"{name}: expected boolean, not truthy value")
    return value


def _time(value: Any, name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise InvalidResearchPacket(f"{name}: expected timezone-aware ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidResearchPacket(f"{name}: invalid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InvalidResearchPacket(f"{name}: timezone is required")
    return parsed.astimezone(timezone.utc)


def _list(value: Any, name: str) -> list:
    if not isinstance(value, list):
        raise InvalidResearchPacket(f"{name}: expected array")
    return value


def _dict(value: Any, name: str) -> dict:
    if not isinstance(value, dict):
        raise InvalidResearchPacket(f"{name}: expected object")
    return value


def evaluate_research(packet: dict[str, Any]) -> dict[str, Any]:
    """Check evidence eligibility without looking up a gold outcome.

    No hidden answer, source inference or model call. A cited evidence ID is
    only a self-declared label; external authenticity MUST be verified elsewhere.
    """
    packet = _dict(packet, "packet")
    if packet.get("schema") != SCHEMA:
        raise InvalidResearchPacket("schema: unsupported research packet")
    risk = packet.get("risk")
    if not isinstance(risk, str) or risk not in RISK:
        raise InvalidResearchPacket("risk: unknown depth")
    _require_text(packet.get("question"), "question")
    source = _dict(packet.get("source"), "source")
    _require_text(source.get("id"), "source.id")
    revision = _require_text(source.get("revision"), "source.revision")
    proposed_at = _time(packet.get("decision_at"), "decision_at")
    target = packet.get("requested_knowledge_state", "HYPOTHESIS")
    if not isinstance(target, str) or target not in DRAFT_CLAIMS:
        raise InvalidResearchPacket("requested_knowledge_state: unknown")
    evidence = _list(packet.get("evidence", []), "evidence")
    hypotheses = _list(packet.get("hypotheses", []), "hypotheses")
    controls = _dict(packet.get("controls", {}), "controls")
    evaluation = _dict(packet.get("evaluation", {}), "evaluation")
    issue_index: dict[str, list[str]] = {key: [] for key in FAMILIES}

    def fail(family: str, issue: str) -> None:
        if issue not in issue_index[family]:
            issue_index[family].append(issue)

    ids: set[str] = set()
    groups: set[str] = set()
    eligible: set[str] = set()
    for index, raw in enumerate(evidence):
        item = _dict(raw, f"evidence[{index}]")
        label = _require_text(item.get("id"), f"evidence[{index}].id")
        if label in ids:
            raise InvalidResearchPacket("evidence IDs must be unique")
        ids.add(label)
        ev_revision = _require_text(item.get("revision"), "evidence.revision")
        origin = _require_text(item.get("origin_group"), "evidence.origin_group")
        source_class = item.get("source_class")
        if not isinstance(source_class, str) or source_class not in SOURCE_CLASSES:
            raise InvalidResearchPacket("evidence.source_class: unknown")
        observed = _time(item.get("observed_at"), "evidence.observed_at")
        available = _time(item.get("available_at"), "evidence.available_at")
        read = _time(item.get("read_at"), "evidence.read_at")
        _require_text(item.get("finding"), "evidence.finding")
        temporal_ok = True
        if observed > available or available > read:
            fail("chronology", "INVALID_OBSERVATION_AVAILABILITY_READ_ORDER")
            temporal_ok = False
        if available > proposed_at or read > proposed_at:
            fail("time_of_knowledge", "SOURCE_NOT_AVAILABLE_AT_DECISION")
            temporal_ok = False
        if ev_revision != revision or source_class == "historical":
            fail("source_integrity", "CURRENT_CONCLUSION_USES_STALE_OR_HISTORICAL_SOURCE")
        if temporal_ok and ev_revision == revision and source_class != "historical":
            eligible.add(label)
            groups.add(origin)

    hyp_ids: set[str] = set()
    for index, raw in enumerate(hypotheses):
        hyp = _dict(raw, f"hypotheses[{index}]")
        h_id = _require_text(hyp.get("id"), "hypothesis.id")
        if h_id in hyp_ids:
            raise InvalidResearchPacket("hypothesis IDs must be unique")
        hyp_ids.add(h_id)
        _require_text(hyp.get("claim"), "hypothesis.claim")
        if risk != "QUICK":
            falsifier = hyp.get("falsifier")
            if not isinstance(falsifier, str) or not falsifier.strip():
                fail("alternative_tests", "HYPOTHESIS_WITHOUT_FALSIFIER")
        refs = _list(hyp.get("evidence_ids", []), "hypothesis.evidence_ids")
        if any(not isinstance(r, str) for r in refs) or len(refs) != len(set(refs)):
            raise InvalidResearchPacket("hypothesis evidence IDs invalid or duplicated")
        if any(ref not in ids for ref in refs):
            fail("source_integrity", "HYPOTHESIS_REFERENCES_UNKNOWN_EVIDENCE")
    if risk == "QUICK":
        if not evidence:
            fail("source_integrity", "QUICK_NEEDS_ONE_OBSERVATION")
        if not isinstance(packet.get("next_test"), str) or not packet["next_test"].strip():
            fail("alternative_tests", "NEXT_CHECK_NOT_SPECIFIED")
    else:
        if len(hyp_ids) < 2:
            fail("alternative_tests", "COMPETING_HYPOTHESES_NOT_RECORDED")
        if not isinstance(packet.get("next_test"), str) or not packet["next_test"].strip():
            fail("alternative_tests", "DISCRIMINATING_CHECK_NOT_SPECIFIED")
        if not isinstance(controls.get("baseline"), str) or not controls["baseline"].strip():
            fail("alternative_tests", "BASELINE_NOT_DEFINED")
        if not isinstance(controls.get("negative_control"), str) or not controls["negative_control"].strip():
            fail("alternative_tests", "NEGATIVE_CONTROL_NOT_DEFINED")
        construct = controls.get("construct_fit")
        if type(construct) is not bool:
            fail("metric_fit", "MEASURE_TARGET_FIT_NOT_DECLARED")
        elif not construct:
            fail("metric_fit", "MEASURE_DOES_NOT_ESTABLISH_TARGET")
        if not eligible:
            fail("source_integrity", "NO_CURRENT_ADMISSIBLE_OBSERVATION")

    if risk == "CRITICAL":
        # Multiple readings from the same generation are not independent.
        if len(groups) < 2:
            fail("corroboration", "NO_INDEPENDENT_ORIGIN_GROUPS_DECLARED")
        reviewer = packet.get("independent_review")
        if not isinstance(reviewer, str) or not reviewer.strip():
            fail("corroboration", "INDEPENDENT_REVIEW_NOT_RECORDED")
        # This field remains unverified: a reference to a reviewer is not a
        # signed review or external authority.

    bearing = evaluation.get("outcome_bearing", False)
    _require_bool(bearing, "evaluation.outcome_bearing")
    if bearing:
        freeze = evaluation.get("plan_frozen_at")
        observed = evaluation.get("outcome_observed_at")
        if freeze is None or observed is None:
            fail("outcome_peeking", "OUTCOME_TIMING_NOT_BOUND")
        else:
            if _time(freeze, "evaluation.plan_frozen_at") >= _time(
                observed, "evaluation.outcome_observed_at"
            ):
                fail("outcome_peeking", "PLAN_NOT_FROZEN_BEFORE_OUTCOME")
        if not isinstance(evaluation.get("pass_criterion"), str) or not evaluation["pass_criterion"].strip():
            fail("outcome_peeking", "SUCCESS_CRITERION_NOT_PREDECLARED")

    # This project has no independent evidence verifier. Neither a self-labelled
    # TESTED nor a self-labelled VALIDATED state can be promoted by this gate.
    if target in ("TESTED", "VALIDATED"):
        fail("claim_boundary", "CANNOT_PROMOTE_TO_TESTED_OR_VALIDATED_FROM_DECLARATIONS")
    elif target == "OBSERVED" and not eligible:
        fail("claim_boundary", "OBSERVED_STATE_REQUIRES_CURRENT_EVIDENCE")

    flat = [issue for family in FAMILIES for issue in issue_index[family]]
    if flat:
        status = "NEEDS_RESEARCH"
    elif risk == "CRITICAL":
        status = "REQUIRES_EXTERNAL_REVIEW"
    else:
        status = "DESIGN_ADMISSIBLE"
    return {
        "schema": "workcoord.research-admission-result/v0",
        "status": status,
        "risk": risk,
        "issues": {family: issue_index[family] for family in FAMILIES if issue_index[family]},
        "issue_count": len(flat),
        "eligible_evidence_ids": sorted(eligible),
        "declared_origin_groups": sorted(groups),
        "execution_authority": "NONE",
        "knowledge_promotion": "NOT_GRANTED",
        "verified_causal_claim": False,
        "observed_productivity_gain": "NOT_MEASURED",
        "explanation": "Advisory packet checks only; evidence identities and reviews remain self-declared.",
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", help="Path to a fictional or user-controlled research packet JSON")
    args = parser.parse_args(argv)
    with Path(args.packet).open(encoding="utf-8") as file:
        packet = json.load(file)
    print(json.dumps(evaluate_research(packet), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
