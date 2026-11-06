"""Full fictional WorkCoord evidence path with the EXISTING SQLite Ledger.

This stdlib-only study driver calls ContextNavigator, the four advisory
evaluators, the existing Ledger lease/fence/approval transitions, and an
independently computed *synthetic* delivery oracle. No new coordinator,
production authority, external agent, API, authenticated reviewer or secret.

The driver must check advisory assessments again before completion because
the Ledger intentionally does NOT enforce the external advisory contracts.
DO NOT use this driver as an authorization or security boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .evaluator import issue_delivery_attestation
from .intelligence import ContextNavigator
from .ledger import GateError, Ledger
from .vertical_integration import evaluate_vertical
from .vertical_integration_suite import load_catalog, materialize_case

FIXTURE = Path(__file__).resolve().parents[2] / "examples" / "full-ledger-cycle-v0.json"
FIXTURE_SCHEMA = "workcoord.full-ledger-cycle-fixture/v0"
READY = "ADVISORY_CANDIDATE_FOR_EXTERNAL_ACCEPTANCE"
# Deliberately disclosed, fictional local test key. NOT a production secret.
FIXTURE_TEST_KEY = b"public-full-ledger-cycle-fictional-key-v0"


class CycleInputError(ValueError):
    """The *development fixture* does not bind the same source and issue."""


def _digest(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def read_fixture() -> dict:
    result = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if not isinstance(result, dict) or result.get("schema") != FIXTURE_SCHEMA:
        raise CycleInputError("unknown public synthetic cycle fixture")
    return result


def load_packets(fixture: dict) -> dict[str, dict]:
    """Use the already-published vertical fixture assembler; do not copy evaluators."""
    catalog, _ = load_catalog()
    by_id = {item["id"]: item for item in catalog["cases"]}
    current = materialize_case(catalog, by_id[fixture["base_current_case_id"]])
    stale = materialize_case(catalog, by_id[fixture["base_stale_revision_case_id"]])
    fresh = materialize_case(catalog, {"patches": fixture["rechecked_patches"]})
    if (current["manifest"]["issue_id"] != stale["manifest"]["issue_id"]
            or current["manifest"]["issue_id"] != fresh["manifest"]["issue_id"]
            or current["manifest"]["proposal_id"] != fresh["manifest"]["proposal_id"]):
        raise CycleInputError("issue and remedy identity must survive revalidation")
    return {"original": current, "stale": stale, "fresh": fresh}


def investigate_and_evaluate(packet: dict, documents: list, *, at_seq: int) -> dict:
    """Select current primary source before running independently typed stages.

    The selector uses public, hand-authored signals; it is not a source oracle.
    """
    manifest = packet["manifest"]
    navigator = ContextNavigator(
        documents, current_revision=manifest["source_revision"],
        issue_tags=["duplicate-notification"], max_chars=1400,
    )
    sequence = (
        ("worker", "focused", "Inspect current fictional worker source."),
        ("queue", "focused", "Follow the worker-to-queue dependency."),
        ("api", "focused", "Inspect producer-side contrary explanations."),
    )
    steps = [navigator.navigate(sector=sector, perspective="reliability",
                                depth=depth, reason=why)
             for sector, depth, why in sequence]
    selected = navigator.context()
    primary = [s for s in selected if s["id"] == manifest["primary_source_id"]]
    if len(primary) != 1 or not primary[0]["current_revision"]:
        raise CycleInputError("the primary source must actually be read at the reviewed revision")
    if _digest(primary[0]["body"]) != manifest["primary_source_sha256"]:
        raise CycleInputError("read source does not match the cross-stage content hash")
    if primary[0]["maturity"] == "historical":
        raise CycleInputError("historical-only source cannot serve as current basis")
    investigation = navigator.assess(["H-retry", "H-producer"])
    # The preliminary hypothesis does NOT itself authorize an action or certify a diagnosis.
    advisory = evaluate_vertical(packet, at_seq=at_seq)
    if (advisory["issue_id"] != manifest["issue_id"]
            or advisory["source_revision"] != manifest["source_revision"]):
        raise CycleInputError("advisory receipt cannot be stitched to another incident")
    return {
        "schema": "workcoord.full-ledger-investigation/v0",
        "status": advisory["status"],
        "issue_id": advisory["issue_id"],
        "proposal_id": advisory["proposal_id"],
        "source_revision": advisory["source_revision"],
        "advisory_checkpoint_sha256": advisory["checkpoint_sha256"],
        "genealogy_prefix_head_sha256": advisory["knowledge_prefix_head_sha256"],
        "context_primary_source_sha256": manifest["primary_source_sha256"],
        "context_source_ids": [s["id"] for s in selected],
        "context_chars": navigator.total_chars(),
        "navigation_sectors": [s["sector"] for s in steps],
        "preliminary_hypothesis": investigation["leading_hypothesis"],
        "source_epoch_drift": advisory["source_epoch_drift"],
        "stage_status": advisory["stage_status"],
        "reason_codes": advisory["reason_codes"],
        "source_authenticity_verified": False,
        "independent_outcome_verified": False,
        "authorization": "NONE",
    }


def _row_receipt(db: Ledger, *, name: str, status: str, observations: list[dict]) -> dict:
    item = db.get(name)
    with db._lock:
        tail = db.db.execute(
            "SELECT event_hash FROM events ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        clock = db.db.execute("SELECT tick FROM logical_clock WHERE id=1").fetchone()[0]
    return {
        "status": status, "work_status": item["status"],
        "work_revision": item["revision"], "generation": item["generation"],
        "lease_clock": clock, "evidence_id": item["evidence_id"],
        "approved_by": item["approved_by"], "completion_receipt_sha256": item["receipt"],
        "event_count": db.event_count(),
        "event_chain_sha256": tail[0] if tail else "0" * 64,
        "event_chain_valid": db.verify_event_chain(),
        "evaluations": observations,
        "ledger_enforces_advisory_state": False,
        "external_reviewer_authenticated": False,
        "synthetic_evaluator_key_is_public": True,
        "real_agent_used": False,
        "real_world_outcome_verified": False,
        "production_authorization": "NONE",
    }


def _attempt_completion(db: Ledger, packet: dict, advisory: dict,
                        fixture: dict, generation: int, tick: list[int]) -> str:
    """The *study driver* checks the advisory state and ledger revision separately.

    The Ledger's complete() does not import the advisory evaluator. A caller
    bypassing this driver is outside this experimental safety contract.
    """
    if advisory["status"] != READY:
        return "HOLD_ADVISORY"
    if (advisory["source_revision"] != packet["manifest"]["source_revision"]
            or db.get(fixture["work_id"])["revision"] != advisory["source_revision"]):
        return "HOLD_REVISION_MISMATCH"
    tick[0] += 1
    db.complete(fixture["work_id"], fixture["synthetic_owner"],
                generation, now=987654321)
    return "DONE_SYNTHETIC"


def _evaluate_original(fixture: dict, packet: dict) -> dict:
    return investigate_and_evaluate(
        packet, fixture["current_documents"], at_seq=fixture["original_cut"],
    )


def _make_attestation(fixture: dict, *, revision: str, evidence_id: str,
                      deliveries: list[str]) -> dict:
    return issue_delivery_attestation(
        FIXTURE_TEST_KEY, evidence_id, fixture["work_id"], revision,
        fixture["fictional_logical_events"], deliveries,
    )


def run_case(mode: str, *, fixture: dict | None = None,
             fresh_packet: dict | None = None,
             fresh_documents: list | None = None,
             delivered_override: list[str] | None = None) -> dict:
    """Run one isolated development scenario with a new in-memory SQLite Ledger.

    Allowed modes have explicit outcomes; the fixture's expected results are
    never consulted by any of the four evaluators or the Ledger.
    """
    modes = {"baseline", "late_counterevidence", "revision_recheck", "behavior_failure"}
    if mode not in modes:
        raise CycleInputError("unknown public cycle scenario")
    fixture = read_fixture() if fixture is None else fixture
    packets = load_packets(fixture)
    packet = packets["original"]
    first = _evaluate_original(fixture, packet)
    if first["status"] != READY:
        raise CycleInputError("baseline must have no local advisory blocker")
    name, owner = fixture["work_id"], fixture["synthetic_owner"]
    rev = packet["manifest"]["source_revision"]
    if name != packet["manifest"]["issue_id"]:
        raise CycleInputError("Ledger work ID cannot differ from the investigated incident")
    # Host-injected, deliberately synthetic fixture clock. Actor-provided
    # enormous timestamps below must not determine expiry.
    clock = [1]
    db = Ledger(verification_key=FIXTURE_TEST_KEY, time_source=lambda: clock[0])
    phases: list[dict] = [dict(phase="initial_review", **first)]
    try:
        db.create(name, rev, authority="REVIEW_REQUIRED")
        generation = db.claim(name, owner, now=12345678, ttl=40)
        if db.get(name)["generation"] != generation:
            raise AssertionError("fencing generation unexpectedly changed")
        try:
            db.claim(name, fixture["synthetic_other_actor"], now=987654321, ttl=40)
        except GateError:
            pass
        else:
            raise AssertionError("a second owner acquired an unexpired lease")

        delivered = (
            delivered_override if delivered_override is not None else
            fixture["declared_failing_deliveries"] if mode == "behavior_failure"
            else fixture["declared_successful_deliveries"]
        )
        first_attestation = _make_attestation(
            fixture, revision=rev, evidence_id="delivery-proof-r2",
            deliveries=delivered,
        )
        db.record_attested_evidence(first_attestation)
        if mode == "behavior_failure":
            if first_attestation["passed"]:
                raise AssertionError("negative control unexpectedly passed the oracle")
            before = db.event_count()
            try:
                db.submit(name, owner, generation, now=10000000,
                          evidence_id="delivery-proof-r2")
            except GateError:
                pass
            else:
                raise AssertionError("nonpassing external proof was admitted")
            if db.event_count() != before:
                raise AssertionError("rejected submission mutated the event chain")
            return _row_receipt(db, name=name, status="HOLD_EXTERNAL_ORACLE",
                                observations=phases)

        clock[0] = 2
        db.submit(name, owner, generation, now=12345678,
                  evidence_id="delivery-proof-r2")
        clock[0] = 3
        db.verify(name, owner, generation, now=12345678)
        # Public synthetic reviewer name. This only checks distinct strings.
        db.approve(name, fixture["synthetic_reviewer"])

        if mode == "late_counterevidence":
            contradicted = investigate_and_evaluate(
                packet, fixture["current_documents"],
                at_seq=fixture["contradiction_cut"],
            )
            phases.append(dict(phase="late_challenge", **contradicted))
            result = _attempt_completion(db, packet, contradicted,
                                         fixture, generation, clock)
            if result != "HOLD_ADVISORY":
                raise AssertionError("late counterexample was incorrectly promoted")
            return _row_receipt(db, name=name, status="HOLD_COUNTEREVIDENCE",
                                observations=phases)

        if mode == "revision_recheck":
            new = packets["fresh"] if fresh_packet is None else fresh_packet
            revised_documents = (
                fixture["rechecked_documents"] if fresh_documents is None
                else fresh_documents
            )
            db.change_revision(name, new["manifest"]["source_revision"])
            invalidated = db.get(name)
            if (invalidated["status"] != "CLAIMED"
                    or invalidated["evidence_id"] is not None
                    or invalidated["approved_by"] is not None
                    or invalidated["generation"] != generation):
                raise AssertionError("revision transition retained stale verification")
            for operation in (
                lambda: db.complete(name, owner, generation, now=12345678),
                lambda: db.submit(name, owner, generation, now=12345678,
                                  evidence_id="delivery-proof-r2"),
            ):
                before = db.event_count()
                try:
                    operation()
                except GateError:
                    if db.event_count() != before:
                        raise AssertionError("rejected obsolete transition mutated ledger")
                else:
                    raise AssertionError("old evidence was accepted after revision change")
            stale = investigate_and_evaluate(
                packets["stale"], fixture["current_documents"],
                at_seq=fixture["stale_revision_cut"],
            )
            phases.append(dict(phase="stale_original_review", **stale))
            if stale["status"] != "HOLD_REASSESS_REVISION":
                raise AssertionError("old stage evaluations unexpectedly survived supersession")
            # New review packet and source documents must be supplied explicitly.
            # The public fixture's patch list is an authored *reinspection*, not
            # an automatic state promotion by the Ledger.
            rechecked = investigate_and_evaluate(
                new, revised_documents, at_seq=fixture["rechecked_cut"],
            )
            phases.append(dict(phase="fresh_explicit_recheck", **rechecked))
            if rechecked["status"] != READY:
                return _row_receipt(db, name=name,
                                    status="HOLD_RECHECK_NOT_ADMISSIBLE",
                                    observations=phases)
            if new["manifest"]["source_revision"] != db.get(name)["revision"]:
                return _row_receipt(db, name=name, status="HOLD_REVISION_MISMATCH",
                                    observations=phases)
            fresh_attestation = _make_attestation(
                fixture, revision=new["manifest"]["source_revision"],
                evidence_id="delivery-proof-r3",
                deliveries=fixture["declared_successful_deliveries"],
            )
            db.record_attested_evidence(fresh_attestation)
            clock[0] = 4
            db.submit(name, owner, generation, now=12345678,
                      evidence_id="delivery-proof-r3")
            clock[0] = 5
            db.verify(name, owner, generation, now=12345678)
            try:
                db.complete(name, owner, generation, now=12345678)
            except GateError:
                pass
            else:
                raise AssertionError("new revision bypassed mandatory approval")
            db.approve(name, fixture["synthetic_reviewer"])
            outcome = _attempt_completion(db, new, rechecked, fixture,
                                          generation, clock)
            if outcome != "DONE_SYNTHETIC":
                raise AssertionError("fresh review and revised proof did not complete")
            return _row_receipt(db, name=name,
                                status="DONE_AFTER_EXPLICIT_REVALIDATION",
                                observations=phases)

        result = _attempt_completion(db, packet, first, fixture, generation, clock)
        if result != "DONE_SYNTHETIC":
            raise AssertionError("the bounded baseline case did not complete")
        return _row_receipt(db, name=name, status="DONE_SYNTHETIC",
                            observations=phases)
    finally:
        db.close()


def run_suite() -> dict:
    data = read_fixture()
    cases = ("baseline", "late_counterevidence",
             "revision_recheck", "behavior_failure")
    outcomes = {mode: run_case(mode, fixture=data) for mode in cases}
    return {
        "schema": "workcoord.full-ledger-cycle-results/v0",
        "status": "SYNTHETIC_AUTHOR_AUTHORED_DEVELOPMENT_FIXTURE_ONLY",
        "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        "cases": outcomes,
        "case_count": len(outcomes),
        "external_agent_benchmark_run": False,
        "codex_api_used": False,
        "authenticated_reviewer_implemented": False,
        "ledger_enforces_advisory_state": False,
        "source_authenticity_verified": False,
        "final_world_outcome_verified": False,
    }


def main(argv: list[str] | None = None) -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output", help="Save deterministic public JSON receipt")
    args = cli.parse_args(argv)
    report = run_suite()
    serialized = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized, encoding="utf-8")
        print(json.dumps({
            "case_count": report["case_count"],
            "outcomes": {k: v["status"] for k, v in report["cases"].items()},
            "receipt": str(path),
        }, sort_keys=True))
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
