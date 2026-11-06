"""Mutation controls for the standalone public research-admission experiment.

A mutant is detected only when its specific named unittest fails by assertion,
not merely due to an import error, crash or timeout. Uses temporary copies.
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
        'M17_skip_decision_time',
        'if available > proposed_at or read > proposed_at:',
        'if False:',
        'test_postdecision_source_available_time_is_caught',
    ),
    (
        'M18_accept_outcome_peeking',
        'if _time(freeze, "evaluation.plan_frozen_at") >= _time(',
        'if False and _time(freeze, "evaluation.plan_frozen_at") >= _time(',
        'test_late_outcome_freeze_blocks_admission',
    ),
    (
        'M19_ignore_falsifier',
        'if not isinstance(falsifier, str) or not falsifier.strip():',
        'if False:',
        'test_hypothesis_requires_actual_falsifier',
    ),
    (
        'M20_accept_invalid_proxy',
        'elif not construct:',
        'elif False:',
        'test_unjustified_proxy_metric_blocks_admission',
    ),
    (
        'M21_allow_self_validation',
        'if target in ("TESTED", "VALIDATED"):',
        'if False:',
        'test_self_asserted_validation_never_passes',
    ),
    (
        'M22_fake_independent_groups',
        'groups.add(origin)',
        'groups.add(label)',
        'test_duplicate_origin_does_not_count_as_two_independent_sources',
    ),
    (
        'M23_ignore_negative_control',
        'if not isinstance(controls.get("negative_control"), str) or not controls["negative_control"].strip():',
        'if False:',
        'test_missing_negative_control_detected',
    ),
    (
        'M24_promote_stale_source',
        'if ev_revision != revision or source_class == "historical":',
        'if False:',
        'test_stale_historical_source_never_promoted_as_current',
    ),
)


def main():
    for name, before, after, expected_test in MUTANTS:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'src' / 'workcoord_lab').mkdir(parents=True)
            (root / 'tests').mkdir()
            (root / 'examples').mkdir()
            (root / 'src' / 'workcoord_lab' / '__init__.py').write_text(
                '"""Isolated research check."""\n', encoding='utf-8')
            source = root / 'src' / 'workcoord_lab' / 'research_quality.py'
            shutil.copy2(ROOT / 'src' / 'workcoord_lab' / 'research_quality.py', source)
            shutil.copy2(ROOT / 'src' / 'workcoord_lab' / 'research_quality_suite.py',
                         root / 'src' / 'workcoord_lab' / 'research_quality_suite.py')
            shutil.copy2(ROOT / 'tests' / 'test_research_quality.py',
                         root / 'tests' / 'test_research_quality.py')
            shutil.copy2(ROOT / 'examples' / 'research-quality-cases-v0.json',
                         root / 'examples' / 'research-quality-cases-v0.json')
            original = source.read_text(encoding='utf-8')
            if original.count(before) != 1:
                raise SystemExit(f'{name}: anchor missing or ambiguous')
            source.write_text(original.replace(before, after, 1),encoding='utf-8')
            env = dict(os.environ, PYTHONPATH=str(root / 'src'))
            try:
                run = subprocess.run(
                    [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests',
                     '-p', 'test_research_quality.py', '-v'],
                    cwd=root, env=env, text=True, capture_output=True, timeout=25,
                )
            except subprocess.TimeoutExpired as exc:
                raise SystemExit(f'{name}: timeout is not a detected mutant') from exc
            log = run.stdout + run.stderr
            if not (run.returncode != 0 and 'FAIL:' in log
                    and f'test_{expected_test[5:]}' in log):
                print(log[-3500:])
                raise SystemExit(f'{name}: no expected assertion failure')
            if f'FAIL: {expected_test} ' not in log:
                print(log[-3500:])
                raise SystemExit(f'{name}: named test did not fail')
            print(f'{name} KILLED by {expected_test}')


if __name__ == '__main__':
    main()
