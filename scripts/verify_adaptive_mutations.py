"""Mutation checks for the publicly inspectable adaptive policy/evaluator.

A mutation counts only if the named negative-control assertion FAILS.
Import errors and timeouts are not accepted as successful detections.
No effect on production systems or external resources.
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
        "M12_disable_deepening",
        "src/workcoord_lab/adaptive_policy.py",
        "if deeper is not None:",
        "if False:",
        "test_permitted_depth_escalation_finds_deep_required_source",
    ),
    (
        "M13_disable_dependency_expansion",
        "src/workcoord_lab/adaptive_policy.py",
        'if available_links and expanded_hops < case["max_hops"]:',
        "if False:",
        "test_high_risk_cross_sector_expands_and_preserves_sources",
    ),
    (
        "M14_ignore_multisector_risk",
        "src/workcoord_lab/adaptive_policy.py",
        'required_sectors = 1 if case["risk_tier"] == "low" else 2',
        "required_sectors = 1",
        "test_missing_dependency_causes_avoidable_hold_not_success",
    ),
    (
        "M15_reward_all_holds",
        "src/workcoord_lab/adaptive_evaluator.py",
        'if gold["outcome_class"] == "INDETERMINATE_UNDER_ALLOWED_DEPTH":',
        "if True:",
        "test_missing_dependency_causes_avoidable_hold_not_success",
    ),
    (
        "M16_accept_lucky_label_without_proof",
        "src/workcoord_lab/adaptive_evaluator.py",
        "if proposed == expected and not missing",
        "if proposed == expected",
        "test_incomplete_evidence_is_never_supported_by_lucky_label",
    ),
)


def main():
    for name, target_path, original, mutated, expected_test in MUTANTS:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            shutil.copytree(ROOT / "src" / "workcoord_lab",
                            root / "src" / "workcoord_lab")
            (root / "examples").mkdir()
            for path in ("flowdesk-context.json", "adaptive-paired-worlds-v0.json"):
                shutil.copy2(ROOT / "examples" / path, root / "examples" / path)
            (root / "evals").mkdir()
            for path in ("adaptive-cases-v0.json", "adaptive-oracle-v0.json",
                         "context_cases_v0.json", "context_oracle_v0.json"):
                shutil.copy2(ROOT / "evals" / path, root / "evals" / path)
            (root / "tests").mkdir()
            shutil.copy2(ROOT / "tests" / "test_adaptive_policy.py",
                         root / "tests" / "test_adaptive_policy.py")
            target = root / target_path
            contents = target.read_text(encoding="utf-8")
            if contents.count(original) != 1:
                raise SystemExit(name + ": original mutation anchor not unique")
            target.write_text(contents.replace(original, mutated, 1), encoding="utf-8")
            env = dict(os.environ, PYTHONPATH=str(root / "src"))
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                     "-p", "test_adaptive_policy.py", "-v"],
                    cwd=root, env=env, capture_output=True, text=True, timeout=45,
                )
            except subprocess.TimeoutExpired as exc:
                raise SystemExit(name + ": timeout does not prove detection") from exc
            combined = result.stdout + result.stderr
            if (result.returncode == 0 or "FAIL:" not in combined
                    or expected_test not in combined):
                print(combined[-5000:])
                raise SystemExit(name + ": expected isolated negative control failed to detect mutation")
            print(name + " KILLED by " + expected_test)


if __name__ == "__main__":
    main()
