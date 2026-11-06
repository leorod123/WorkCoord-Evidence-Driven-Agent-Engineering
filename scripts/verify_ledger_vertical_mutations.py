"""Mutation probes for bounded, synthetic context -> vertical -> Ledger path.

Only a designated failing assertion counts. Exceptions, import errors, false
successes and timeouts are never interpreted as a killed mutant.
No API keys, remote agents, source control mutations or external processes.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]

MUTANTS = (
    ("M96_ignore_context_body_hash",
     'or sha_body(document["body"]) != manifest["primary_source_sha256"]',
     'or False',
     "test_context_body_mismatch_rejected"),
    ("M97_count_unread_primary_as_selected",
     'document = selected.get(required_id)',
     'document = selected.get(required_id) or primary_document',
     "test_missing_selected_primary_source_never_counts_as_retrieval"),
    ("M98_skip_vertical_counterevidence_hold",
     'elif vertical["status"] != CANDIDATE:',
     'elif False:',
     "test_late_contradiction_prevents_sandbox_submission"),
    ("M99_skip_ledger_revision_binding",
     'if state["revision"] != result["source_revision"]:',
     'if False:',
     "test_ledger_revision_mismatch_fails_before_proof"),
    ("M100_ignore_semantic_oracle_failure",
     'if not receipt["passed"]:',
     'if False:',
     "test_false_behavior_oracle_cannot_create_proof_or_submit"),
    ("M101_skip_completion_recheck",
     '    _require_gate(\n'
     '        db, packet, at_seq=at_seq, primary_document=primary_document,\n'
     '        background_documents=background_documents, max_chars=max_chars,\n'
     '        work_id=work_id,\n'
     '    )\n'
     '    return db.complete(work_id, owner, generation, now=now)',
     '    return db.complete(work_id, owner, generation, now=now)',
     "test_cannot_complete_after_late_contradiction_despite_approved_proof"),
    ("M102_skip_verification_recheck",
     '    _require_gate(\n'
     '        db, packet, at_seq=at_seq, primary_document=primary_document,\n'
     '        background_documents=background_documents, max_chars=max_chars,\n'
     '        work_id=work_id,\n'
     '    )\n'
     '    db.verify(work_id, owner, generation, now=now)',
     '    db.verify(work_id, owner, generation, now=now)',
     "test_cannot_verify_when_new_contradiction_is_in_current_packet"),
    ("M103_ignore_navigation_budget",
     'issue_tags=["duplicate-notification"], max_chars=max_chars,',
     'issue_tags=["duplicate-notification"], max_chars=999999,',
     "test_tiny_budget_does_not_consume_unread_primary"),
    ("M104_ignore_task_issue_identity",
     'if state["id"] != result["issue_id"]:',
     'if False:',
     "test_work_identity_mismatch_blocks_proof"),
    ("M105_allow_unreviewed_sandbox_authority",
     'if state["authority"] != "REVIEW_REQUIRED":',
     'if False:',
     "test_unexpected_ledger_authority_rejected_by_bridge"),
    ("M106_export_raw_hmac_events_in_public_receipt",
     'json.loads(row[0])["type"] for row in db.db.execute(',
     'json.loads(row[0]) for row in db.db.execute(',
     "test_public_receipt_never_contains_mac_or_secret_material"),
)


def main():
    for name, before, after, expected_test in MUTANTS:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(ROOT / "src" / "workcoord_lab",
                            root / "src" / "workcoord_lab")
            shutil.copytree(ROOT / "examples", root / "examples")
            (root / "tests").mkdir()
            shutil.copy2(ROOT / "tests" / "test_ledger_vertical_e2e.py",
                         root / "tests" / "test_ledger_vertical_e2e.py")
            path = root / "src" / "workcoord_lab" / "ledger_vertical_e2e.py"
            original = path.read_text(encoding="utf-8")
            if original.count(before) != 1:
                raise SystemExit(name + ": mutation anchor absent or ambiguous")
            path.write_text(original.replace(before, after, 1), encoding="utf-8")
            env = dict(os.environ, PYTHONPATH=str(root / "src"))
            try:
                run = subprocess.run(
                    [sys.executable, "-m", "unittest", "discover",
                     "-s", "tests", "-p", "test_ledger_vertical_e2e.py",
                     "-v", "-k", expected_test],
                    cwd=root, env=env, capture_output=True, text=True,
                    timeout=40,
                )
            except subprocess.TimeoutExpired as exc:
                raise SystemExit(name + ": timeout not a valid mutation kill") from exc
            output = run.stdout + run.stderr
            if (run.returncode == 0 or "ERROR:" in output
                    or f"FAIL: {expected_test} (" not in output):
                print(output[-5500:])
                raise SystemExit(name + ": named assertion did not fail")
            print(name + " KILLED by " + expected_test)


if __name__ == "__main__":
    main()
