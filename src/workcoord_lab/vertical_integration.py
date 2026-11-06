"""One minimal vertical *advisory* evidence chain using existing public modules.

Connects Research Quality -> Problem & Decision -> Cognitive Perspectives ->
Knowledge Genealogy over a shared fictional incident, proposal, revision and
source-body digest. No new coordinator, process, store, model, external tool,
independent validator, approval or runtime permission.

A later append-only challenge can invalidate a once-admissible *candidate*.
The earlier checkpoint is still reconstructible at its historical event cut.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .research_quality import evaluate_research
from .problem_decision import evaluate_problem_decision
from .cognitive_perspectives import evaluate_perspectives
from .knowledge_genealogy import evaluate_actions

SCHEMA = "workcoord.vertical-evidence-chain/v0"
MANIFEST_SCHEMA = "workcoord.vertical-source-manifest/v0"
MANIFEST_FIELDS = frozenset({
    "schema", "issue_id", "proposal_id", "source_revision", "primary_source_id",
    "primary_observation_id", "primary_source_sha256", "claim_id",
    "source_lineage", "risk",
})
PACKET_FIELDS = frozenset({
    "schema", "manifest", "research", "problem", "cognitive", "knowledge_actions",
})
VALID_RISK = ("QUICK", "STRUCTURED", "CRITICAL")
RESEARCH_READY = "DESIGN_ADMISSIBLE"
PROBLEM_READY = "CANDIDATE_FOR_EXTERNAL_ACCEPTANCE"
COGNITIVE_READY = "ADVISORY_READY"
KNOWLEDGE_READY = "ADVISORY_CURRENT"


class VerticalInputError(ValueError):
    """A malformed or mismatched cross-stage packet, never permission."""


def _obj(v: Any, field: str) -> dict:
    if not isinstance(v, dict):
        raise VerticalInputError(f"{field}: object required")
    return v


def _text(v: Any, field: str) -> str:
    if not isinstance(v, str) or not v.strip():
        raise VerticalInputError(f"{field}: nonempty string required")
    return v


def _sha(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=True, allow_nan=False,
                   separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _source_sha(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _one(items: Any, target_id: str, key: str, field: str) -> dict:
    if not isinstance(items, list):
        raise VerticalInputError(f"{field}: list required")
    matching = [x for x in items if isinstance(x, dict) and x.get(key) == target_id]
    if len(matching) != 1:
        raise VerticalInputError(f"{field}: exact shared identity must appear once")
    return matching[0]


def _validate_common(packet: dict) -> tuple[dict, list]:
    if set(packet) != PACKET_FIELDS or packet.get("schema") != SCHEMA:
        raise VerticalInputError("vertical packet: unknown schema or unexpected fields")
    manifest = _obj(packet["manifest"], "manifest")
    if set(manifest) != MANIFEST_FIELDS or manifest.get("schema") != MANIFEST_SCHEMA:
        raise VerticalInputError("manifest: unexpected fields or schema")
    for key in MANIFEST_FIELDS - {"schema", "risk"}:
        _text(manifest[key], "manifest." + key)
    if manifest["risk"] not in VALID_RISK or type(manifest["risk"]) is not str:
        raise VerticalInputError("manifest.risk: invalid tier")
    digest = manifest["primary_source_sha256"]
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise VerticalInputError("manifest.primary_source_sha256: invalid SHA-256 hex")

    rq = _obj(packet["research"], "research")
    pd = _obj(packet["problem"], "problem")
    cp = _obj(packet["cognitive"], "cognitive")
    actions = packet["knowledge_actions"]
    if not isinstance(actions, list):
        raise VerticalInputError("knowledge_actions: list required")

    # These identity checks prevent mixing valid but unrelated stage outputs.
    if (rq.get("risk") != manifest["risk"]
        or pd.get("risk") != manifest["risk"]
        or _obj(cp.get("issue"), "cognitive.issue").get("risk") != manifest["risk"]):
        raise VerticalInputError("risk tier must be shared across all four stages")

    source = _obj(rq.get("source"), "research.source")
    problem = _obj(pd.get("problem"), "problem.problem")
    issue = cp["issue"]
    if (source.get("id") != manifest["primary_source_id"]
        or source.get("revision") != manifest["source_revision"]
        or problem.get("id") != manifest["issue_id"]
        or problem.get("source_revision") != manifest["source_revision"]
        or issue.get("id") != manifest["issue_id"]
        or issue.get("proposal_id") != manifest["proposal_id"]
        or issue.get("source_revision") != manifest["source_revision"]):
        raise VerticalInputError("issue, source, proposal or revision mismatch")

    if pd.get("decision") is not None:
        if _obj(pd["decision"], "problem.decision").get("selected_id") != manifest["proposal_id"]:
            raise VerticalInputError("selected remedy is not the reviewed proposal")
    elif manifest["risk"] != "QUICK":
        raise VerticalInputError("non-QUICK problem needs an explicit decision")

    for review in cp.get("reviews", []):
        rev = _obj(review, "cognitive.review")
        if rev.get("issue_id") != manifest["issue_id"] or rev.get("proposal_id") != manifest["proposal_id"]:
            raise VerticalInputError("cognitive lens addresses a different issue or remedy")

    shared = manifest["primary_observation_id"]
    r_obs = _one(rq.get("evidence"), shared, "id", "research.evidence")
    c_obs = _one(cp.get("sources"), shared, "id", "cognitive.sources")
    k_source = _one(
        [a["data"] for a in actions if isinstance(a, dict) and a.get("kind") == "SOURCE_ADD"],
        manifest["primary_source_id"], "source_id", "knowledge.source",
    )
    k_obs = _one(
        [a["data"] for a in actions if isinstance(a, dict) and a.get("kind") == "OBSERVATION_ADD"],
        shared, "observation_id", "knowledge.observation",
    )
    if (r_obs.get("revision") != manifest["source_revision"]
        or c_obs.get("source_revision") != manifest["source_revision"]
        or k_source.get("revision") != manifest["source_revision"]
        or k_source.get("lineage_id") != manifest["source_lineage"]
        or k_obs.get("claim_id") != manifest["claim_id"]
        or k_obs.get("source_id") != manifest["primary_source_id"]
        or k_obs.get("stance") != "SUPPORT"):
        raise VerticalInputError("primary shared evidence revision/claim/source mismatch")

    # Body integrity is checked across independently shaped record types.
    for label, body in [
        ("research", r_obs.get("finding")), ("cognitive", c_obs.get("finding")),
        ("knowledge source", k_source.get("body")),
        ("knowledge observation", k_obs.get("finding")),
    ]:
        if not isinstance(body, str) or _source_sha(body) != digest:
            raise VerticalInputError(f"{label}: shared body hash is not identical")
    if manifest["risk"] != "QUICK":
        primary_hypothesis = _one(
            rq.get("hypotheses", []), manifest["claim_id"], "id",
            "research.hypotheses"
        )
        opened = _one(
            [a["data"] for a in actions
             if isinstance(a, dict) and a.get("kind") == "CLAIM_OPEN"],
            manifest["claim_id"], "claim_id", "knowledge.claim",
        )
        if primary_hypothesis.get("claim") != opened.get("statement"):
            raise VerticalInputError("knowledge claim and researched hypothesis text differ")
    if not any(
        isinstance(a, dict) and a.get("kind") == "CLAIM_OPEN"
        and isinstance(a.get("data"), dict)
        and a["data"].get("claim_id") == manifest["claim_id"]
        for a in actions
    ):
        raise VerticalInputError("knowledge claim is missing from the shared investigation")
    problem_witness = _one(pd.get("evidence"), shared, "id", "problem.evidence")
    if problem_witness.get("revision") != manifest["source_revision"]:
        raise VerticalInputError("problem witness does not match shared revision")
    if not any(
        isinstance(rev, dict) and shared in rev.get("source_ids", [])
        for rev in cp.get("reviews", [])
    ):
        raise VerticalInputError("primary source is not cited by any cognitive perspective")
    return manifest, actions


def evaluate_vertical(packet: dict[str, Any], *, at_seq: int) -> dict[str, Any]:
    """Evaluate a history cut. Neither this nor any upstream stage grants authority."""
    packet = _obj(packet, "packet")
    manifest, actions = _validate_common(packet)
    if type(at_seq) is not int or at_seq < 1 or at_seq > len(actions):
        raise VerticalInputError("at_seq must be a nonempty valid historical cut")

    research = evaluate_research(packet["research"])
    problem = evaluate_problem_decision(packet["problem"])
    cognitive = evaluate_perspectives(packet["cognitive"])
    knowledge = evaluate_actions(actions, at_seq=at_seq)

    # Protect against retroactively counting future observations at an earlier cut.
    shared_obs = manifest["primary_observation_id"]
    obs = next((e for e in knowledge["observations"] if e["id"] == shared_obs), None)
    if obs is None:
        raise VerticalInputError("primary observation did not yet exist at historical cut")
    claims = {item["id"]: item["status"] for item in knowledge["claims"]}
    if manifest["claim_id"] not in claims:
        raise VerticalInputError("primary claim not yet present at historical cut")
    lineage = next((x for x in knowledge["lineages"]
                    if x["lineage_id"] == manifest["source_lineage"]), None)
    if lineage is None:
        raise VerticalInputError("primary source lineage missing at history cut")
    active_source = lineage["active_source_id"]
    selected = next((x for x in lineage["versions"]
                     if x["source_id"] == active_source), None)
    if selected is None:
        raise VerticalInputError("incomplete lineage state")
    source_epoch_drift = (
        active_source != manifest["primary_source_id"]
        or selected["revision"] != manifest["source_revision"]
        or selected["body_sha256"] != manifest["primary_source_sha256"]
    )

    reasons = []
    if source_epoch_drift:
        reasons.append("SOURCE_EPOCH_CHANGED_REASSESS_ALL_STAGES")
    if claims[manifest["claim_id"]] != KNOWLEDGE_READY:
        reasons.append("GENEALOGY_" + claims[manifest["claim_id"]])
    if research["status"] != RESEARCH_READY:
        reasons.append("RESEARCH_" + research["status"])
    if problem["status"] != PROBLEM_READY:
        reasons.append("PROBLEM_" + problem["status"])
    if cognitive["status"] != COGNITIVE_READY:
        reasons.append("COGNITIVE_" + cognitive["status"])

    # Stable priority is useful for displaying the *new late counterevidence*
    # without concealing other independent blockers in the reasons array.
    if source_epoch_drift:
        decision = "HOLD_REASSESS_REVISION"
    elif claims[manifest["claim_id"]] != KNOWLEDGE_READY:
        decision = "HOLD_KNOWLEDGE"
    elif research["status"] == "NEEDS_RESEARCH":
        decision = "HOLD_RESEARCH"
    elif problem["status"] in ("HOLD_REQUIRED_PROBLEM_OPEN", "HOLD_DECISION_INCOMPLETE"):
        decision = "HOLD_PROBLEM"
    elif cognitive["status"].startswith("HOLD_"):
        decision = "HOLD_COGNITIVE"
    elif reasons:
        decision = "REQUIRES_EXTERNAL_REVIEW"
    else:
        decision = "ADVISORY_CANDIDATE_FOR_EXTERNAL_ACCEPTANCE"

    result = {
        "schema": "workcoord.vertical-evidence-checkpoint/v0",
        "status": decision,
        "reason_codes": sorted(set(reasons)),
        "issue_id": manifest["issue_id"], "proposal_id": manifest["proposal_id"],
        "source_revision": manifest["source_revision"],
        "source_epoch_drift": source_epoch_drift,
        "primary_source_sha256": manifest["primary_source_sha256"],
        "manifest_sha256": _sha(manifest),
        "historical_cut_seq": at_seq,
        "knowledge_prefix_head_sha256": knowledge["prefix_head_sha256"],
        "upstream_receipt_sha256": {
            "research": _sha(research), "problem": _sha(problem),
            "cognitive": _sha(cognitive), "knowledge": _sha(knowledge),
        },
        "stage_status": {
            "research": research["status"],
            "problem": problem["status"],
            "cognitive": cognitive["status"],
            "knowledge_claim": claims[manifest["claim_id"]],
        },
        "technical_tests_declared_green": problem["reported_technical_tests_green"],
        "mandatory_open_nodes": problem["required_open_node_ids"],
        "cognitive_challenges": cognitive["challenging_perspectives"],
        "active_source_id": active_source,
        "historical_observation_count": len(knowledge["observations"]),
        "historical_transition_count": len(knowledge["transitions"]),
        "assumed_review_effort_units": cognitive["total_declared_review_units"],
        "assumed_remedy_cost_table": problem["estimated_alternatives"],
        "independent_outcome_verified": False,
        "model_learning_performed": False,
        "source_authenticity_verified": False,
        "authorization": "NONE",
        "work_ownership": "NOT_ASSIGNED",
        "knowledge_promotion": "NOT_GRANTED",
        "evaluation_note": "Advisory fictional stage composition; no agent correctness, learning, source authentication or action privilege.",
    }
    result["checkpoint_sha256"] = _sha(result)
    return result


def main(argv: list[str] | None = None) -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("packet", help="Path to self-contained fictional vertical packet JSON")
    cli.add_argument("--at-seq", type=int, required=True)
    args = cli.parse_args(argv)
    packet = json.loads(Path(args.packet).read_text(encoding="utf-8"))
    print(json.dumps(evaluate_vertical(packet, at_seq=args.at_seq),
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
