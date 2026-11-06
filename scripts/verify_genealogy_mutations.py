"""Mutate one public genealogy invariant at a time in isolated temp copies.

A mutation is detected only by its own named assertion failure (not an
exception, an import failure or a timeout). No external services are touched.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MUTANTS = (
    ("M54_suppress_source_supersession",
     'a["active"] = False', 'a["active"] = True',
     "test_supersession_invalidates_review_even_when_same_content"),
    ("M55_ignore_old_basis_revision",
     'elif any(not sources[evidence[eid]["source_id"]]["active"]',
     'elif False and any(not sources[evidence[eid]["source_id"]]["active"]',
     "test_old_source_is_retained_and_stale_review_explicit"),
    ("M56_ignore_live_counterevidence",
     'if challenges:', 'if False:',
     "test_current_challenge_prevents_majority_based_acceptance"),
    ("M57_auto_reinstate_after_retraction",
     'claims[evidence[eid]["claim_id"]]["touched_seq"] = seq',
     'pass  # bad: the retraction fails to invalidate a review',
     "test_retraction_does_not_automatically_reactivate_acceptance"),
    ("M58_ignore_parent_status",
     'elif any(status(dep) != CURRENT for dep in claim["depends_on"]):',
     'elif False and any(status(dep) != CURRENT for dep in claim["depends_on"]):',
     "test_downstream_claim_is_blocked_when_parent_invalidated"),
    ("M59_ignore_parent_review_identity",
     'elif any(claims[dep]["review"]["event_sha256"] !=',
     'elif False and any(claims[dep]["review"]["event_sha256"] !=',
     "test_parent_restoration_does_not_silently_restore_child"),
    ("M60_fail_to_retract_negative",
     'evidence[eid]["retracted_seq"] = seq',
     'evidence[eid]["retracted_seq"] = None',
     "test_retraction_does_not_automatically_reactivate_acceptance"),
    ("M61_skip_hash_verification",
     'if row["event_sha256"] != _hash(input_row):',
     'if False:',
     "test_tampering_a_historical_event_breaks_hash_chain"),
    ("M62_allow_future_source",
     'if available > tick:', 'if False:',
     "test_source_available_time_cannot_follow_registration"),
    ("M63_let_staged_source_supply_current_evidence",
     'if not sources[sid]["active"] or sources[sid]["available_tick"] > tick:',
     'if False:',
     "test_staged_revision_cannot_be_used_as_current_observation"),
    ("M64_ignore_new_evidence_after_review",
     'elif claim["touched_seq"] > reviews["seq"]:',
     'elif False:',
     "test_new_positive_observation_also_demands_reassessment"),
    ("M65_allow_review_to_ignore_live_challenge",
     'if sorted(basis) != supporters or any(',
     'if sorted(basis) != supporters and any(',
     "test_current_challenge_prevents_majority_based_acceptance"),
    ("M66_ignore_retracted_review_basis",
     'elif any(evidence[eid]["retracted_seq"] is not None',
     'elif False and any(evidence[eid]["retracted_seq"] is not None',
     "test_explicit_support_retraction_breaks_review_basis"),
    ("M67_drop_historical_negative_evidence",
     'for ev in sorted(evidence.values(), key=lambda e: e["recorded_seq"])',
     'for ev in sorted((e for e in evidence.values() '
     'if e["retracted_seq"] is None), key=lambda e: e["recorded_seq"])',
     "test_retraction_plus_explicit_review_restores_and_keeps_negative"),
    ("M68_bind_source_identity_to_id_instead_of_body",
     'hashlib.sha256(body.encode("utf-8")).hexdigest()',
     'hashlib.sha256(sid.encode("utf-8")).hexdigest()',
     "test_supersession_invalidates_review_even_when_same_content"),
    ("M69_grant_execution_without_external_authority",
     '"execution_authority": "NONE",',
     '"execution_authority": "APPROVED",',
     "test_initial_fictional_review_is_advisory_only"),
    ("M70_permit_unknown_dependency",
     'if cid in claims or cid in parents or any(p not in claims for p in parents):',
     'if cid in claims or cid in parents or False:',
     "test_dependency_must_reference_preexisting_claim"),
)


def main():
    for name, before, after, expected_test in MUTANTS:
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            package = folder / "src" / "workcoord_lab"
            package.mkdir(parents=True)
            (folder / "tests").mkdir()
            (folder / "examples").mkdir()
            (package / "__init__.py").write_text(
                '"""Isolated fictional genealogy."""\n', encoding="utf-8")
            for name_py in ("knowledge_genealogy.py", "knowledge_genealogy_suite.py"):
                shutil.copy2(ROOT / "src" / "workcoord_lab" / name_py,
                             package / name_py)
            shutil.copy2(ROOT / "tests" / "test_knowledge_genealogy.py",
                         folder / "tests" / "test_knowledge_genealogy.py")
            shutil.copy2(ROOT / "examples" / "knowledge-genealogy-cases-v0.json",
                         folder / "examples" / "knowledge-genealogy-cases-v0.json")
            source_path = package / "knowledge_genealogy.py"
            original = source_path.read_text(encoding="utf-8")
            if original.count(before) != 1:
                raise SystemExit(name + ": expected mutation anchor absent or ambiguous")
            source_path.write_text(original.replace(before, after, 1), encoding="utf-8")
            env = dict(os.environ, PYTHONPATH=str(folder / "src"))
            try:
                run = subprocess.run(
                    [sys.executable, "-m", "unittest", "discover",
                     "-s", "tests", "-p", "test_knowledge_genealogy.py", "-v"],
                    cwd=folder, env=env, capture_output=True,
                    text=True, timeout=45,
                )
            except subprocess.TimeoutExpired as exc:
                raise SystemExit(name + ": timeout is not a successful mutation") from exc
            text = run.stdout + run.stderr
            if (run.returncode == 0 or "ERROR:" in text
                    or f"FAIL: {expected_test} (" not in text):
                print(text[-4500:])
                raise SystemExit(name + ": expected named assertion did not fail")
            print(name + " KILLED by " + expected_test)


if __name__ == "__main__":
    main()
