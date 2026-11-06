"""Isolated mutation tests for full synthetic Ledger-path invariants M96-M102.

A kill means one **named assertion** fails. An unexpected exception, import
error, crash or timeout is never counted. Copies have no network or secrets.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MUTANTS = (
    (
        "M96_ignore_read_source_digest",
        "full_ledger_cycle.py",
        'if _digest(primary[0]["body"]) != manifest["primary_source_sha256"]:',
        'if False:',
        "test_modified_initial_source_body_fails_closed",
    ),
    (
        "M97_complete_despite_late_counterevidence",
        "full_ledger_cycle.py",
        'if advisory["status"] != READY:',
        'if False:',
        "test_completion_helper_refuses_late_advisory_hold",
    ),
    (
        "M98_keep_stale_revision_approval",
        "ledger.py",
        '"approved_by=NULL,receipt=NULL WHERE id=?",\n'
        '                (revision, next_status, work_id),',
        '"approved_by=approved_by,receipt=NULL WHERE id=?",\n'
        '                (revision, next_status, work_id),',
        "test_revision_change_in_claimed_submitted_verified_states",
    ),
    (
        "M99_ignore_inconsistent_advisory_revision",
        "full_ledger_cycle.py",
        'if (advisory["source_revision"] != packet["manifest"]["source_revision"]\n'
        '            or db.get(fixture["work_id"])["revision"] != advisory["source_revision"]):',
        'if False:',
        "test_completion_helper_refuses_outdated_advisory_revision",
    ),
    (
        "M100_use_pass_trace_instead_of_observed_negative",
        "full_ledger_cycle.py",
        'fixture["fictional_logical_events"], deliveries,',
        'fixture["fictional_logical_events"], fixture["declared_successful_deliveries"],',
        "test_external_oracle_computes_failure_from_delivery_trace",
    ),
    (
        "M101_bypass_distinct_declared_reviewer",
        "ledger.py",
        'if item["authority"] == "REVIEW_REQUIRED" and not item["approved_by"]:',
        'if False:',
        "test_old_proof_and_old_approval_cannot_complete_revised_work",
    ),
    (
        "M102_preserve_stale_proof_on_source_change",
        "ledger.py",
        '"UPDATE work SET revision=?,status=?,evidence_id=NULL,"',
        '"UPDATE work SET revision=?,status=?,evidence_id=evidence_id,"',
        "test_revision_change_in_claimed_submitted_verified_states",
    ),
)


def main():
    for name, filename, before, after, expected in MUTANTS:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "src" / "workcoord_lab",
                            root / "src" / "workcoord_lab")
            shutil.copytree(ROOT / "examples", root / "examples")
            (root / "tests").mkdir()
            shutil.copy2(ROOT / "tests" / "test_full_ledger_cycle.py",
                         root / "tests" / "test_full_ledger_cycle.py")
            source = root / "src" / "workcoord_lab" / filename
            content = source.read_text(encoding="utf-8")
            if content.count(before) != 1:
                raise SystemExit(name + ": mutant anchor not unique")
            source.write_text(content.replace(before, after, 1), encoding="utf-8")
            env = dict(os.environ, PYTHONPATH=str(root / "src"))
            try:
                outcome = subprocess.run(
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                     "-p", "test_full_ledger_cycle.py", "-v", "-k", expected],
                    cwd=root, env=env, capture_output=True, text=True, timeout=45,
                )
            except subprocess.TimeoutExpired as exc:
                raise SystemExit(name + ": timeout is not detection") from exc
            log = outcome.stdout + outcome.stderr
            if (outcome.returncode == 0 or "ERROR:" in log
                    or "FAIL: " + expected + " (" not in log):
                print(log[-5000:])
                raise SystemExit(name + ": designated assertion did not fail")
            print(name + " KILLED by " + expected)


if __name__ == "__main__":
    main()
