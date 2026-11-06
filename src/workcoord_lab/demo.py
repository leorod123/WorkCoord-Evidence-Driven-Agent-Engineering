"""Five-second demonstration of idempotency and evidence-gated completion."""

import json

from .ledger import Ledger
from .simulator import deliver, semantic_oracle


def main():
    logical_events = ["ticket-42-closed", "ticket-42-closed"]
    broken = deliver(logical_events)
    fixed = deliver(logical_events, idempotent=True)
    db = Ledger()
    try:
        db.create("fix-notifications", revision="synthetic-r1")
        gen = db.claim("fix-notifications", "agent-a", now=1, ttl=20)
        db.record_evidence("test-e1", "synthetic-r1", "test", passed=semantic_oracle(logical_events, fixed), artifact="sha256:synthetic-test-a")
        db.submit("fix-notifications", "agent-a", gen, now=2, evidence_id="test-e1")
        db.verify("fix-notifications", "agent-a", gen, now=3)
        receipt = db.complete("fix-notifications", "agent-a", gen, now=4)
        print(json.dumps({
            "environment": "fictional_demo", "before_deliveries": len(broken),
            "before_oracle_passed": semantic_oracle(logical_events, broken),
            "after_deliveries": len(fixed), "after_oracle_passed": semantic_oracle(logical_events, fixed),
            "work_status": db.get("fix-notifications")["status"], "receipt_sha256": receipt,
            "event_chain_valid": db.verify_event_chain(),
            "evaluation_claim": "deterministic_example_only_not_agent_benchmark",
        }, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
