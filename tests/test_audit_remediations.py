"""Independent-targeted adversarial controls A01-A05 plus read isolation.

All material is fictional and published. This file tests concrete contract
invariants identified by external static review; it is not a real-world
agent/benchmark correctness result or production security certification.
"""
from copy import deepcopy
import json
from pathlib import Path
import threading
import time
import unittest

from workcoord_lab.ledger import Ledger, GateError
from workcoord_lab.evaluator import issue_delivery_attestation
from workcoord_lab.knowledge_genealogy import evaluate_actions, verify_chain, seal_actions
from workcoord_lab.vertical_integration import evaluate_vertical
from workcoord_lab.vertical_integration_suite import load_catalog, materialize_case
from workcoord_lab.intelligence import ContextNavigator
from workcoord_lab.intelligence_demo import fixture as context_fixture
from workcoord_lab.research_quality import evaluate_research
from workcoord_lab.cognitive_perspectives import (
    InvalidPerspectivePacket, evaluate_perspectives,
)

ROOT = Path(__file__).resolve().parents[1]
KEY = b"public-fixture-only-not-a-secret"
RESEARCH = json.loads((ROOT / "examples" / "research-quality-cases-v0.json")
                      .read_text(encoding="utf-8"))
COGNITIVE = json.loads((ROOT / "examples" / "cognitive-perspective-cases-v0.json")
                       .read_text(encoding="utf-8"))
GENEALOGY = json.loads((ROOT / "examples" / "knowledge-genealogy-cases-v0.json")
                       .read_text(encoding="utf-8"))


def named(data, key):
    return deepcopy(next(x for x in data["cases"]
                         if x.get("case_id", x.get("id")) == key))


