"""Negative controls for the *planned* Harbor pilot's accounting rules.

Each source mutation executes one named synthetic assertion in an isolated
stdlib-only temporary checkout. An exception/import error is not a kill.
Nothing runs Harbor, Codex, Docker or a paid model.
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
        "M107_accept_mutated_task_manifest",
        '_require(b["task_manifest_sha256"] == task_fingerprint(p),',
        '_require(True,',
        "test_tampered_manifest_detected",
    ),
    (
        "M108_gate_block_counts_as_external_success",
        'success = sum(r["verifier_status"] == "PASS" for r in observed)',
        'success = sum((r["verifier_status"] == "PASS" or '
        '(r["gate_blocked_invalid_attempts"] or 0) > 0) for r in observed)',
        "test_gate_block_rejection_not_success",
    ),
    (
        "M109_infrastructure_error_removed_from_denominator",
        'assigned = len(tasks) * attempts',
        'assigned = len(tasks) * attempts - sum('
        'r["verifier_status"] == "HARNESS_ERROR" for r in observed)',
        "test_harness_errors_counted_as_nonsuccess",
    ),
    (
        "M110_drop_failed_attempt_cost",
        'total_cost = sum(r["cost_usd"] for r in observed) if cost_complete else None',
        'total_cost = sum(r["cost_usd"] for r in observed '
        'if r["verifier_status"] == "PASS") if cost_complete else None',
        "test_failed_attempt_costs_included",
    ),
    (
        "M111_allow_unreviewed_raw_trace_or_secret_metadata",
        '_require(isinstance(r, dict) and set(r) == EXPECTED_ROW_FIELDS,',
        '_require(isinstance(r, dict) and EXPECTED_ROW_FIELDS.issubset(r),',
        "test_raw_trajectory_and_secrets_rejected",
    ),
    (
        "M112_impute_unknown_invalid_attempts_as_zero",
        'sum(r["invalid_completion_attempts"] for r in observed)\n'
        '                if adjudication_complete else None',
        'sum(r["invalid_completion_attempts"] for r in observed)\n'
        '                if adjudication_complete else 0',
        "test_no_adjudication_does_not_look_like_no_false_completion",
    ),
    (
        "M113_absent_trial_becomes_success",
        'success = sum(r["verifier_status"] == "PASS" for r in observed)',
        'success = sum(r["verifier_status"] == "PASS" for r in observed) + '
        '(assigned - len(observed))',
        "test_missing_rows_not_success",
    ),
)


def main():
    for name, before, after, selected_test in MUTANTS:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "src" / "workcoord_lab"
            folder.parent.mkdir(parents=True)
            (root / "tests").mkdir()
            (root / "evals").mkdir()
            folder.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / "src" / "workcoord_lab" / "__init__.py",
                         folder / "__init__.py")
            shutil.copy2(ROOT / "src" / "workcoord_lab" / "harbor_pilot.py",
                         folder / "harbor_pilot.py")
            shutil.copy2(ROOT / "tests" / "test_harbor_pilot.py",
                         root / "tests" / "test_harbor_pilot.py")
            shutil.copy2(ROOT / "evals" / "harbor-pilot-protocol-v0.json",
                         root / "evals" / "harbor-pilot-protocol-v0.json")
            source = folder / "harbor_pilot.py"
            content = source.read_text(encoding="utf-8")
            if content.count(before) != 1:
                raise SystemExit(name + ": mutation anchor not unique")
            source.write_text(content.replace(before, after, 1), encoding="utf-8")
            env = dict(os.environ, PYTHONPATH=str(root / "src"))
            try:
                run = subprocess.run(
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                     "-p", "test_harbor_pilot.py", "-v", "-k", selected_test],
                    cwd=root, capture_output=True, text=True, env=env, timeout=40,
                )
            except subprocess.TimeoutExpired as exc:
                raise SystemExit(name + ": a timeout is not evidence") from exc
            output = run.stdout + run.stderr
            if (run.returncode == 0 or "ERROR:" in output
                    or ("FAIL: " + selected_test + " (") not in output):
                print(output[-5000:])
                raise SystemExit(name + ": designated assertion did not reject mutation")
            print(name + " KILLED by " + selected_test)


if __name__ == "__main__":
    main()
