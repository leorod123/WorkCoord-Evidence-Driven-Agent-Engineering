"""A01-A05/A08 targeted mutation probes against reviewed contracts.

Each mutant operates in an isolated temporary copy and must trigger its
designated assertion failure. Imports, errors, timeouts and crashes never
count. No agent/API credentials or external services are used.
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
        "M89_rejected_actor_poison_clock",
        "ledger.py",
        '    def submit(self, work_id, agent, generation, now, evidence_id):\n'
        '        with self._transaction():',
        '    def submit(self, work_id, agent, generation, now, evidence_id):\n'
        '        with self._transaction():\n'
        '            self.db.execute("UPDATE logical_clock SET tick=? WHERE id=1", (now,))\n'
        '        with self._transaction():',
        "test_rejected_actor_cannot_advance_lease_clock",
    ),
    (
        "M90_ignore_host_clock_authority",
        "ledger.py",
        "now = self._time_source() if self._time_source is not None else supplied_now",
        "now = supplied_now",
        "test_authority_time_source_overrides_actor_supplied_timestamp",
    ),
    (
        "M91_future_event_hash_leaks_into_past",
        "knowledge_genealogy.py",
        '        "prefix_head_sha256": (',
        '        "verified_supplied_chain_head_sha256": verify_chain(records),\n'
        '        "prefix_head_sha256": (',
        "test_historical_checkpoint_stable_after_future_append",
    ),
    (
        "M92_unread_contradiction_answer_key",
        "intelligence.py",
        '            "unread_due_to_budget": budget_excluded,',
        '            "unread_due_to_budget": budget_excluded,\n'
        '            "potential_counterevidence_unread": [\n'
        '                identifier for identifier in budget_excluded\n'
        '                if "contradicts" in self.documents[identifier]["signals"].values()\n'
        '            ],',
        "test_unread_source_stance_not_exposed",
    ),
    (
        "M93_block_uncited_historical_background",
        "research_quality.py",
        'if role == "basis" and (ev_revision != revision or source_class == "historical"):',
        'if ev_revision != revision or source_class == "historical":',
        "test_uncited_historical_background_does_not_force_hold",
    ),
    (
        "M94_support_hides_open_counterevidence",
        "cognitive_perspectives.py",
        '    elif unresolved_counterevidence:\n'
        '        status = "HOLD_UNRESOLVED_COUNTEREVIDENCE"',
        '    elif False:\n'
        '        status = "HOLD_UNRESOLVED_COUNTEREVIDENCE"',
        "test_unresolved_counterevidence_blocks_advisory_ready",
    ),
    (
        "M95_shared_sqlite_read_without_lock",
        "ledger.py",
        '        with self._lock:\n'
        '            return dict(self._row(work_id))',
        '        return dict(self._row(work_id))',
        "test_shared_connection_get_cannot_read_uncommitted_data",
    ),
)


def main():
    for name, module, before, after, expected_test in MUTANTS:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "src" / "workcoord_lab",
                            root / "src" / "workcoord_lab")
            shutil.copytree(ROOT / "examples", root / "examples")
            (root / "tests").mkdir()
            shutil.copy2(ROOT / "tests" / "test_audit_remediations.py",
                         root / "tests" / "test_audit_remediations.py")
            source = root / "src" / "workcoord_lab" / module
            content = source.read_text(encoding="utf-8")
            if content.count(before) != 1:
                raise SystemExit(name + ": expected mutation anchor not unique")
            source.write_text(content.replace(before, after, 1), encoding="utf-8")
            env = dict(os.environ, PYTHONPATH=str(root / "src"))
            try:
                run = subprocess.run(
                    [sys.executable, "-m", "unittest", "discover",
                     "-s", "tests", "-p", "test_audit_remediations.py",
                     "-v", "-k", expected_test],
                    cwd=root, env=env, capture_output=True, text=True, timeout=40,
                )
            except subprocess.TimeoutExpired as exc:
                raise SystemExit(name + ": timeout is not a detected mutant") from exc
            output = run.stdout + run.stderr
            if (run.returncode == 0 or "ERROR:" in output
                    or f"FAIL: {expected_test} (" not in output):
                print(output[-5000:])
                raise SystemExit(name + ": designated assertion did not fail")
            print(name + " KILLED by " + expected_test)


if __name__ == "__main__":
    main()