class AuditRemediationTests(unittest.TestCase):
    def test_rejected_actor_cannot_advance_lease_clock(self):
        db = Ledger(verification_key=KEY)
        self.addCleanup(db.close)
        db.create("case", "r1")
        generation = db.claim("case", "worker-A", 100, 10)
        db.record_attested_evidence(issue_delivery_attestation(
            KEY, "proof-A", "case", "r1", ["event", "event"], ["event"]
        ))
        before_tick = db.db.execute("SELECT tick FROM logical_clock WHERE id=1").fetchone()[0]
        before_count = db.event_count()
        with self.assertRaises(GateError):
            db.submit("case", "worker-B", generation, 1000, "proof-A")
        self.assertEqual(db.db.execute(
            "SELECT tick FROM logical_clock WHERE id=1").fetchone()[0], before_tick)
        self.assertEqual(db.event_count(), before_count)
        db.submit("case", "worker-A", generation, 101, "proof-A")
        self.assertEqual(db.get("case")["status"], "SUBMITTED")
        self.assertTrue(db.verify_event_chain())

    def test_authority_time_source_overrides_actor_supplied_timestamp(self):
        clock = [100]
        db = Ledger(time_source=lambda: clock[0])
        self.addCleanup(db.close)
        db.create("case", "r1")
        db.claim("case", "holder", 1000000, 10)
        with self.assertRaises(GateError):
            db.claim("case", "outsider", 2000000, 1)
        self.assertEqual(db.db.execute(
            "SELECT tick FROM logical_clock WHERE id=1").fetchone()[0], 100)
        clock[0] = 110
        self.assertEqual(db.claim("case", "next", 0, 10), 2)

    def test_clock_updates_are_referenced_by_auditable_events(self):
        db = Ledger()
        self.addCleanup(db.close)
        db.create("case", "r1")
        db.claim("case", "holder", 2, 10)
        with self.assertRaises(GateError):
            db.claim("case", "outsider", 1000, 1)
        events = [
            json.loads(e[0]) for e in db.db.execute(
                "SELECT payload FROM events ORDER BY seq")
        ]
        clock_events = [e for e in events if e["type"] == "clock_advance"]
        self.assertEqual([(x["previous_tick"], x["tick"], x["cause"])
                          for x in clock_events], [(-1, 2, "claim")])
        self.assertTrue(db.verify_event_chain())

    def test_historical_checkpoint_stable_after_future_append(self):
        actions = named(GENEALOGY, "KG02")["actions"]
        earlier = actions[:4]
        baseline = evaluate_actions(earlier, at_seq=4)
        replay = evaluate_actions(actions, at_seq=4)
        self.assertEqual(baseline, replay)
        self.assertEqual(baseline["prefix_head_sha256"],
                         replay["prefix_head_sha256"])
        self.assertNotIn("verified_supplied_chain_head_sha256", replay)
        self.assertNotEqual(
            verify_chain(seal_actions(earlier)), verify_chain(seal_actions(actions))
        )

    def test_vertical_historical_receipt_stable_after_future_append(self):
        catalog, _ = load_catalog()
        case = next(x for x in catalog["cases"] if x["id"] == "VI01")
        full = materialize_case(catalog, case)
        earlier = deepcopy(full)
        earlier["knowledge_actions"] = earlier["knowledge_actions"][:4]
        before = evaluate_vertical(earlier, at_seq=4)
        after = evaluate_vertical(full, at_seq=4)
        self.assertEqual(before, after)
        self.assertEqual(before["checkpoint_sha256"], after["checkpoint_sha256"])
        self.assertEqual(before["upstream_receipt_sha256"],
                         after["upstream_receipt_sha256"])

    def test_unread_source_stance_not_exposed(self):
        data = context_fixture()
        nav_kwargs = {
            "current_revision": data["current_revision"],
            "issue_tags": data["issue_tags"], "max_chars": 1,
        }
        first = ContextNavigator(deepcopy(data["documents"]), **nav_kwargs)
        changed = deepcopy(data["documents"])
        target = next(item for item in changed if item["id"] == "queue-ack-r2")
        for key in target["signals"]:
            target["signals"][key] = (
                "supports" if target["signals"][key] == "contradicts"
                else "contradicts"
            )
        second = ContextNavigator(changed, **nav_kwargs)
        request = {"sector": "queue", "perspective": "reliability",
                   "depth": "focused", "reason": "bounded lookup"}
        a = first.navigate(**request)
        b = second.navigate(**request)
        self.assertEqual(a, b)
        self.assertEqual(a["new_sources"], [])
        self.assertIn("queue-ack-r2", a["gaps"]["unread_due_to_budget"])
        self.assertNotIn("potential_counterevidence_unread", a["gaps"])
        self.assertNotIn("contradicts", json.dumps(a))
        self.assertEqual(first.context(), second.context())

    def test_uncited_historical_background_does_not_force_hold(self):
        research = named(RESEARCH, "RQ02")["packet"]
        old = deepcopy(research["evidence"][0])
        old["id"] = "old-context-only"
        old["revision"] = "fictional-r0"
        old["source_class"] = "historical"
        old["role"] = "background"
        research["evidence"].append(old)
        out = evaluate_research(research)
        self.assertEqual(out["status"], "DESIGN_ADMISSIBLE")
        self.assertEqual(out["issues"], {})
        self.assertEqual(out["eligible_evidence_ids"], ["queue-observation"])
        self.assertIn({"id": "old-context-only",
                       "code": "UNCITED_HISTORICAL_BACKGROUND_ONLY"},
                      out["background_warnings"])

    def test_hypothesis_cannot_promote_historical_background(self):
        research = named(RESEARCH, "RQ02")["packet"]
        old = deepcopy(research["evidence"][0])
        old.update({"id": "old-context-only", "revision": "fictional-r0",
                    "source_class": "historical", "role": "background"})
        research["evidence"].append(old)
        research["hypotheses"][0]["evidence_ids"].append("old-context-only")
        out = evaluate_research(research)
        self.assertEqual(out["status"], "NEEDS_RESEARCH")
        self.assertIn("HYPOTHESIS_REFERENCES_BACKGROUND_EVIDENCE",
                      out["issues"]["source_integrity"])

    def test_unresolved_counterevidence_blocks_advisory_ready(self):
        packet = named(COGNITIVE, "CP01")["packet"]
        lens = packet["reviews"][0]
        lens["counterevidence_ids"] = ["unit-green"]
        out = evaluate_perspectives(packet)
        self.assertEqual(out["status"], "HOLD_UNRESOLVED_COUNTEREVIDENCE")
        self.assertEqual(out["unresolved_counterevidence_ids"], ["unit-green"])
        self.assertEqual(out["supporting_perspectives"],
                         ["EFFICIENCY", "ENGINEERING", "RESEARCH", "RISK"])
        self.assertEqual(out["execution_authority"], "NONE")

    def test_typed_resolution_is_advisory_not_source_authentication(self):
        packet = named(COGNITIVE, "CP01")["packet"]
        lens = packet["reviews"][0]
        lens["source_ids"].append("risk-note")
        lens["counterevidence_ids"] = ["unit-green"]
        lens["counterevidence_resolutions"] = [{
            "source_id": "unit-green", "state": "RESOLVED",
            "justification": "A declared secondary check appears to refute this objection.",
            "basis_source_id": "risk-note",
        }]
        out = evaluate_perspectives(packet)
        self.assertEqual(out["status"], "ADVISORY_READY")
        self.assertEqual(out["unresolved_counterevidence_ids"], [])
        self.assertFalse(out["source_independence_authenticated"])
        self.assertFalse(out["external_problem_acceptance_verified"])
        self.assertEqual(out["execution_authority"], "NONE")

    def test_false_resolution_without_distinct_cited_basis_is_invalid(self):
        packet = named(COGNITIVE, "CP01")["packet"]
        lens = packet["reviews"][0]
        lens["counterevidence_ids"] = ["unit-green"]
        lens["counterevidence_resolutions"] = [{
            "source_id": "unit-green", "state": "RESOLVED",
            "justification": "I merely assert that it was resolved.",
            "basis_source_id": "unit-green",
        }]
        with self.assertRaises(InvalidPerspectivePacket):
            evaluate_perspectives(packet)

    def test_shared_connection_get_cannot_read_uncommitted_data(self):
        db = Ledger()
        self.addCleanup(db.close)
        db.create("case", "r1")
        locked = threading.Event()
        release = threading.Event()
        seen = []
        exceptions = []

        def writer():
            try:
                with db._transaction():
                    db.db.execute("UPDATE work SET revision='r2' WHERE id='case'")
                    locked.set()
                    if not release.wait(5):
                        raise RuntimeError("writer timeout")
            except BaseException as error:
                exceptions.append(error)

        def reader():
            try:
                seen.append(db.get("case")["revision"])
            except BaseException as error:
                exceptions.append(error)

        tw = threading.Thread(target=writer)
        tr = threading.Thread(target=reader)
        tw.start()
        self.assertTrue(locked.wait(3))
        tr.start()
        try:
            tr.join(0.1)
            self.assertTrue(tr.is_alive(), "uncommitted value was read early")
        finally:
            release.set()
            tw.join(3)
            tr.join(3)
        self.assertEqual(exceptions, [])
        self.assertFalse(tw.is_alive())
        self.assertFalse(tr.is_alive())
        self.assertEqual(seen, ["r2"])


if __name__ == "__main__":
    unittest.main()
