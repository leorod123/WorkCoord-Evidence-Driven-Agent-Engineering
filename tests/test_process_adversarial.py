"""Cross-process adversarial probes; separate SQLite connections and processes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from workcoord_lab.ledger import GateError, Ledger


class MultiProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = str(Path(self.temp.name) / "lab.sqlite")
        db = Ledger(self.database)
        db.create("one", "fictional-r1")
        db.close()

    def worker(self, mode, *args):
        root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.Popen(
            [sys.executable, "-m", "workcoord_lab.claim_worker", mode, self.database, *args],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            env=env, cwd=root,
        )

    def test_eight_independent_processes_only_one_claim(self):
        start = str(Path(self.temp.name) / "start")
        workers = []
        try:
            for idx in range(8):
                ready = str(Path(self.temp.name) / f"ready-{idx}")
                workers.append(self.worker("compete", f"agent-{idx}", ready, start))
            deadline = time.monotonic() + 12
            while not all((Path(self.temp.name) / f"ready-{idx}").exists() for idx in range(8)):
                self.assertTrue(time.monotonic() < deadline, "workers did not become ready")
                self.assertTrue(all(p.poll() is None for p in workers), "worker exited before start")
                time.sleep(0.01)
            Path(start).touch()
            reports = []
            for proc in workers:
                out, err = proc.communicate(timeout=12)
                self.assertEqual(proc.returncode, 0, err)
                reports.append(json.loads(out))
            self.assertEqual(sum(r["status"] == "CLAIMED" for r in reports), 1)
            self.assertEqual(sum(r["status"] == "REJECTED" for r in reports), 7)
            db = Ledger(self.database)
            try:
                self.assertEqual(db.get("one")["generation"], 1)
                self.assertTrue(db.verify_event_chain())
            finally:
                db.close()
        finally:
            for proc in workers:
                if proc.poll() is None:
                    proc.kill()
                    proc.communicate(timeout=4)

    def test_interrupted_uncommitted_transaction_rolls_back(self):
        proc = self.worker("abort-before-commit")
        out, err = proc.communicate(timeout=10)
        self.assertEqual(proc.returncode, 17, err)
        db = Ledger(self.database)
        try:
            item = db.get("one")
            self.assertEqual(item["status"], "READY")
            self.assertEqual(item["generation"], 0)
            self.assertIsNone(item["owner"])
            self.assertEqual(db.claim("one", "new-owner", 1, 10), 1)
            self.assertTrue(db.verify_event_chain())
        finally:
            db.close()

    def test_committed_claim_survives_process_crash(self):
        proc = self.worker("abort-after-commit")
        out, err = proc.communicate(timeout=10)
        self.assertEqual(proc.returncode, 18, err)
        db = Ledger(self.database)
        try:
            item = db.get("one")
            self.assertEqual(item["status"], "CLAIMED")
            self.assertEqual(item["owner"], "ghost")
            self.assertEqual(item["generation"], 1)
            with self.assertRaises(GateError):
                db.claim("one", "new-owner", 19, 10)
            self.assertEqual(db.claim("one", "new-owner", 21, 10), 2)
            self.assertTrue(db.verify_event_chain())
        finally:
            db.close()

    def test_modified_event_detected_by_hash_chain(self):
        db = Ledger(self.database)
        try:
            db.db.execute("UPDATE events SET payload='tampered' WHERE seq=1")
            self.assertFalse(db.verify_event_chain())
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
