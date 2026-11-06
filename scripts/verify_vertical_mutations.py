"""Adversarial mutation checks for the *vertical* public reference.

Each altered copy runs only the named negative-control unittest. A mutation
counts only when a specific assertion FAILS; syntax errors, missing imports,
unexpected exceptions or timeouts do NOT count. No production side effects.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MUTANTS = (
    ("M71_ignore_late_genealogy_hold",
     'elif claims[manifest["claim_id"]] != KNOWLEDGE_READY:',
     'elif False:',
     "test_late_counterevidence_blocks_even_when_all_earlier_checks_green"),
    ("M72_skip_source_epoch_rebase",
     'if source_epoch_drift:\n        decision = "HOLD_REASSESS_REVISION"',
     'if False:\n        decision = "HOLD_REASSESS_REVISION"',
     "test_source_supersession_rejects_old_four_stage_epoch"),
    ("M73_ignore_research_falsifier_hold",
     'elif research["status"] == "NEEDS_RESEARCH":',
     'elif False:',
     "test_research_falsifier_gap_not_bypassed_by_green_downstream"),
    ("M74_ignore_open_required_problem",
     'elif problem["status"] in ("HOLD_REQUIRED_PROBLEM_OPEN", "HOLD_DECISION_INCOMPLETE"):',
     'elif False:',
     "test_green_technical_tests_do_not_close_missing_behavior"),
    ("M75_ignore_dissenting_cognitive_perspective",
     'elif cognitive["status"].startswith("HOLD_"):',
     'elif False:',
     "test_efficiency_uncertainty_is_not_fabricated_consensus"),
    ("M76_skip_external_review_requirement",
     'elif reasons:\n        decision = "REQUIRES_EXTERNAL_REVIEW"',
     'elif False:\n        decision = "REQUIRES_EXTERNAL_REVIEW"',
     "test_critical_study_requires_external_review_despite_unanimity"),
    ("M77_accept_changed_primary_source_body",
     'if not isinstance(body, str) or _source_sha(body) != digest:',
     'if False:',
     "test_same_length_changed_primary_source_body_is_rejected"),
    ("M78_stitch_different_issue_into_problem",
     'or problem.get("id") != manifest["issue_id"]',
     'or False',
     "test_cross_issue_stitching_is_rejected"),
    ("M79_allow_wrong_selected_remedy",
     'if _obj(pd["decision"], "problem.decision").get("selected_id") != manifest["proposal_id"]:',
     'if False:',
     "test_selected_remedy_must_be_the_reviewed_proposal"),
    ("M80_downgrade_risk_in_research_only",
     'if (rq.get("risk") != manifest["risk"]',
     'if (False',
     "test_risk_tier_cannot_be_lowered_in_only_one_layer"),
    ("M81_ignore_research_source_revision",
     'or source.get("revision") != manifest["source_revision"]',
     'or False',
     "test_research_source_identity_and_revision_are_fenced"),
    ("M82_stitch_different_claim_text_into_history",
     'if primary_hypothesis.get("claim") != opened.get("statement"):',
     'if False:',
     "test_shared_hypothesis_and_genealogy_claim_must_be_same"),
    ("M83_allow_cognitive_review_without_shared_source",
     'if not any(\n        isinstance(rev, dict) and shared in rev.get("source_ids", [])',
     'if False and not any(\n        isinstance(rev, dict) and shared in rev.get("source_ids", [])',
     "test_unshared_cognitive_evidence_does_not_count_as_integration"),
    ("M84_accept_missing_problem_witness_as_same_evidence",
     'problem_witness = _one(pd.get("evidence"), shared, "id", "problem.evidence")',
     'problem_witness = _one(rq.get("evidence"), shared, "id", "research.evidence")',
     "test_unshared_problem_witness_cannot_be_stitched_into_flow"),
    ("M85_grant_execution_authorization_from_advisory_checks",
     '"authorization": "NONE",',
     '"authorization": "APPROVED",',
     "test_earlier_positive_four_stage_candidate_remains_only_advisory"),
    ("M86_drop_historical_counterobservation_count",
     '"historical_observation_count": len(knowledge["observations"]),',
     '"historical_observation_count": 1,',
     "test_late_counterevidence_blocks_even_when_all_earlier_checks_green"),
    ("M87_count_future_counterevidence_at_old_cut",
     'knowledge = evaluate_actions(actions, at_seq=at_seq)',
     'knowledge = evaluate_actions(actions)',
     "test_no_lookahead_from_future_evidence_at_earlier_cut"),
    ("M88_forge_knowledge_promotion",
     '"knowledge_promotion": "NOT_GRANTED",',
     '"knowledge_promotion": "VALIDATED",',
     "test_every_result_preserves_all_authority_separations"),
)


def main():
    for name, before, after, expected_test in MUTANTS:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = root / "src" / "workcoord_lab"
            package.mkdir(parents=True)
            (root / "tests").mkdir()
            (root / "examples").mkdir()
            (package / "__init__.py").write_text(
                '"""Isolated four-stage fictional integration."""\n', encoding="utf-8")
            for module in (
                "research_quality.py", "problem_decision.py",
                "cognitive_perspectives.py", "knowledge_genealogy.py",
                "vertical_integration.py", "vertical_integration_suite.py",
            ):
                shutil.copy2(ROOT / "src" / "workcoord_lab" / module,
                             package / module)
            shutil.copy2(ROOT / "tests" / "test_vertical_integration.py",
                         root / "tests" / "test_vertical_integration.py")
            shutil.copy2(ROOT / "examples" / "vertical-integration-cases-v0.json",
                         root / "examples" / "vertical-integration-cases-v0.json")
            target = package / "vertical_integration.py"
            content = target.read_text(encoding="utf-8")
            if content.count(before) != 1:
                raise SystemExit(name + ": expected mutation anchor not unique")
            target.write_text(content.replace(before, after, 1), encoding="utf-8")
            env = dict(os.environ, PYTHONPATH=str(root / "src"))
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                     "-p", "test_vertical_integration.py", "-v", "-k", expected_test],
                    cwd=root, env=env, capture_output=True, text=True, timeout=40,
                )
            except subprocess.TimeoutExpired as exc:
                raise SystemExit(name + ": timeout does not prove mutation kill") from exc
            output = result.stdout + result.stderr
            if (result.returncode == 0 or "ERROR:" in output
                    or "FAIL: " + expected_test + " (" not in output):
                print(output[-4500:])
                raise SystemExit(name + ": named assertion did not detect mutation")
            print(name + " KILLED by " + expected_test)


if __name__ == "__main__":
    main()
