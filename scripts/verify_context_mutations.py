"""Require negative tests to detect removal of context navigation controls.

A mutation is counted as detected only if an expected test FAILS by assertion,
not when the mutated source fails to import or times out.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SRC = "src/workcoord_lab/intelligence.py"

MUTANTS = {
    "M3_ignore_perspective": (
        'and perspective in doc["perspectives"]',
        "and True",
        "test_perspective_changes_selected_sources",
    ),
    "M4_ignore_depth": (
        'and DEPTH[doc["depth"]] <= DEPTH[depth]',
        "and True",
        "test_depth_controls_specificity",
    ),
    "M5_ignore_source_revision": (
        'current = doc["revision"] == self.current_revision',
        "current = True",
        "test_initial_stale_validated_note_is_not_current_authority",
    ),
    "M6_ignore_budget": (
        'if self.total_chars() + len(doc["body"]) > self.max_chars:',
        "if False:",
        "test_budget_exclusions_explicit_without_unread_stance",
    ),
    "M7_drop_counterevidence": (
        'contradict[name].append(doc["id"])',
        'pass  # synthetic mutation omits contradiction record',
        "test_cross_sector_contradiction_revises_investigation",
    ),
}


def main():
    for name, (before, after, expected_test) in MUTANTS.items():
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "src").mkdir()
            shutil.copytree(ROOT / "src" / "workcoord_lab", project / "src" / "workcoord_lab")
            (project / "examples").mkdir()
            shutil.copy2(ROOT / "examples" / "flowdesk-context.json",
                         project / "examples" / "flowdesk-context.json")
            (project / "tests").mkdir()
            shutil.copy2(ROOT / "tests" / "test_intelligence_navigation.py",
                         project / "tests" / "test_intelligence_navigation.py")
            path = project / SRC
            original = path.read_text(encoding="utf-8")
            if original.count(before) != 1:
                raise SystemExit(name + ": exact mutation anchor missing or ambiguous")
            path.write_text(original.replace(before, after, 1), encoding="utf-8")
            env = dict(os.environ, PYTHONPATH=str(project / "src"))
            run = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_intelligence_navigation.py", "-v"],
                cwd=project, env=env, capture_output=True, text=True, timeout=30,
            )
            log = run.stdout + run.stderr
            if not (run.returncode != 0 and expected_test in log and "FAIL:" in log):
                print(log[-5000:])
                raise SystemExit(name + ": expected negative control did not fail")
            print(name + " KILLED by " + expected_test)


if __name__ == "__main__":
    main()
