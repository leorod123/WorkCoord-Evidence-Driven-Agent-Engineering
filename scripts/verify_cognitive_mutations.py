"""Prove cognitive-perspective safeguards are exercised by named negative tests.

Mutations run only in temporary fictional-package copies. A mutation is
detected if and only if its named assertion FAILS without import errors or
crashes; tests must not interpret an exception as a successful mutation.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MUTANTS = (
    ("M40_skip_four_required_structured_lenses",
     'return ("ENGINEERING",) if risk == "QUICK" else LENSES',
     'return ("ENGINEERING",)',
     "test_missing_risk_lens_blocks_structured_admission"),
    ("M41_ignore_support_challenge_conflict",
     'elif conflict:',
     'elif False:',
     "test_risk_challenge_cannot_be_outvoted_by_three_supporters"),
    ("M42_ignore_stale_cognitive_review",
     'elif stale:',
     'elif False:',
     "test_stale_review_must_not_be_silent"),
    ("M43_allow_historical_source_as_current",
     'if src["revision"] != revision:',
     'if False:',
     "test_old_source_revision_exposes_coverage_gap"),
    ("M44_ignore_source_availability",
     'if src["available_tick"] > review["review_tick"]:',
     'if False:',
     "test_causal_source_available_after_review_causes_hold"),
    ("M45_skip_external_critical_review",
     'elif risk == "CRITICAL":',
     'elif False:',
     "test_critical_consensus_still_requires_external_review"),
    ("M46_force_four_lenses_for_quick",
     'return ("ENGINEERING",) if risk == "QUICK" else LENSES',
     'return LENSES',
     "test_quick_single_lens_path_has_lower_declared_overhead"),
    ("M47_unbind_cited_source_content_hash",
     'sources[item]["summary"].encode("utf-8")',
     'sources[item]["id"].encode("utf-8")',
     "test_cited_source_content_change_invalidates_checkpoint_even_same_length"),
    ("M48_grant_execution_without_permission",
     '"execution_authority": "NONE",',
     '"execution_authority": "APPROVED",',
     "test_no_work_or_source_authorization_even_with_full_consensus"),
    ("M49_ignore_future_review_tick",
     'if review["review_tick"] > decision_tick:',
     'if False:',
     "test_review_written_after_decision_cannot_be_causal"),
    ("M50_drop_review_cost",
     'cost = sum(rev["estimated_review_units"] for rev in reviews.values())',
     'cost = 0',
     "test_high_self_reported_review_cost_is_not_efficacy"),
    ("M51_discard_optional_quick_risk_challenge",
     'challenged = sorted(lens for lens, rev in reviews.items()\n'
     '                        if rev["stance"] == "CHALLENGE")',
     'challenged = sorted(lens for lens, rev in reviews.items()\n'
     '                        if lens in required and rev["stance"] == "CHALLENGE")',
     "test_quick_optional_challenge_is_not_ignored"),
    ("M52_fake_independent_provenance",
     '"source_independence_authenticated": False,',
     '"source_independence_authenticated": True,',
     "test_same_declared_group_is_not_authenticated_independence"),
    ("M53_silence_evidence_free_perspective",
     'if not review["source_ids"]:',
     'if False:',
     "test_no_cited_evidence_is_an_explicit_gap"),
)


def main():
    for name, before, after, expected_test in MUTANTS:
        with tempfile.TemporaryDirectory() as temp:
            tmp = Path(temp)
            package = tmp / "src" / "workcoord_lab"
            package.mkdir(parents=True)
            (tmp / "tests").mkdir()
            (tmp / "examples").mkdir()
            (package / "__init__.py").write_text(
                '"""Isolated cognitive-review test package."""\n', encoding="utf-8")
            for module in ("cognitive_perspectives.py", "cognitive_perspectives_suite.py"):
                shutil.copy2(ROOT / "src" / "workcoord_lab" / module, package / module)
            shutil.copy2(ROOT / "tests" / "test_cognitive_perspectives.py",
                         tmp / "tests" / "test_cognitive_perspectives.py")
            shutil.copy2(ROOT / "examples" / "cognitive-perspective-cases-v0.json",
                         tmp / "examples" / "cognitive-perspective-cases-v0.json")
            target = package / "cognitive_perspectives.py"
            source = target.read_text(encoding="utf-8")
            if source.count(before) != 1:
                raise SystemExit(name + ": source mutation anchor unavailable/ambiguous")
            target.write_text(source.replace(before, after, 1), encoding="utf-8")
            env = dict(os.environ, PYTHONPATH=str(tmp / "src"))
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                     "-p", "test_cognitive_perspectives.py", "-v"],
                    cwd=tmp, env=env, text=True, capture_output=True, timeout=35,
                )
            except subprocess.TimeoutExpired as exc:
                raise SystemExit(name + ": timeout does not prove regression") from exc
            log = result.stdout + result.stderr
            if (result.returncode == 0 or "ERROR:" in log
                    or "FAIL: " + expected_test + " (" not in log):
                print(log[-5000:])
                raise SystemExit(name + ": named assertion did not detect mutation")
            print(name + " KILLED by " + expected_test)


if __name__ == "__main__":
    main()
