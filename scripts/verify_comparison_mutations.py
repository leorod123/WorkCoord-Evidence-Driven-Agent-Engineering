"""Mutation evidence for synthetic context-comparison invariants.

Each mutant must cause an expected assertion failure, not merely a syntax
error or timeout. This does not make a public fixture an agent benchmark.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PATH = "src/workcoord_lab/context_comparison.py"
MUTANTS = {
    "M8_disable_dependency_expansion": (
        'if strategy == "dependency_expand":', "if False:",
        "test_expansion_recovers_linked_counterevidence",
    ),
    "M9_accept_correct_sounding_without_decisive_evidence": (
        '"evidence_supported_provisional_label": bool(matches and complete)',
        '"evidence_supported_provisional_label": bool(matches)',
        "test_depth_bottleneck_can_look_correct_but_lack_evidence",
    ),
    "M10_ignore_full_corpus_budget": (
        "if chars > budget:", "if False:",
        "test_full_corpus_refuses_oversized_budget_without_truncation",
    ),
    "M11_ignore_characters_read": (
        '"read_characters": nav.total_chars(),',
        '"read_characters": 0,',
        "test_equal_per_case_budget_and_exact_character_measure",
    ),
}


def main():
    for name, (original, replacement, expected_failure) in MUTANTS.items():
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / "src").mkdir()
            shutil.copytree(ROOT / "src" / "workcoord_lab",
                            target / "src" / "workcoord_lab")
            (target / "tests").mkdir()
            shutil.copy2(ROOT / "tests" / "test_context_comparison.py",
                         target / "tests" / "test_context_comparison.py")
            (target / "evals").mkdir()
            for path in ("context_cases_v0.json", "context_oracle_v0.json"):
                shutil.copy2(ROOT / "evals" / path, target / "evals" / path)
            (target / "examples").mkdir()
            shutil.copy2(ROOT / "examples" / "flowdesk-context.json",
                         target / "examples" / "flowdesk-context.json")
            source = target / PATH
            text = source.read_text(encoding="utf-8")
            if text.count(original) != 1:
                raise SystemExit(name + ": expected exact source anchor unavailable")
            source.write_text(text.replace(original, replacement, 1),
                              encoding="utf-8")
            env = dict(os.environ, PYTHONPATH=str(target / "src"))
            try:
                run = subprocess.run(
                    [sys.executable, "-m", "unittest", "discover",
                     "-s", "tests", "-p", "test_context_comparison.py", "-v"],
                    cwd=target, env=env, text=True,
                    capture_output=True, timeout=35,
                )
            except subprocess.TimeoutExpired as exc:
                raise SystemExit(name + ": timeout is not a successful mutation") from exc
            observed = run.stdout + run.stderr
            if not (run.returncode != 0
                    and "FAIL:" in observed
                    and expected_failure in observed):
                print(observed[-5500:])
                raise SystemExit(name + ": expected negative control did not fail")
            print(name + " KILLED by " + expected_failure)


if __name__ == "__main__":
    main()
