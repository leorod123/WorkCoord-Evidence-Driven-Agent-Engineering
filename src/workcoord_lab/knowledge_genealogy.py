"""Append-only, source-linked fictional knowledge genealogy reference (stdlib).

All sources, observations, revision labels, logical ticks and review receipts
are declared by a public development fixture. SHA-256 detects accidental
record changes; it does NOT authenticate origin, timestamp, scientific truth,
reviewer independence, or authority to execute.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "workcoord.knowledge-genealogy/v0"
EVENT_KINDS = (
    "SOURCE_ADD", "SOURCE_SUPERSEDE", "CLAIM_OPEN",
    "OBSERVATION_ADD", "OBSERVATION_RETRACT", "REVIEW_ACCEPT",
)
STANCES = ("SUPPORT", "CHALLENGE")
CURRENT = "ADVISORY_CURRENT"
ZERO_HASH = "0" * 64


class GenealogyError(ValueError):
    """Malformed or inadmissible fictional knowledge record."""


def _object(value: Any, name: str) -> dict:
    if not isinstance(value, dict):
        raise GenealogyError(f"{name}: expected object")
    return value


def _array(value: Any, name: str) -> list:
    if not isinstance(value, list):
        raise GenealogyError(f"{name}: expected array")
    return value


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GenealogyError(f"{name}: nonempty string required")
    return value


def _tick(value: Any, name: str) -> int:
    if type(value) is not int or value < 0 or value > 1000000000:
        raise GenealogyError(f"{name}: bounded logical tick required")
    return value


def _ids(value: Any, name: str) -> list[str]:
    ids = _array(value, name)
    for item in ids:
        _text(item, name + "[]")
    if len(ids) != len(set(ids)):
        raise GenealogyError(f"{name}: duplicate reference")
    return ids


def _fields(value: Any, expected: set[str], name: str) -> dict:
    obj = _object(value, name)
    if set(obj) != expected:
        raise GenealogyError(f"{name}: unexpected or missing fields")
    return obj


def _encode(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def _hash(value: Any) -> str:
    return hashlib.sha256(_encode(value)).hexdigest()


def seal_actions(actions: list) -> list[dict]:
    """Hash-chain an authored fixture; this is not a cryptographic signature."""
    records = []
    prior = ZERO_HASH
    for number, raw in enumerate(_array(actions, "actions"), 1):
        act = _fields(raw, {"id", "tick", "kind", "data"}, "action")
        event = {
            "seq": number, "event_id": _text(act["id"], "event id"),
            "tick": _tick(act["tick"], "event tick"),
            "kind": _text(act["kind"], "event kind"),
            "data": _object(act["data"], "event data"),
            "previous_sha256": prior,
        }
        event["event_sha256"] = _hash(event)
        prior = event["event_sha256"]
        records.append(event)
    return records


def verify_chain(records: list) -> str:
    """Detect altered/reordered/truncated-without-expected-head records.

    A complete adversarial re-sealing is NOT prevented without an independent
    trusted head anchor or signature, neither of which exists in this v0.
    """
    prev = ZERO_HASH
    last_tick = -1
    seen = set()
    for number, raw in enumerate(_array(records, "records"), 1):
        row = _fields(raw, {
            "seq", "event_id", "tick", "kind", "data",
            "previous_sha256", "event_sha256",
        }, "event")
        if type(row["seq"]) is not int or row["seq"] != number:
            raise GenealogyError("event sequence is not contiguous")
        name = _text(row["event_id"], "event_id")
        if name in seen:
            raise GenealogyError("duplicate event ID")
        seen.add(name)
        tick = _tick(row["tick"], "event tick")
        if tick < last_tick:
            raise GenealogyError("logical clock moved backwards")
        last_tick = tick
        if row["kind"] not in EVENT_KINDS:
            raise GenealogyError("unknown event type")
        _object(row["data"], "event.data")
        if row["previous_sha256"] != prev:
            raise GenealogyError("event's predecessor hash does not match")
        input_row = {k: v for k, v in row.items() if k != "event_sha256"}
        if row["event_sha256"] != _hash(input_row):
            raise GenealogyError("event content digest mismatch")
        prev = row["event_sha256"]
    return prev


def _evidence_current(item: dict, sources: dict) -> bool:
    return (item["retracted_seq"] is None and
            sources[item["source_id"]]["active"])


def _claim_statuses(claims: dict, evidence: dict, sources: dict) -> dict:
    """Evaluate a DAG without changing accepted review history."""
    cache: dict[str, str] = {}

    def status(cid: str) -> str:
        if cid in cache:
            return cache[cid]
        claim = claims[cid]
        reviews = claim["review"]
        active = [r for r in evidence.values()
                  if r["claim_id"] == cid and _evidence_current(r, sources)]
        challenges = [r for r in active if r["stance"] == "CHALLENGE"]
        if challenges:
            value = "HOLD_COUNTEREVIDENCE"
        elif reviews is None:
            value = "HOLD_UNREVIEWED"
        elif any(not sources[evidence[eid]["source_id"]]["active"]
                 for eid in reviews["basis_ids"]):
            value = "HOLD_STALE_BASIS"
        elif any(evidence[eid]["retracted_seq"] is not None
                 for eid in reviews["basis_ids"]):
            value = "HOLD_RETRACTED_BASIS"
        elif claim["touched_seq"] > reviews["seq"]:
            value = "HOLD_REVIEW_REQUIRED"
        elif any(status(dep) != CURRENT for dep in claim["depends_on"]):
            value = "HOLD_UPSTREAM"
        elif any(claims[dep]["review"]["event_sha256"] !=
                 reviews["upstream_reviews"][dep] for dep in claim["depends_on"]):
            value = "HOLD_UPSTREAM_REVIEW_CHANGED"
        else:
            value = CURRENT
        cache[cid] = value
        return value

    return {key: status(key) for key in sorted(claims)}


def replay_events(records: list, *, at_seq: int | None = None) -> dict:
    """Verify the full supplied chain, then evaluate a prefix-only checkpoint.

    Caller may separately call verify_chain(records) to audit the whole log.
    That *future* head must never enter an as-of checkpoint identity.
    """
    verify_chain(records)
    if at_seq is None:
        at_seq = len(records)
    if type(at_seq) is not int or not 0 <= at_seq <= len(records):
        raise GenealogyError("at_seq must be a valid integer history cut")
    sources: dict[str, dict] = {}
    active_lineage: dict[str, str] = {}
    claims: dict[str, dict] = {}
    evidence: dict[str, dict] = {}
    prior_status: dict[str, str] = {}
    transitions: list[dict] = []

    for row in records[:at_seq]:
        kind = row["kind"]
        data = _object(row["data"], "event data")
        seq = row["seq"]
        tick = row["tick"]

        if kind == "SOURCE_ADD":
            data = _fields(data, {
                "source_id", "lineage_id", "revision", "body", "available_tick",
            }, kind)
            sid = _text(data["source_id"], "source_id")
            lineage = _text(data["lineage_id"], "lineage_id")
            revision = _text(data["revision"], "revision")
            body = _text(data["body"], "source.body")
            available = _tick(data["available_tick"], "available_tick")
            if available > tick:
                raise GenealogyError("source registered before availability")
            if sid in sources:
                raise GenealogyError("duplicate immutable source ID")
            for source in sources.values():
                if source["lineage_id"] == lineage and source["revision"] == revision:
                    raise GenealogyError("duplicate revision for one source lineage")
            first = lineage not in active_lineage
            sources[sid] = {
                "id": sid, "lineage_id": lineage, "revision": revision,
                "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                "available_tick": available, "active": first,
                "registered_seq": seq,
            }
            if first:
                active_lineage[lineage] = sid

        elif kind == "SOURCE_SUPERSEDE":
            data = _fields(data, {"old_source_id", "new_source_id", "reason"}, kind)
            old = _text(data["old_source_id"], "old_source_id")
            new = _text(data["new_source_id"], "new_source_id")
            _text(data["reason"], "reason")
            if old == new or old not in sources or new not in sources:
                raise GenealogyError("unknown or identical supersession references")
            a, b = sources[old], sources[new]
            if (a["lineage_id"] != b["lineage_id"]
                    or active_lineage[a["lineage_id"]] != old
                    or b["active"] or b["registered_seq"] <= a["registered_seq"]
                    or b["available_tick"] > tick):
                raise GenealogyError("supersession must replace active lineage with staged successor")
            a["active"] = False
            b["active"] = True
            active_lineage[a["lineage_id"]] = new
            for witness in evidence.values():
                if witness["source_id"] in (old, new):
                    claims[witness["claim_id"]]["touched_seq"] = seq

        elif kind == "CLAIM_OPEN":
            data = _fields(data, {"claim_id", "statement", "depends_on"}, kind)
            cid = _text(data["claim_id"], "claim_id")
            _text(data["statement"], "claim.statement")
            parents = _ids(data["depends_on"], "claim.depends_on")
            if cid in claims or cid in parents or any(p not in claims for p in parents):
                raise GenealogyError("claim ID or dependency invalid (future/cyclic edges rejected)")
            claims[cid] = {
                "id": cid, "statement_sha256": hashlib.sha256(
                    data["statement"].encode("utf-8")).hexdigest(),
                "depends_on": list(parents),
                "created_seq": seq, "touched_seq": seq, "review": None,
            }

        elif kind == "OBSERVATION_ADD":
            data = _fields(data, {
                "observation_id", "claim_id", "source_id", "stance", "finding",
            }, kind)
            eid = _text(data["observation_id"], "observation_id")
            cid = _text(data["claim_id"], "claim_id")
            sid = _text(data["source_id"], "source_id")
            stance = data["stance"]
            finding = _text(data["finding"], "finding")
            if stance not in STANCES or not isinstance(stance, str):
                raise GenealogyError("invalid observation stance")
            if eid in evidence or cid not in claims or sid not in sources:
                raise GenealogyError("duplicate or unknown observation, claim or source")
            if not sources[sid]["active"] or sources[sid]["available_tick"] > tick:
                raise GenealogyError("observation must be based on an active available source")
            evidence[eid] = {
                "id": eid, "claim_id": cid, "source_id": sid, "stance": stance,
                "finding_sha256": hashlib.sha256(finding.encode("utf-8")).hexdigest(),
                "recorded_seq": seq, "retracted_seq": None,
                "retraction_reason": None,
            }
            claims[cid]["touched_seq"] = seq

        elif kind == "OBSERVATION_RETRACT":
            data = _fields(data, {"observation_id", "reason"}, kind)
            eid = _text(data["observation_id"], "observation_id")
            reason = _text(data["reason"], "retraction reason")
            if eid not in evidence or evidence[eid]["retracted_seq"] is not None:
                raise GenealogyError("observation missing or already retracted")
            evidence[eid]["retracted_seq"] = seq
            evidence[eid]["retraction_reason"] = reason
            claims[evidence[eid]["claim_id"]]["touched_seq"] = seq

        elif kind == "REVIEW_ACCEPT":
            data = _fields(data, {
                "claim_id", "basis_ids", "review_note",
            }, kind)
            cid = _text(data["claim_id"], "claim_id")
            basis = _ids(data["basis_ids"], "basis_ids")
            _text(data["review_note"], "review_note")
            if cid not in claims or not basis:
                raise GenealogyError("review needs an existing claim and supporting basis")
            current = [obs for obs in evidence.values()
                       if obs["claim_id"] == cid and _evidence_current(obs, sources)]
            supporters = sorted(o["id"] for o in current if o["stance"] == "SUPPORT")
            if sorted(basis) != supporters or any(
                    obs["stance"] == "CHALLENGE" for obs in current):
                raise GenealogyError("review cannot omit current support or ignore counterevidence")
            statuses = _claim_statuses(claims, evidence, sources)
            dependencies = claims[cid]["depends_on"]
            if any(statuses[d] != CURRENT for d in dependencies):
                raise GenealogyError("review cannot bypass unresolved upstream claim")
            claims[cid]["review"] = {
                "seq": seq, "event_sha256": row["event_sha256"],
                "basis_ids": sorted(basis),
                "upstream_reviews": {
                    dep: claims[dep]["review"]["event_sha256"]
                    for dep in dependencies
                },
            }

        else:
            raise GenealogyError("unknown event type")

        statuses = _claim_statuses(claims, evidence, sources)
        for cid in sorted(statuses):
            if prior_status.get(cid) != statuses[cid]:
                transitions.append({
                    "seq": seq, "tick": tick, "claim_id": cid,
                    "from": prior_status.get(cid),
                    "to": statuses[cid], "cause_event_id": row["event_id"],
                })
        prior_status = statuses

    lineage_records = [
        {
            "lineage_id": lineage, "active_source_id": active_lineage[lineage],
            "versions": [
                {
                    "source_id": source["id"],
                    "revision": source["revision"],
                    "body_sha256": source["body_sha256"],
                    "available_tick": source["available_tick"],
                    "state": ("ACTIVE" if source["active"] else
                              "STAGED" if source["registered_seq"] >
                              sources[active_lineage[lineage]]["registered_seq"]
                              else "SUPERSEDED"),
                } for source in sorted(sources.values(), key=lambda s: s["registered_seq"])
                if source["lineage_id"] == lineage
            ],
        } for lineage in sorted(active_lineage)
    ]
    claim_records = [
        {
            "id": key, "status": prior_status[key],
            "depends_on": claims[key]["depends_on"],
            "statement_sha256": claims[key]["statement_sha256"],
            "review_event_sha256": (
                claims[key]["review"]["event_sha256"]
                if claims[key]["review"] else None
            ),
            "current_review_basis_ids": (
                claims[key]["review"]["basis_ids"]
                if claims[key]["review"] else []
            ),
        } for key in sorted(claims)
    ]
    observation_records = [
        {
            "id": ev["id"], "claim_id": ev["claim_id"],
            "source_id": ev["source_id"], "stance": ev["stance"],
            "finding_sha256": ev["finding_sha256"],
            "recorded_seq": ev["recorded_seq"],
            "retracted_seq": ev["retracted_seq"],
            "retraction_reason": ev["retraction_reason"],
            "currently_applicable": _evidence_current(ev, sources),
        } for ev in sorted(evidence.values(), key=lambda e: e["recorded_seq"])
    ]
    return {
        "schema": "workcoord.knowledge-genealogy-checkpoint/v0",
        "status": "PUBLIC_SYNTHETIC_DECLARATIONS_ONLY",
        "event_count": at_seq,
        "prefix_head_sha256": (
            records[at_seq - 1]["event_sha256"] if at_seq else ZERO_HASH
        ),
        "lineages": lineage_records, "claims": claim_records,
        "observations": observation_records, "transitions": transitions,
        "knowledge_promotion": "NOT_GRANTED",
        "external_source_authenticity_verified": False,
        "independent_scientific_validation": False,
        "execution_authority": "NONE",
        "work_ownership": "NOT_ASSIGNED",
        "model_learning_or_training_performed": False,
        "note": (
            "Historical observations and superseded revisions remain in the "
            "append-only log; advisory review never becomes independent truth."
        ),
    }


def evaluate_actions(actions: list, *, at_seq: int | None = None) -> dict:
    """Convenience only: no authenticated input, no database or live agent."""
    return replay_events(seal_actions(actions), at_seq=at_seq)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("actions", help="Path to fictional JSON action array")
    parser.add_argument("--at-seq", type=int)
    args = parser.parse_args(argv)
    actions = json.loads(Path(args.actions).read_text(encoding="utf-8"))
    if isinstance(actions, dict):
        actions = actions["actions"]
    print(json.dumps(evaluate_actions(actions, at_seq=args.at_seq),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
