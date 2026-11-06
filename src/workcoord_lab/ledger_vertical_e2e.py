"""Synthetic, bounded vertical-to-Ledger proof path over EXISTING modules.

This is intentionally NOT a coordinator, persistent service, model/agent, source
authenticator, or execution-authorization bridge. It exercises existing advisory
gates, context selection, synthetic semantic evaluator, revision-bound SQLite
work state, lease fencing, required review and completion in one fictional case.
The caller must supply current packets and sources: no real source clock exists.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import secrets

from .evaluator import issue_delivery_attestation
from .intelligence import ContextNavigator
from .intelligence_demo import fixture as navigation_fixture
from .ledger import GateError, Ledger
from .vertical_integration import evaluate_vertical
from .vertical_integration_suite import load_catalog, materialize_case

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT / "examples" / "ledger-vertical-fixture-v0.json"
SCHEMA = "workcoord.ledger-vertical-fixture/v0"
RESULT_SCHEMA = "workcoord.ledger-vertical-result/v0"
CANDIDATE = "ADVISORY_CANDIDATE_FOR_EXTERNAL_ACCEPTANCE"
ELIGIBLE = "SYNTHETIC_SANDBOX_EVALUATION_ELIGIBLE"


class BridgeHold(ValueError):
    """Explicitly blocked fictional composition; no ledger transition."""


def sha_body(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def load_fixture() -> dict:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError("unexpected public synthetic E2E fixture")
    return data


def packets(fixture: dict) -> tuple[dict, dict, dict]:
    """Explicit fixture patches, not automatic real-world source rebinding."""
    catalog, _ = load_catalog()
    first = deepcopy(catalog["base_packet"])
    revised = materialize_case(
        catalog, {"patches": fixture["revision_patches"]})
    late_case = next(
        (x for x in catalog["cases"] if x["id"] == fixture["base_vertical_case"]),
        None)
    if late_case is None:
        raise ValueError("public vertical fixture case missing")
    late = materialize_case(catalog, late_case)
    if (first["manifest"]["source_revision"] ==
            revised["manifest"]["source_revision"]):
        raise ValueError("changed fixture must identify a different revision")
    return first, revised, late


def evaluate_context_and_decision(
    packet: dict, *, at_seq: int, primary_document: dict,
    background_documents: list[dict], max_chars: int,
) -> dict:
    """Advisory stage composition, never an authorization or proof receipt."""
    manifest = packet["manifest"]
    nav = ContextNavigator(
        deepcopy(background_documents) + [deepcopy(primary_document)],
        current_revision=manifest["source_revision"],
        issue_tags=["duplicate-notification"], max_chars=max_chars,
    )
    # Explicit cross-sector navigation, never automatic dependency expansion.
    steps = []
    for sector in ("worker", "queue", "api"):
        steps.append(nav.navigate(
            sector=sector, perspective="reliability", depth="focused",
            reason="Fictional investigation of a shared notification issue.",
        ))
    assessment = nav.assess(["producer-duplicates", "ack-retry"])
    vertical = evaluate_vertical(packet, at_seq=at_seq)
    selected = {doc["id"]: doc for doc in nav.context()}
    required_id = manifest["primary_observation_id"]
    document = selected.get(required_id)

    if document is None:
        reason = "PRIMARY_SOURCE_NOT_READ"
    elif (document.get("source_revision") != manifest["source_revision"]
          or sha_body(document["body"]) != manifest["primary_source_sha256"]):
        reason = "PRIMARY_CONTEXT_REVISION_OR_BODY_MISMATCH"
    elif vertical["status"] != CANDIDATE:
        reason = "VERTICAL_" + vertical["status"]
    else:
        reason = "NO_LOCAL_BLOCKER"

    return {
        "schema": "workcoord.ledger-vertical-admission/v0",
        "status": ELIGIBLE if reason == "NO_LOCAL_BLOCKER" else "HOLD",
        "reason": reason,
        "issue_id": manifest["issue_id"],
        "source_revision": manifest["source_revision"],
        "primary_observation_id": required_id,
        "primary_source_sha256": manifest["primary_source_sha256"],
        "selected_context_source_ids": sorted(selected),
        "unique_context_body_chars": nav.total_chars(),
        "navigator_status": assessment["status"],
        "requires_independent_test": assessment["requires_independent_test"],
        "vertical_status": vertical["status"],
        "vertical_checkpoint_sha256": vertical["checkpoint_sha256"],
        "knowledge_prefix_sha256": vertical["knowledge_prefix_head_sha256"],
        "source_epoch_drift": vertical["source_epoch_drift"],
        "context_sectors_visited": ["worker", "queue", "api"],
        "context_budget_exclusion_count": sum(
            len(s["gaps"]["unread_due_to_budget"]) for s in steps
        ),
        "authorization": "NONE",
        "trusted_source_authentication": False,
        "real_agent_evaluation": False,
    }


def _require_gate(db: Ledger, packet: dict, *, at_seq: int,
                  primary_document: dict, background_documents: list[dict],
                  max_chars: int, work_id: str) -> dict:
    """Recompute every stage rather than trusting a caller-supplied status."""
    result = evaluate_context_and_decision(
        packet, at_seq=at_seq, primary_document=primary_document,
        background_documents=background_documents, max_chars=max_chars)
    if result["status"] != ELIGIBLE:
        raise BridgeHold("HOLD_" + result["reason"])
    state = db.get(work_id)
    if state["id"] != result["issue_id"]:
        raise BridgeHold("HOLD_WORK_IDENTITY_MISMATCH")
    if state["revision"] != result["source_revision"]:
        raise BridgeHold("HOLD_LEDGER_SOURCE_REVISION_CHANGED")
    if state["authority"] != "REVIEW_REQUIRED":
        raise BridgeHold("HOLD_UNEXPECTED_SANDBOX_AUTHORITY")
    return result


def submit_under_gate(
    db: Ledger, packet: dict, *, at_seq: int, primary_document: dict,
    background_documents: list[dict], max_chars: int,
    work_id: str, owner: str, generation: int, now: int,
    evidence_id: str, key: bytes, logical_events: list[str],
    observed_deliveries: list[str],
) -> dict:
    gate = _require_gate(
        db, packet, at_seq=at_seq, primary_document=primary_document,
        background_documents=background_documents, max_chars=max_chars,
        work_id=work_id,
    )
    # The evaluator, not a user-supplied PASS flag, computes the semantic result.
    receipt = issue_delivery_attestation(
        key, evidence_id, work_id, gate["source_revision"],
        logical_events, observed_deliveries,
    )
    if not receipt["passed"]:
        raise BridgeHold("HOLD_SYNTHETIC_BEHAVIOR_ORACLE_FAILED")
    db.record_attested_evidence(receipt)
    db.submit(work_id, owner, generation, now=now, evidence_id=evidence_id)
    return {
        "evidence_id": evidence_id,
        "revision": receipt["revision"],
        "artifact_sha256": receipt["artifact_sha256"],
        "synthetic_oracle_passed": receipt["passed"],
        "evaluator_authenticity": "RUNTIME_EPHEMERAL_TEST_KEY_NOT_EXTERNAL_TRUST",
        "ledger_status": db.get(work_id)["status"],
    }


def verify_under_gate(
    db: Ledger, packet: dict, *, at_seq: int, primary_document: dict,
    background_documents: list[dict], max_chars: int, work_id: str,
    owner: str, generation: int, now: int,
) -> None:
    _require_gate(
        db, packet, at_seq=at_seq, primary_document=primary_document,
        background_documents=background_documents, max_chars=max_chars,
        work_id=work_id,
    )
    db.verify(work_id, owner, generation, now=now)


def complete_under_gate(
    db: Ledger, packet: dict, *, at_seq: int, primary_document: dict,
    background_documents: list[dict], max_chars: int, work_id: str,
    owner: str, generation: int, now: int,
) -> str:
    _require_gate(
        db, packet, at_seq=at_seq, primary_document=primary_document,
        background_documents=background_documents, max_chars=max_chars,
        work_id=work_id,
    )
    return db.complete(work_id, owner, generation, now=now)


def _public_event_types(db: Ledger) -> list[str]:
    """Do not publish HMACs, source bodies, private logs, or raw attestations."""
    with db._lock:
        return [
            json.loads(row[0])["type"] for row in db.db.execute(
                "SELECT payload FROM events ORDER BY seq")
        ]


def run_walkthrough() -> dict:
    """A single two-revision replay with deliberately rejected regressions.

    The HMAC secret is generated in runtime memory and NEVER written or printed.
    The public receipt intentionally excludes secret-dependent hash-chain heads.
    """
    fixture = load_fixture()
    raw = FIXTURE_PATH.read_bytes()
    first, revised, late = packets(fixture)
    corpus = navigation_fixture()["documents"]
    old_doc = fixture["initial_primary_document"]
    new_doc = fixture["revised_primary_document"]
    work_id, owner, reviewer = (
        fixture["work_id"], fixture["owner_label"], fixture["reviewer_label"])
    budget = fixture["context_budget_chars"]
    old_cut, new_cut, late_cut = (
        fixture["base_history_cut"], fixture["revised_history_cut"],
        fixture["late_counterevidence_history_cut"])

    first_gate = evaluate_context_and_decision(
        first, at_seq=old_cut, primary_document=old_doc,
        background_documents=corpus, max_chars=budget)
    late_gate = evaluate_context_and_decision(
        late, at_seq=late_cut, primary_document=old_doc,
        background_documents=corpus, max_chars=budget)
    stale = deepcopy(first)
    stale["knowledge_actions"] = deepcopy(revised["knowledge_actions"])
    stale_gate = evaluate_context_and_decision(
        stale, at_seq=new_cut, primary_document=old_doc,
        background_documents=corpus, max_chars=budget)
    refreshed_gate = evaluate_context_and_decision(
        revised, at_seq=new_cut, primary_document=new_doc,
        background_documents=corpus + [old_doc], max_chars=budget)
    if first_gate["status"] != ELIGIBLE or refreshed_gate["status"] != ELIGIBLE:
        raise BridgeHold("public positive fixture failed advisory admission")
    if late_gate["status"] != "HOLD" or stale_gate["status"] != "HOLD":
        raise BridgeHold("public negative fixture failed to block")

    # Runtime-only random key, not stored in Git, fixture, receipt, or output.
    key = secrets.token_bytes(32)
    logical_tick = [10]
    db = Ledger(verification_key=key, time_source=lambda: logical_tick[0])
    probes = {}
    try:
        db.create(work_id, first["manifest"]["source_revision"],
                  authority="REVIEW_REQUIRED")
        generation = db.claim(work_id, owner, now=9999, ttl=40)
        before = db.event_count()
        try:
            db.submit(work_id, "wrong-owner", generation, now=1000000,
                      evidence_id="no-proof")
        except GateError:
            probes["rejected_owner_fenced"] = (
                db.event_count() == before
                and db.db.execute(
                    "SELECT tick FROM logical_clock WHERE id=1"
                ).fetchone()[0] == 10
            )
        else:
            probes["rejected_owner_fenced"] = False

        # Do not allow forged status flags: compute from observed deliveries.
        try:
            submit_under_gate(
                db, first, at_seq=old_cut, primary_document=old_doc,
                background_documents=corpus, max_chars=budget,
                work_id=work_id, owner=owner, generation=generation, now=11,
                evidence_id="rejected-duplicate-r2", key=key,
                logical_events=fixture["logical_events"],
                observed_deliveries=fixture["broken_delivery_observations"])
        except BridgeHold:
            probes["duplicate_delivery_oracle_rejected"] = (
                db.get(work_id)["status"] == "CLAIMED"
            )
        else:
            probes["duplicate_delivery_oracle_rejected"] = False

        logical_tick[0] = 11
        initial_proof = submit_under_gate(
            db, first, at_seq=old_cut, primary_document=old_doc,
            background_documents=corpus, max_chars=budget, work_id=work_id,
            owner=owner, generation=generation, now=11,
            evidence_id="accepted-delivery-r2", key=key,
            logical_events=fixture["logical_events"],
            observed_deliveries=fixture["correct_delivery_observations"])
        logical_tick[0] = 12
        verify_under_gate(
            db, first, at_seq=old_cut, primary_document=old_doc,
            background_documents=corpus, max_chars=budget, work_id=work_id,
            owner=owner, generation=generation, now=12)
        db.approve(work_id, reviewer)
        before_revision_state = db.get(work_id)

        # Revision change after verification invalidates old proof and approval.
        db.change_revision(work_id, revised["manifest"]["source_revision"])
        changed = db.get(work_id)
        try:
            complete_under_gate(
                db, first, at_seq=old_cut, primary_document=old_doc,
                background_documents=corpus, max_chars=budget, work_id=work_id,
                owner=owner, generation=generation, now=13)
        except BridgeHold:
            probes["old_gate_rejected_after_revision"] = True
        else:
            probes["old_gate_rejected_after_revision"] = False

        try:
            _require_gate(
                db, stale, at_seq=new_cut, primary_document=old_doc,
                background_documents=corpus, max_chars=budget, work_id=work_id)
        except BridgeHold:
            probes["reassessment_required_after_supersession"] = True
        else:
            probes["reassessment_required_after_supersession"] = False

        logical_tick[0] = 13
        try:
            db.submit(work_id, owner, generation, now=13,
                      evidence_id="accepted-delivery-r2")
        except GateError:
            probes["old_revision_proof_rejected"] = (
                db.get(work_id)["status"] == "CLAIMED")
        else:
            probes["old_revision_proof_rejected"] = False

        new_proof = submit_under_gate(
            db, revised, at_seq=new_cut, primary_document=new_doc,
            background_documents=corpus + [old_doc], max_chars=budget,
            work_id=work_id, owner=owner, generation=generation, now=13,
            evidence_id="accepted-delivery-r3", key=key,
            logical_events=fixture["logical_events"],
            observed_deliveries=fixture["correct_delivery_observations"])
        logical_tick[0] = 14
        verify_under_gate(
            db, revised, at_seq=new_cut, primary_document=new_doc,
            background_documents=corpus + [old_doc], max_chars=budget,
            work_id=work_id, owner=owner, generation=generation, now=14)
        try:
            complete_under_gate(
                db, revised, at_seq=new_cut, primary_document=new_doc,
                background_documents=corpus + [old_doc], max_chars=budget,
                work_id=work_id, owner=owner, generation=generation, now=15)
        except GateError:
            probes["new_review_required"] = (
                db.get(work_id)["approved_by"] is None)
        else:
            probes["new_review_required"] = False
        try:
            db.approve(work_id, owner)
        except GateError:
            probes["owner_cannot_self_approve"] = True
        else:
            probes["owner_cannot_self_approve"] = False
        db.approve(work_id, reviewer)
        logical_tick[0] = 15
        final_receipt = complete_under_gate(
            db, revised, at_seq=new_cut, primary_document=new_doc,
            background_documents=corpus + [old_doc], max_chars=budget,
            work_id=work_id, owner=owner, generation=generation, now=15)
        count = db.event_count()
        second_receipt = complete_under_gate(
            db, revised, at_seq=new_cut, primary_document=new_doc,
            background_documents=corpus + [old_doc], max_chars=budget,
            work_id=work_id, owner=owner, generation=generation, now=15)
        probes["duplicate_completion_idempotent"] = (
            second_receipt == final_receipt and db.event_count() == count)
        probes["late_counterevidence_blocks"] = late_gate["status"] == "HOLD"
        probes["source_revalidation_cleared_old_proof"] = (
            before_revision_state["status"] == "VERIFIED"
            and before_revision_state["approved_by"] == reviewer
            and changed["status"] == "CLAIMED"
            and changed["evidence_id"] is None
            and changed["approved_by"] is None
            and changed["generation"] == generation)
        return {
            "schema": RESULT_SCHEMA,
            "status": "PUBLIC_FICTIONAL_DEVELOPMENT_NOT_AGENT_BENCHMARK",
            "fixture_sha256": hashlib.sha256(raw).hexdigest(),
            "first_gate": first_gate,
            "late_counterevidence_gate": late_gate,
            "stale_source_gate": stale_gate,
            "refreshed_gate": refreshed_gate,
            "before_revision_ledger_status": before_revision_state["status"],
            "after_revision_ledger_status": changed["status"],
            "before_revision_proof": initial_proof,
            "after_revision_proof": new_proof,
            "final_ledger_status": db.get(work_id)["status"],
            "final_synthetic_completion_sha256": final_receipt,
            "ledger_generation": generation,
            "ledger_event_count": db.event_count(),
            "ledger_event_types": _public_event_types(db),
            "ledger_event_chain_valid": db.verify_event_chain(),
            "invariant_probes": probes,
            "synthetic_behavior_oracle": "one-delivery-per-distinct-event/v1",
            "external_source_authenticated": False,
            "reviewer_identity_authenticated": False,
            "independent_real_world_outcome_verified": False,
            "production_authorization": "NONE",
            "model_or_codex_api_used": False,
            "no_secrets_in_result": True,
            "note": "A synthetic Ledger DONE is not real-world acceptance; all reviews and packets are fictional.",
        }
    finally:
        db.close()


def main(argv: list[str] | None = None) -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output", help="Output redacted public JSON receipt")
    args = cli.parse_args(argv)
    outcome = run_walkthrough()
    body = json.dumps(outcome, sort_keys=True, indent=2) + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        print(json.dumps({
            "receipt": str(path), "status": outcome["final_ledger_status"],
            "probes": len(outcome["invariant_probes"]),
            "all_probes_pass": all(outcome["invariant_probes"].values()),
        }, sort_keys=True))
    else:
        print(body, end="")


if __name__ == "__main__":
    main()
