"""Synthetic evaluator receipts computed from observed data, not caller-supplied PASS.

This is a teaching contract, not a security boundary: anyone with the key or
write access to the SQLite database can forge records.
"""
import hashlib
import hmac
import json
import re
from .simulator import semantic_oracle

SCHEMA = "workcoord.synthetic-evidence/v1"

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

def _check_key(key):
    if not isinstance(key, bytes) or len(key) < 16:
        raise ValueError("a synthetic evaluator key of at least 16 bytes is required")

def issue_delivery_attestation(key, evidence_id, revision, logical_events, observed_deliveries):
    """The evaluator computes the result, independently of any claimed status.

    A real evaluator must control its ground truth, source identity and key.
    """
    _check_key(key)
    if not isinstance(evidence_id, str) or not evidence_id or not isinstance(revision, str) or not revision:
        raise ValueError("evidence id and revision required")
    if (not isinstance(logical_events, list) or not logical_events or
            not isinstance(observed_deliveries, list) or
            not all(isinstance(v, str) for v in logical_events + observed_deliveries)):
        raise ValueError("invalid fictional delivery fixture")
    artifact = canonical({"logical_events": logical_events, "observed_deliveries": observed_deliveries}).encode()
    statement = {
        "schema": SCHEMA,
        "evidence_id": evidence_id,
        "revision": revision,
        "oracle": "one-delivery-per-distinct-event/v1",
        "artifact_sha256": hashlib.sha256(artifact).hexdigest(),
        "passed": bool(semantic_oracle(logical_events, observed_deliveries)),
    }
    mac = hmac.new(key, canonical(statement).encode(), hashlib.sha256).hexdigest()
    return {**statement, "mac": mac}

def verify_attestation(receipt, key):
    """Fail closed for changed fields, wrong keys and malformed receipts."""
    try:
        _check_key(key)
        if not isinstance(receipt, dict) or set(receipt) != {
            "schema", "evidence_id", "revision", "oracle", "artifact_sha256", "passed", "mac",
        }:
            return False
        if (receipt["schema"] != SCHEMA or
                receipt["oracle"] != "one-delivery-per-distinct-event/v1" or
                not isinstance(receipt["evidence_id"], str) or not receipt["evidence_id"] or
                not isinstance(receipt["revision"], str) or not receipt["revision"] or
                not isinstance(receipt["passed"], bool)):
            return False
        if not isinstance(receipt["artifact_sha256"], str) or not re.fullmatch("[0-9a-f]{64}", receipt["artifact_sha256"]):
            return False
        if not isinstance(receipt["mac"], str) or not re.fullmatch("[0-9a-f]{64}", receipt["mac"]):
            return False
        payload = {k: v for k, v in receipt.items() if k != "mac"}
        expected = hmac.new(key, canonical(payload).encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(receipt["mac"], expected)
    except (ValueError, TypeError):
        return False
