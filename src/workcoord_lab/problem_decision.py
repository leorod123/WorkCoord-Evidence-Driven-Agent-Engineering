"""Independent problem-map and solution-decision *admission* reference.

A technical test's PASS flag is not proof that the user's required outcome was
achieved. This module checks the internal consistency of synthetic records,
not the truth of evidence, cost forecasts, reviewer identities, or deployment
authority. It does not edit WorkCoord or any external runtime state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "workcoord.problem-decision/v0"
RISKS = {"QUICK", "STRUCTURED", "CRITICAL"}
KNOWLEDGE = {"KNOWN", "HYPOTHESIS", "UNKNOWN"}
KINDS = {"technical_test", "behavior_probe"}
RESULTS = {"PASS", "FAIL", "INCONCLUSIVE"}
STRATEGIES = {"reuse", "simplify", "adapt", "build", "defer"}
APPLICATIONS = {"reuse_existing", "configure", "modify_local", "new_component", "defer"}


class ProblemInputError(ValueError):
    """Malformed public example; unlike a genuine unresolved problem."""


def _obj(value: Any, label: str) -> dict:
    if not isinstance(value, dict):
        raise ProblemInputError(f"{label}: expected object")
    return value


def _items(value: Any, label: str) -> list:
    if not isinstance(value, list):
        raise ProblemInputError(f"{label}: expected list")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProblemInputError(f"{label}: nonempty text required")
    return value


def _bool(value: Any, label: str) -> bool:
    if type(value) is not bool:
        raise ProblemInputError(f"{label}: boolean required")
    return value


def _count(value: Any, label: str, *, positive: bool = False) -> int:
    if type(value) is not int or value < int(positive) or value > 1000000000:
        raise ProblemInputError(f"{label}: expected bounded nonnegative integer")
    return value


def _enum(value: Any, accepted: set[str], label: str) -> str:
    if not isinstance(value, str) or value not in accepted:
        raise ProblemInputError(f"{label}: unknown value")
    return value


def _ids(value: Any, label: str) -> list[str]:
    seq = _items(value, label)
    for entry in seq:
        _string(entry, label + "[]")
    if len(seq) != len(set(seq)):
        raise ProblemInputError(f"{label}: repeated reference")
    return seq


def _tree(nodes: list[dict]) -> tuple[dict[str, dict], str, list[str]]:
    """Check hierarchy and return all required leaf IDs (not merely root)."""
    if not nodes:
        raise ProblemInputError("problem map cannot be empty")
    if len(nodes) > 256:
        raise ProblemInputError("example limits problem map to 256 nodes")
    indexed: dict[str, dict] = {}
    for raw in nodes:
        node = _obj(raw, "nodes[]")
        key = _string(node.get("id"), "node.id")
        if key in indexed:
            raise ProblemInputError("duplicate node id")
        parent = node.get("parent_id")
        if parent is not None:
            _string(parent, "node.parent_id")
        _string(node.get("title"), "node.title")
        required = _bool(node.get("required"), "node.required")
        state = _enum(node.get("knowledge"), KNOWLEDGE, "node.knowledge")
        criteria: dict[str, dict] = {}
        for raw_criterion in _items(node.get("criteria"), "node.criteria"):
            criterion = _obj(raw_criterion, "criteria[]")
            c_id = _string(criterion.get("id"), "criterion.id")
            if c_id in criteria:
                raise ProblemInputError("duplicate criterion within node")
            _string(criterion.get("check"), "criterion.check")
            kind = _enum(criterion.get("kind"), KINDS, "criterion.kind")
            criteria[c_id] = {"id": c_id, "kind": kind}
        if required and not criteria:
            raise ProblemInputError("required node needs an acceptance criterion")
        indexed[key] = {
            "id": key, "parent_id": parent, "required": required,
            "knowledge": state, "criteria": criteria,
        }
    roots = [name for name, n in indexed.items() if n["parent_id"] is None]
    if len(roots) != 1 or not indexed[roots[0]]["required"]:
        raise ProblemInputError("exactly one required root must exist")

    for name, node in indexed.items():
        ancestors: set[str] = {name}
        parent = node["parent_id"]
        while parent is not None:
            if parent not in indexed:
                raise ProblemInputError("dangling problem parent")
            if parent in ancestors:
                raise ProblemInputError("cycle in problem map")
            ancestors.add(parent)
            if node["required"] and not indexed[parent]["required"]:
                raise ProblemInputError("required node under optional ancestor")
            parent = indexed[parent]["parent_id"]
        if roots[0] not in ancestors:
            raise ProblemInputError("disconnected problem map")
    parents = {n["parent_id"] for n in indexed.values() if n["parent_id"]}
    leaf_ids = sorted(key for key, n in indexed.items()
                      if n["required"] and key not in parents)
    return indexed, roots[0], leaf_ids


def _witnesses(raw: Any, nodes: dict[str, dict], revision: str) -> dict:
    """Check fixture declarations; never infer independent authenticity."""
    seen: set[str] = set()
    indexed: dict[tuple[str, str], list[dict]] = {}
    for raw_evidence in _items(raw, "evidence"):
        evidence = _obj(raw_evidence, "evidence[]")
        ev_id = _string(evidence.get("id"), "evidence.id")
        if ev_id in seen:
            raise ProblemInputError("duplicate evidence id")
        seen.add(ev_id)
        node_id = _string(evidence.get("node_id"), "evidence.node_id")
        criterion_id = _string(evidence.get("criterion_id"), "evidence.criterion_id")
        if node_id not in nodes or criterion_id not in nodes[node_id]["criteria"]:
            raise ProblemInputError("evidence targets an unknown problem criterion")
        ev_revision = _string(evidence.get("revision"), "evidence.revision")
        kind = _enum(evidence.get("kind"), KINDS, "evidence.kind")
        result = _enum(evidence.get("declared_result"), RESULTS, "evidence.declared_result")
        # Revision mismatch is a diagnostic failure, not malformed input.
        indexed.setdefault((node_id, criterion_id), []).append({
            "id": ev_id, "revision": ev_revision,
            "current": ev_revision == revision, "kind": kind, "result": result,
        })
    return indexed


def _costed_decision(data: Any, leaf_ids: list[str], nodes: dict[str, dict],
                     risk: str) -> tuple[str, list[str], list[dict]]:
    """Compare *declared assumptions* at a common horizon, without choosing."""
    if risk == "QUICK" and data is None:
        return "LIGHTWEIGHT_ROUTE", [], []
    if data is None:
        return "INCOMPLETE", ["ALTERNATIVES_NOT_RECORDED"], []
    d = _obj(data, "decision")
    horizon = _count(d.get("horizon_cycles"), "decision.horizon_cycles", positive=True)
    unit = _string(d.get("cost_unit"), "decision.cost_unit")
    selected_id = _string(d.get("selected_id"), "decision.selected_id")
    options = _items(d.get("alternatives"), "decision.alternatives")
    if not options:
        return "INCOMPLETE", ["ALTERNATIVES_NOT_RECORDED"], []
    known: dict[str, dict] = {}
    computed: list[dict] = []
    for raw in options:
        alt = _obj(raw, "alternative")
        key = _string(alt.get("id"), "alternative.id")
        if key in known:
            raise ProblemInputError("duplicate alternative id")
        strategy = _enum(alt.get("strategy"), STRATEGIES, "alternative.strategy")
        coverage = _ids(alt.get("addresses"), "alternative.addresses")
        if any(node_id not in nodes for node_id in coverage):
            raise ProblemInputError("alternative targets unknown problem node")
        upfront = _count(alt.get("upfront_units"), "alternative.upfront_units")
        recurring = _count(alt.get("recurring_units"), "alternative.recurring_units")
        risk_reserve = _count(alt.get("risk_allowance_units"), "alternative.risk_allowance_units")
        rework_reserve = _count(alt.get("rework_allowance_units"), "alternative.rework_allowance_units")
        _bool(alt.get("reversible"), "alternative.reversible")
        why_not = alt.get("rejection_reason", "")
        if not isinstance(why_not, str):
            raise ProblemInputError("alternative.rejection_reason: text required")
        total = upfront + horizon * recurring + risk_reserve + rework_reserve
        known[key] = {
            "id": key, "strategy": strategy, "addresses": coverage,
            "cost_units": total, "rejection_reason": why_not,
            "reversible": alt["reversible"],
        }
        computed.append({
            "id": key, "strategy": strategy, "estimated_total_units": total,
            "upfront_units": upfront, "recurring_units": recurring,
            "horizon_cycles": horizon, "cost_unit": unit,
        })
    if selected_id not in known:
        raise ProblemInputError("decision selects an unknown alternative")
    selected = known[selected_id]
    findings: list[str] = []
    if risk != "QUICK":
        if len(known) < 2 or len({a["strategy"] for a in known.values()}) < 2:
            findings.append("ALTERNATIVE_COMPARISON_INSUFFICIENT")
        if not isinstance(d.get("rationale"), str) or not d["rationale"].strip():
            findings.append("DECISION_RATIONALE_MISSING")
    if selected["strategy"] == "defer":
        findings.append("DECISION_IS_DEFERRED")
    if not set(leaf_ids).issubset(selected["addresses"]):
        findings.append("REQUIRED_LEAF_NOT_ADDRESSED_BY_SELECTED_ALTERNATIVE")
    if selected["strategy"] == "build":
        cheaper = [
            item for item in known.values()
            if item["strategy"] in {"reuse", "simplify"}
            and set(leaf_ids).issubset(item["addresses"])
            and item["cost_units"] < selected["cost_units"]
            and not item["rejection_reason"].strip()
        ]
        if cheaper:
            findings.append("CHEAPER_COMPARABLE_REUSE_NOT_EXPLAINED")

    application = d.get("application")
    if risk != "QUICK":
        if not isinstance(application, dict):
            findings.append("APPLICATION_PLAN_MISSING")
        else:
            mode = application.get("mode")
            if not isinstance(mode, str) or mode not in APPLICATIONS:
                findings.append("APPLICATION_MODE_UNSPECIFIED")
            steps = application.get("steps")
            if not isinstance(steps, list) or not steps or any(
                    not isinstance(step, str) or not step.strip() for step in steps):
                findings.append("APPLICATION_STEPS_MISSING")
            rollback = application.get("rollback")
            if selected["reversible"] and (
                    not isinstance(rollback, str) or not rollback.strip()):
                findings.append("REVERSIBLE_APPLICATION_HAS_NO_ROLLBACK")
            if risk == "CRITICAL":
                containment = application.get("containment")
                if not isinstance(containment, str) or not containment.strip():
                    findings.append("CRITICAL_IMPACT_CONTAINMENT_NOT_RECORDED")
    if findings:
        return "DECISION_INCOMPLETE", findings, sorted(computed, key=lambda x: x["id"])
    return "OPTIONS_COMPARED_NOT_APPROVED", [], sorted(computed, key=lambda x: x["id"])


def evaluate_problem_decision(packet: dict[str, Any]) -> dict[str, Any]:
    """Run an advisory eligibility check. No work, knowledge or authority mutation."""
    packet = _obj(packet, "packet")
    if packet.get("schema") != SCHEMA:
        raise ProblemInputError("unknown problem-decision schema")
    risk = _enum(packet.get("risk"), RISKS, "risk")
    problem = _obj(packet.get("problem"), "problem")
    _string(problem.get("id"), "problem.id")
    _string(problem.get("statement"), "problem.statement")
    _string(problem.get("goal"), "problem.goal")
    revision = _string(problem.get("source_revision"), "problem.source_revision")
    implementation = _obj(packet.get("implementation"), "implementation")
    green = _bool(implementation.get("technical_tests_green"),
                  "implementation.technical_tests_green")
    _string(implementation.get("work_status"), "implementation.work_status")
    nodes, root_id, leaves = _tree(_items(packet.get("nodes"), "nodes"))
    evidence = _witnesses(packet.get("evidence"), nodes, revision)
    problems: dict[str, list[str]] = {}
    node_report: list[dict] = []
    unaddressed: list[str] = []

    for key in sorted(nodes):
        node = nodes[key]
        issues = []
        criteria = []
        if node["knowledge"] != "KNOWN":
            issues.append("REQUIRED_NODE_NOT_KNOWN" if node["required"]
                          else "OPTIONAL_NODE_NOT_KNOWN")
        for c_id in sorted(node["criteria"]):
            requirement = node["criteria"][c_id]
            submitted = evidence.get((key, c_id), [])
            admissible = [w for w in submitted if w["current"]
                          and w["kind"] == requirement["kind"]]
            passes = [w["id"] for w in admissible if w["result"] == "PASS"]
            failures = [w["id"] for w in admissible if w["result"] == "FAIL"]
            if failures:
                outcome = "CONTRADICTED"
                issues.append("CONTRADICTORY_CURRENT_EVIDENCE")
            elif passes:
                outcome = "DECLARED_COVERED_UNVERIFIED"
            else:
                outcome = "MISSING_REQUIRED_BEHAVIOR_WITNESS" if requirement["kind"] == "behavior_probe" else "MISSING_REQUIRED_TECHNICAL_WITNESS"
                issues.append(outcome)
            if any(not w["current"] for w in submitted):
                issues.append("STALE_EVIDENCE_PRESENT")
            if submitted and any(w["kind"] != requirement["kind"] for w in submitted):
                issues.append("WRONG_EVIDENCE_KIND_PRESENT")
            criteria.append({
                "id": c_id, "required_kind": requirement["kind"], "outcome": outcome,
                "declared_current_pass_ids": sorted(passes),
                "declared_current_fail_ids": sorted(failures),
            })
        if node["required"] and issues:
            unaddressed.append(key)
            problems[key] = sorted(set(issues))
        node_report.append({
            "id": key, "parent_id": node["parent_id"], "required": node["required"],
            "knowledge": node["knowledge"], "acceptance": criteria,
            "issues": sorted(set(issues)),
            "readiness": ("REQUIRES_EVIDENCE" if node["required"] and issues
                          else "COVERED_DECLARATIONS_ONLY" if node["required"]
                          else "OPTIONAL_NOT_A_CLOSURE_GATE"),
        })

    decision_status, decision_issues, cost_table = _costed_decision(
        packet.get("decision"), leaves, nodes, risk)
    if green and unaddressed:
        decision_issues.append("TECHNICAL_GREEN_DOES_NOT_CLOSE_REQUIRED_OUTCOMES")
    if unaddressed:
        status = "HOLD_REQUIRED_PROBLEM_OPEN"
    elif decision_issues:
        status = "HOLD_DECISION_INCOMPLETE"
    elif risk == "CRITICAL":
        status = "REQUIRES_EXTERNAL_REVIEW"
    else:
        status = "CANDIDATE_FOR_EXTERNAL_ACCEPTANCE"
    return {
        "schema": "workcoord.problem-decision-evaluation/v0",
        "status": status,
        "risk": risk,
        "root_id": root_id,
        "required_leaf_ids": leaves,
        "node_results": node_report,
        "required_open_node_ids": sorted(unaddressed),
        "problem_findings": problems,
        "decision_status": decision_status,
        "decision_issues": sorted(set(decision_issues)),
        "estimated_alternatives": cost_table,
        "reported_technical_tests_green": green,
        "semantic_closure_granted": False,
        "knowledge_promotion": "NOT_GRANTED",
        "execution_authority": "NONE",
        "real_world_cost_measured": False,
        "independent_source_validation": False,
        "disclaimer": "All evidence and costs are self-declared; this is admission to external acceptance, not problem closure.",
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", help="JSON problem-decision packet")
    args = parser.parse_args(argv)
    with Path(args.packet).open(encoding="utf-8") as source:
        packet = json.load(source)
    print(json.dumps(evaluate_problem_decision(packet), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
