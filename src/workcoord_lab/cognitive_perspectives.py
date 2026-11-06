"""Four consultative cognitive lenses over one fictional problem.

A review is a declared perspective, NOT an independent AI agent, authenticated
source, proof of correctness, instruction to execute, or work ownership.
This module constructs one deterministic, non-authoritative checkpoint.

Distinct axes:
  * technical sector = where an observation came from (API, worker, queue)
  * cognitive lens = how a single shared problem is reviewed
      (research, engineering, efficiency, risk)

Source and review revision/time checks are consistency tests on declared input.
They cannot authenticate the clocks, reporters or underlying observations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "workcoord.cognitive-perspectives/v0"
LENSES = ("RESEARCH", "ENGINEERING", "EFFICIENCY", "RISK")
RISK_LEVELS = ("QUICK", "STRUCTURED", "CRITICAL")
STANCES = ("SUPPORT", "CHALLENGE", "UNCERTAIN")
LENS_FOCUS = {
    "RESEARCH": "What observation would falsify this explanation?",
    "ENGINEERING": "Which required behavior is actually tested?",
    "EFFICIENCY": "Does incremental complexity justify its cost?",
    "RISK": "Which failure or authority boundary could invalidate action?",
}


class InvalidPerspectivePacket(ValueError):
    """Invalid input shape; distinct from unresolved substantive evidence."""


def _dict(value: Any, field: str) -> dict:
    if not isinstance(value, dict):
        raise InvalidPerspectivePacket(f"{field}: object required")
    return value


def _list(value: Any, field: str) -> list:
    if not isinstance(value, list):
        raise InvalidPerspectivePacket(f"{field}: list required")
    return value


def _text(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise InvalidPerspectivePacket(f"{field}: text required")
    return value


def _enum(value: Any, choices: tuple[str, ...], field: str) -> str:
    if not isinstance(value, str) or value not in choices:
        raise InvalidPerspectivePacket(f"{field}: unknown value")
    return value


def _tick(value: Any, field: str) -> int:
    if type(value) is not int or value < 0 or value > 1000000000:
        raise InvalidPerspectivePacket(f"{field}: bounded nonnegative integer required")
    return value


def _ids(value: Any, field: str) -> list[str]:
    arr = _list(value, field)
    for item in arr:
        _text(item, field + "[]")
    if len(arr) != len(set(arr)):
        raise InvalidPerspectivePacket(f"{field}: duplicate reference")
    return arr


def _required_lenses(risk: str) -> tuple[str, ...]:
    # Low-risk work must not automatically pay for four reviews.
    return ("ENGINEERING",) if risk == "QUICK" else LENSES


def evaluate_perspectives(packet: dict[str, Any]) -> dict[str, Any]:
    """Return an evidence-linked advisory checkpoint, never permission or truth."""
    packet = _dict(packet, "packet")
    if packet.get("schema") != SCHEMA:
        raise InvalidPerspectivePacket("unsupported cognitive review schema")
    issue = _dict(packet.get("issue"), "issue")
    issue_id = _text(issue.get("id"), "issue.id")
    proposal_id = _text(issue.get("proposal_id"), "issue.proposal_id")
    revision = _text(issue.get("source_revision"), "issue.source_revision")
    _text(issue.get("question"), "issue.question")
    risk = _enum(issue.get("risk"), RISK_LEVELS, "issue.risk")
    decision_tick = _tick(issue.get("decision_tick"), "issue.decision_tick")

    sources: dict[str, dict] = {}
    for raw in _list(packet.get("sources"), "sources"):
        source = _dict(raw, "source")
        source_id = _text(source.get("id"), "source.id")
        if source_id in sources:
            raise InvalidPerspectivePacket("duplicate source identifier")
        sources[source_id] = {
            "id": source_id,
            "revision": _text(source.get("source_revision"), "source.source_revision"),
            "sector": _text(source.get("technical_sector"), "source.technical_sector"),
            "origin": _text(source.get("origin_group"), "source.origin_group"),
            "available_tick": _tick(source.get("available_tick"), "source.available_tick"),
            "summary": _text(source.get("finding"), "source.finding"),
        }

    reviews: dict[str, dict] = {}
    for raw in _list(packet.get("reviews"), "reviews"):
        review = _dict(raw, "review")
        lens = _enum(review.get("perspective"), LENSES, "review.perspective")
        if lens in reviews:
            raise InvalidPerspectivePacket("duplicate cognitive perspective")
        if _text(review.get("issue_id"), "review.issue_id") != issue_id:
            raise InvalidPerspectivePacket("perspective examines a different issue")
        if _text(review.get("proposal_id"), "review.proposal_id") != proposal_id:
            raise InvalidPerspectivePacket("perspective examines a different proposal")
        stance = _enum(review.get("stance"), STANCES, "review.stance")
        refs = _ids(review.get("source_ids"), "review.source_ids")
        counterrefs = _ids(review.get("counterevidence_ids"), "review.counterevidence_ids")
        if not set(counterrefs).issubset(refs):
            raise InvalidPerspectivePacket("counterevidence must be among cited sources")
        rationale = _text(review.get("rationale"), "review.rationale")
        next_check = _text(review.get("next_check"), "review.next_check")
        question = _text(review.get("open_question", ""), "review.open_question",
                         allow_empty=True)
        if stance != "SUPPORT" and not question.strip():
            raise InvalidPerspectivePacket("unresolved perspective needs an open question")
        reviews[lens] = {
            "perspective": lens, "focus": LENS_FOCUS[lens],
            "issue_id": issue_id, "proposal_id": proposal_id,
            "source_revision": _text(review.get("source_revision"),
                                     "review.source_revision"),
            "review_tick": _tick(review.get("review_tick"), "review.review_tick"),
            "stance": stance, "source_ids": refs,
            "counterevidence_ids": counterrefs, "rationale": rationale,
            "open_question": question, "next_check": next_check,
            "estimated_review_units": _tick(review.get("estimated_review_units"),
                                            "review.estimated_review_units"),
        }

    required = _required_lenses(risk)
    missing = [lens for lens in required if lens not in reviews]
    stale = []
    source_gaps: list[dict] = []
    cited_ids = set()
    notes = []
    for lens in LENSES:
        if lens not in reviews:
            continue
        review = reviews[lens]
        invalid_review = review["source_revision"] != revision
        if review["review_tick"] > decision_tick:
            source_gaps.append({
                "perspective": lens, "code": "REVIEW_AFTER_DECISION",
                "source_id": None,
            })
        if invalid_review:
            stale.append(lens)
        for source_id in review["source_ids"]:
            cited_ids.add(source_id)
            src = sources.get(source_id)
            if src is None:
                source_gaps.append({
                    "perspective": lens, "source_id": source_id,
                    "code": "UNKNOWN_SOURCE_REFERENCE",
                })
            else:
                if src["revision"] != revision:
                    source_gaps.append({
                        "perspective": lens, "source_id": source_id,
                        "code": "SOURCE_REVISION_NOT_CURRENT",
                    })
                if src["available_tick"] > review["review_tick"]:
                    source_gaps.append({
                        "perspective": lens, "source_id": source_id,
                        "code": "SOURCE_UNAVAILABLE_AT_REVIEW",
                    })
        if not review["source_ids"]:
            source_gaps.append({
                "perspective": lens, "source_id": None,
                "code": "NO_CITED_EVIDENCE",
            })
        notes.append({
            "perspective": lens, "stance": review["stance"],
            "focus": review["focus"], "source_ids": list(review["source_ids"]),
            "counterevidence_ids": list(review["counterevidence_ids"]),
            "open_question": review["open_question"],
            "next_check": review["next_check"],
            "rationale": review["rationale"],
            "review_tick": review["review_tick"],
            "source_revision": review["source_revision"],
            "estimated_review_units": review["estimated_review_units"],
        })

    supported = sorted(lens for lens, rev in reviews.items()
                       if rev["stance"] == "SUPPORT")
    challenged = sorted(lens for lens, rev in reviews.items()
                        if rev["stance"] == "CHALLENGE")
    uncertain = sorted(lens for lens, rev in reviews.items()
                       if rev["stance"] == "UNCERTAIN")
    conflict = bool(supported and challenged)
    counterevidence_ids = sorted({
        item for review in reviews.values()
        for item in review["counterevidence_ids"]
    })
    if source_gaps:
        status = "HOLD_SOURCE_GAP"
    elif stale:
        status = "HOLD_STALE_PERSPECTIVE"
    elif missing:
        status = "HOLD_MISSING_PERSPECTIVE"
    elif conflict:
        status = "HOLD_CONTRADICTION"
    elif challenged:
        status = "HOLD_UNRESOLVED_CHALLENGE"
    elif uncertain:
        status = "HOLD_UNRESOLVED_UNCERTAINTY"
    elif risk == "CRITICAL":
        status = "REQUIRES_EXTERNAL_REVIEW"
    else:
        status = "ADVISORY_READY"

    source_manifest = [
        {
            "id": item, "technical_sector": sources[item]["sector"],
            "origin_group": sources[item]["origin"],
            "source_revision": sources[item]["revision"],
            "available_tick": sources[item]["available_tick"],
            "finding_sha256": hashlib.sha256(
                sources[item]["summary"].encode("utf-8")
            ).hexdigest(),
        } for item in sorted(cited_ids) if item in sources
    ]
    source_chars = sum(len(sources[item]["summary"]) for item in cited_ids
                       if item in sources)
    cost = sum(rev["estimated_review_units"] for rev in reviews.values())
    payload = {
        "schema": "workcoord.cognitive-checkpoint/v0",
        "issue_id": issue_id, "proposal_id": proposal_id,
        "source_revision": revision, "risk": risk,
        "decision_tick": decision_tick, "required_perspectives": list(required),
        "received_perspectives": [lens for lens in LENSES if lens in reviews],
        "missing_perspectives": missing, "stale_perspectives": stale,
        "source_gaps": sorted(source_gaps,
                              key=lambda g: (g["perspective"],
                                             g["code"], g["source_id"] or "")),
        "notes": notes,
        "supporting_perspectives": supported,
        "challenging_perspectives": challenged,
        "uncertain_perspectives": uncertain,
        "has_support_challenge_conflict": conflict,
        "counterevidence_ids": counterevidence_ids,
        "cited_source_manifest": source_manifest,
        "declared_origin_groups": sorted({sources[item]["origin"] for item in cited_ids
                                         if item in sources}),
        "total_declared_review_units": cost,
        "unique_cited_source_body_characters": source_chars,
        "status": status,
        "recommended_next_step": (
            "REFER_FOR_EXTERNAL_REVIEW" if status == "REQUIRES_EXTERNAL_REVIEW"
            else "REQUEST_EXTERNAL_ACCEPTANCE" if status == "ADVISORY_READY"
            else "INVESTIGATE_OR_REVISE"
        ),
        "knowledge_promotion": "NOT_GRANTED",
        "work_ownership": "NOT_ASSIGNED",
        "execution_authority": "NONE",
        "source_independence_authenticated": False,
        "external_problem_acceptance_verified": False,
        "real_agent_efficiency_measured": False,
        "contract_limits": (
            "Perspective records, time ticks and origins are authored labels. "
            "No LLM agents, source authentication or authority escalation."
        ),
    }
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    payload["checkpoint_sha256"] = hashlib.sha256(encoded).hexdigest()
    return payload


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", help="Path to one fictional cognitive review packet")
    args = parser.parse_args(argv)
    with Path(args.packet).open(encoding="utf-8") as f:
        packet = json.load(f)
    print(json.dumps(evaluate_perspectives(packet), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
