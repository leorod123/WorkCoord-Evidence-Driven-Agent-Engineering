"""Adversarial regression probes for the fictional Problem & Decision gate.

A mutant counts only if its designated test makes an assertion FAIL. Syntax
errors, imports, timeouts, unrelated failures, and crashes do not qualify.
Runs entirely inside temporary Python-package copies, without Git changes.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MUTANTS = (
    ("M25_confuse_technical_with_behavior",
     'and w["kind"] == requirement["kind"]',
     "and True",
     "test_technical_witness_cannot_substitute_for_behavior_probe"),
    ("M26_admit_stale_witness_as_current",
     'admissible = [w for w in submitted if w["current"]',
     'admissible = [w for w in submitted if True',
     "test_stale_witness_never_counts_as_current_pass"),
    ("M27_ignore_required_child_problems",
     'if node["required"] and issues:',
     'if node["required"] and issues and key == root_id:',
     "test_child_required_obligation_blocks_parent_readiness"),
    ("M28_ignore_contradictory_current_probe",
     'if failures:',
     'if False:',
     "test_current_negative_probe_cannot_be_outvoted_by_positive_probe"),
    ("M29_ignore_selected_solution_scope",
     'if not set(leaf_ids).issubset(selected["addresses"]):',
     'if False:',
     "test_selected_solution_must_address_all_required_leaves"),
    ("M30_drop_recurring_cost_horizon",
     'total = upfront + horizon * recurring + risk_reserve + rework_reserve',
     'total = upfront + risk_reserve + rework_reserve',
     "test_common_horizon_accounts_for_recurring_cost"),
    ("M31_allow_unexplained_expensive_build",
     'if selected["strategy"] == "build":',
     'if False:',
     "test_new_component_must_explain_cheaper_comparable_reuse"),
    ("M32_force_heavy_comparison_on_quick",
     'if risk == "QUICK" and data is None:',
     'if False:',
     "test_quick_simple_work_needs_no_heavy_alternative_matrix"),
    ("M33_skip_critical_external_review",
     'elif risk == "CRITICAL":',
     'elif False:',
     "test_critical_ready_design_needs_external_review"),
    ("M34_ignore_unknown_problem_state",
     'if node["knowledge"] != "KNOWN":',
     'if False:',
     "test_knowledge_unknown_is_not_fixed_by_a_green_test"),
    ("M35_skip_root_outcome_criterion",
     'for c_id in sorted(node["criteria"]):',
     'for c_id in ([] if key == root_id else sorted(node["criteria"])):',
     "test_missing_root_acceptance_blocks_even_when_children_are_green"),
    ("M36_promote_optional_gap_to_required",
     'if node["required"] and issues:',
     'if issues:',
     "test_optional_open_node_is_visible_but_not_a_closure_gate"),
    ("M37_grant_closure_on_self_declaration",
     '"semantic_closure_granted": False,',
     '"semantic_closure_granted": True,',
     "test_all_outputs_advisory_even_with_work_status_done"),
)


def main():
    for name, before, after, expected_test in MUTANTS:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            package = folder / "src" / "workcoord_lab"
            package.mkdir(parents=True)
            (folder / "tests").mkdir()
            (folder / "examples").mkdir()
            (package / "__init__.py").write_text(
                '"""Isolated fictional problem-admission check."""\n',
                encoding="utf-8",
            )
            for filename in ("problem_decision.py", "problem_decision_suite.py"):
                shutil.copy2(ROOT / "src" / "workcoord_lab" / filename,
                             package / filename)
            shutil.copy2(ROOT / "tests" / "test_problem_decision.py",
                         folder / "tests" / "test_problem_decision.py")
            shutil.copy2(ROOT / "examples" / "problem-decision-cases-v0.json",
                         folder / "examples" / "problem-decision-cases-v0.json")
            target = package / "problem_decision.py"
            source = target.read_text(encoding="utf-8")
            if source.count(before) != 1:
                raise SystemExit(name + ": mutation anchor is absent/ambiguous")
            target.write_text(source.replace(before, after, 1), encoding="utf-8")
            env = dict(os.environ, PYTHONPATH=str(folder / "src"))
            try:
                run = subprocess.run(
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                     "-p", "test_problem_decision.py", "-v"],
                    cwd=folder, env=env, capture_output=True, text=True, timeout=40,
                )
            except subprocess.TimeoutExpired as exc:
                raise SystemExit(name + ": timeout is not mutation detection") from exc
            output = run.stdout + run.stderr
            if (run.returncode == 0 or "ERROR:" in output
                    or f"FAIL: {expected_test} (" not in output):
                print(output[-5000:])
                raise SystemExit(name + ": specific negative assertion was not killed")
            print(name + " KILLED by " + expected_test)


if __name__ == "__main__":
    main()
