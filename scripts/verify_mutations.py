"""Mutation test: kill M1 (owner/generation removed) and M2 (expiry removed).

Each mutant must fail a named isolated negative-control test; merely causing
an import error or timeout does not count as killing the mutation.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LEDGER = "src/workcoord_lab/ledger.py"
BEFORE = 'item["owner"] != agent or item["generation"] != generation\n                or now >= item["expires"]'
MUTANTS = {
    "M1_remove_identity": (
        "now >= item[\"expires\"]", "test_identity_fencing_isolated"
    ),
    "M2_remove_expiry": (
        'item["owner"] != agent or item["generation"] != generation',
        "test_expiry_fencing_isolated"
    ),
}


def main():
    for name, (after, expected_test) in MUTANTS.items():
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "src").mkdir()
            shutil.copytree(ROOT / "src" / "workcoord_lab", project / "src" / "workcoord_lab")
            (project / "tests").mkdir()
            shutil.copy2(
                ROOT / "tests" / "test_adversarial_controls.py",
                project / "tests" / "test_adversarial_controls.py",
            )
            filename = project / LEDGER
            source = filename.read_text(encoding="utf-8")
            if source.count(BEFORE) != 1:
                raise SystemExit(name + ": mutation anchor missing or duplicated")
            filename.write_text(source.replace(BEFORE, after, 1), encoding="utf-8")
            env = dict(os.environ, PYTHONPATH=str(project / "src"))
            run = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_adversarial_controls.py", "-v"],
                cwd=project, env=env, capture_output=True,
                text=True, timeout=30,
            )
            raw = run.stdout + run.stderr
            if not (run.returncode != 0 and expected_test in raw and "FAIL:" in raw):
                print(raw[-6000:])
                raise SystemExit(name + ": mutant not killed by expected failing test")
            print(name + " KILLED by " + expected_test)


if __name__ == "__main__":
    main()
