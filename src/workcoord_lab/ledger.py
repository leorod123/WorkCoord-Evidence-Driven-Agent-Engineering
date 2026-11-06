"""Small SQLite reference state machine, not an execution authority.

Caller-supplied ticks are checked against a durable ledger-local nondecreasing clock.
A fence token is (work_id, generation). This is not a trusted distributed clock.
No API here executes code, edits a repository, or grants production permissions.
"""

import hashlib
import json
import sqlite3
import threading
from contextlib import contextmanager


class GateError(ValueError):
    """Requested state transition violates a declared invariant."""


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class Ledger:
    def __init__(self, path=":memory:", *, verification_key=None):
        self._verification_key = verification_key
        self.db = sqlite3.connect(path, isolation_level=None, timeout=5, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.execute("PRAGMA foreign_keys=ON")
        self._lock = threading.RLock()
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS work (
            id TEXT PRIMARY KEY, status TEXT NOT NULL, revision TEXT NOT NULL,
            owner TEXT, generation INTEGER NOT NULL DEFAULT 0,
            expires INTEGER, evidence_id TEXT, approved_by TEXT, receipt TEXT,
            authority TEXT NOT NULL, deps TEXT NOT NULL DEFAULT '[]');
          CREATE TABLE IF NOT EXISTS evidence (
            id TEXT PRIMARY KEY, revision TEXT NOT NULL, kind TEXT NOT NULL,
            passed INTEGER NOT NULL, artifact TEXT, independent_group TEXT, attestation TEXT, work_id TEXT);
          CREATE TABLE IF NOT EXISTS events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL,
            previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS logical_clock (
            id INTEGER PRIMARY KEY CHECK(id=1), tick INTEGER NOT NULL);
          INSERT OR IGNORE INTO logical_clock(id,tick) VALUES (1,-1);
        """)
        # Existing local v0 databases may lack the new column.
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(evidence)")}
        if "attestation" not in columns:
            self.db.execute("ALTER TABLE evidence ADD COLUMN attestation TEXT")
        if "work_id" not in columns:
            self.db.execute("ALTER TABLE evidence ADD COLUMN work_id TEXT")

    def close(self):
        self.db.close()

    @contextmanager
    def _transaction(self):
        with self._lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                yield
                self.db.execute("COMMIT")
            except BaseException:
                self.db.execute("ROLLBACK")
                raise

    def _observe_tick(self, now):
        """Persist even a rejected call's observed time, preventing rollback of time.

        Two transactions are intentional: a failed work transition must not
        erase the logical time already observed by the ledger.
        """
        if type(now) is not int or now < 0:
            raise GateError("logical tick must be a nonnegative integer")
        with self._transaction():
            previous = self.db.execute(
                "SELECT tick FROM logical_clock WHERE id=1"
            ).fetchone()[0]
            if now < previous:
                raise GateError("logical clock cannot move backwards")
            self.db.execute(
                "UPDATE logical_clock SET tick=? WHERE id=1", (now,)
            )

    def _require_current_tick(self, now):
        last = self.db.execute(
            "SELECT tick FROM logical_clock WHERE id=1"
        ).fetchone()[0]
        if type(now) is not int or now < last:
            raise GateError("stale or invalid logical tick")

    def _row(self, work_id):
        row = self.db.execute("SELECT * FROM work WHERE id=?", (work_id,)).fetchone()
        if row is None:
            raise GateError("unknown work item")
        return row

    def get(self, work_id):
        return dict(self._row(work_id))

    def _event(self, name, **details):
        item = _canonical({"type": name, **details})
        last = self.db.execute("SELECT event_hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        previous = last[0] if last else "0" * 64
        digest = hashlib.sha256((previous + item).encode()).hexdigest()
        self.db.execute(
            "INSERT INTO events (payload,previous_hash,event_hash) VALUES (?,?,?)",
            (item, previous, digest),
        )

    def verify_event_chain(self):
        previous = "0" * 64
        for row in self.db.execute("SELECT * FROM events ORDER BY seq"):
            expected = hashlib.sha256((previous + row["payload"]).encode()).hexdigest()
            if row["previous_hash"] != previous or row["event_hash"] != expected:
                return False
            previous = expected
        return True

    def event_count(self):
        return self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def create(self, work_id, revision, authority="EDIT_SANDBOX"):
        if not work_id or not revision:
            raise GateError("work id and revision are required")
        if authority not in {"READ_ONLY", "EDIT_SANDBOX", "REVIEW_REQUIRED"}:
            raise GateError("invalid authority scope")
        with self._transaction():
            try:
                self.db.execute(
                    "INSERT INTO work (id,status,revision,authority) VALUES (?,?,?,?)",
                    (work_id, "READY", revision, authority),
                )
            except sqlite3.IntegrityError as exc:
                raise GateError("duplicate work id") from exc
            self._event("create", work_id=work_id, revision=revision, authority=authority)

    def add_dependency(self, work_id, dependency_id):
        with self._transaction():
            item = self._row(work_id)
            self._row(dependency_id)
            if item["status"] != "READY":
                raise GateError("dependencies can only change on ready work")
            if work_id == dependency_id:
                raise GateError("self dependency")
            deps = json.loads(item["deps"])
            if dependency_id in deps:
                return

            def reaches(start, target, seen):
                if start == target:
                    return True
                if start in seen:
                    return False
                seen.add(start)
                parents = json.loads(self._row(start)["deps"])
                return any(reaches(p, target, seen) for p in parents)

            if reaches(dependency_id, work_id, set()):
                raise GateError("dependency cycle")
            deps.append(dependency_id)
            self.db.execute("UPDATE work SET deps=? WHERE id=?", (_canonical(deps), work_id))
            self._event("dependency", work_id=work_id, prerequisite=dependency_id)

    def claim(self, work_id, agent, now, ttl):
        if not agent or type(ttl) is not int or ttl <= 0:
            raise GateError("invalid lease parameters")
        self._observe_tick(now)
        with self._transaction():
            self._require_current_tick(now)
            item = self._row(work_id)
            if item["status"] == "DONE":
                raise GateError("completed work is not claimable")
            if item["owner"] is not None and now < item["expires"]:
                raise GateError("lease already held")
            generation = item["generation"] + 1
            self.db.execute(
                "UPDATE work SET status='CLAIMED',owner=?,generation=?,expires=?,"
                "evidence_id=NULL,approved_by=NULL,receipt=NULL WHERE id=?",
                (agent, generation, now + ttl, work_id),
            )
            self._event("claim", work_id=work_id, agent=agent, generation=generation,
                        issued_at=now, ttl=ttl, expires_at=now + ttl,
                        revision=item["revision"])
            return generation

    def _fenced(self, item, agent, generation, now, status):
        self._require_current_tick(now)
        if (item["owner"] != agent or item["generation"] != generation
                or now >= item["expires"]):
            raise GateError("stale owner or expired lease")
        if item["status"] != status:
            raise GateError("invalid work transition")

    def record_evidence(self, evidence_id, revision, kind, passed=False, artifact=None, independent_group=None):
        if not evidence_id or not revision or kind not in {"hypothesis", "observation", "test"}:
            raise GateError("invalid evidence record")
        with self._transaction():
            try:
                self.db.execute(
                    "INSERT INTO evidence (id,revision,kind,passed,artifact,independent_group) VALUES (?,?,?,?,?,?)",
                    (evidence_id, revision, kind, int(bool(passed)), artifact, independent_group),
                )
            except sqlite3.IntegrityError as exc:
                raise GateError("duplicate evidence id") from exc
            self._event("evidence", evidence_id=evidence_id, kind=kind,
                        revision=revision, declared_group=independent_group)


    def record_attested_evidence(self, receipt):
        """Accept only an integrity-checked result from the fictional evaluator."""
        from .evaluator import verify_attestation, canonical
        if self._verification_key is None or not verify_attestation(receipt, self._verification_key):
            raise GateError("invalid or missing evaluator attestation")
        with self._transaction():
            try:
                self.db.execute(
                    "INSERT INTO evidence (id,work_id,revision,kind,passed,artifact,independent_group,attestation)"
                    " VALUES (?,?,?,'test',?,?,?,?)",
                    (receipt["evidence_id"], receipt["work_id"], receipt["revision"], int(receipt["passed"]),
                     receipt["artifact_sha256"], "synthetic-evaluator", canonical(receipt)),
                )
            except sqlite3.IntegrityError as exc:
                raise GateError("duplicate evidence id") from exc
            self._event("attested_evidence", evidence_id=receipt["evidence_id"],
                        work_id=receipt["work_id"], revision=receipt["revision"],
                        passed=receipt["passed"], artifact_sha256=receipt["artifact_sha256"],
                        receipt_mac=receipt["mac"])

    def _valid_attestation(self, evidence):
        from .evaluator import verify_attestation
        if evidence is None or not evidence["attestation"] or self._verification_key is None:
            return False
        try:
            receipt = json.loads(evidence["attestation"])
        except (ValueError, TypeError):
            return False
        return (
            verify_attestation(receipt, self._verification_key)
            and receipt["evidence_id"] == evidence["id"]
            and receipt["work_id"] == evidence["work_id"]
            and receipt["revision"] == evidence["revision"]
            and receipt["artifact_sha256"] == evidence["artifact"]
            and receipt["passed"] is bool(evidence["passed"])
        )

    def has_distinct_declared_groups(self, evidence_ids, required=2):
        """Count only caller-supplied origin labels, NOT true independence."""
        if type(required) is not int or required <= 0:
            raise GateError("required declared groups must be a positive integer")
        if not isinstance(evidence_ids, (list, tuple)) or any(
                not isinstance(eid, str) or not eid for eid in evidence_ids):
            raise GateError("evidence ids must be a sequence of nonempty strings")
        if len(evidence_ids) < required or len(set(evidence_ids)) != len(evidence_ids):
            return False
        groups = set()
        for evidence_id in evidence_ids:
            row = self.db.execute("SELECT * FROM evidence WHERE id=?", (evidence_id,)).fetchone()
            if row is None or not row["independent_group"]:
                return False
            groups.add(row["independent_group"])
        return len(groups) >= required

    def submit(self, work_id, agent, generation, now, evidence_id):
        self._observe_tick(now)
        with self._transaction():
            item = self._row(work_id)
            self._fenced(item, agent, generation, now, "CLAIMED")
            ev = self.db.execute("SELECT * FROM evidence WHERE id=?", (evidence_id,)).fetchone()
            if (ev is None or ev["work_id"] != work_id or ev["revision"] != item["revision"] or ev["kind"] != "test"
                    or not ev["passed"] or not ev["artifact"] or not self._valid_attestation(ev)):
                raise GateError("missing passing revision-bound test artifact")
            self.db.execute("UPDATE work SET status='SUBMITTED',evidence_id=? WHERE id=?", (evidence_id, work_id))
            self._event("submit", work_id=work_id, agent=agent, generation=generation,
                        at_tick=now, revision=item["revision"], evidence_id=evidence_id,
                        artifact_sha256=ev["artifact"])

    def verify(self, work_id, agent, generation, now):
        self._observe_tick(now)
        with self._transaction():
            item = self._row(work_id)
            self._fenced(item, agent, generation, now, "SUBMITTED")
            for dep in json.loads(item["deps"]):
                if self._row(dep)["status"] != "DONE":
                    raise GateError("dependency not completed")
            ev = self.db.execute("SELECT * FROM evidence WHERE id=?", (item["evidence_id"],)).fetchone()
            if (ev is None or ev["work_id"] != work_id or ev["revision"] != item["revision"] or not ev["passed"]
                    or not ev["artifact"] or not self._valid_attestation(ev)):
                raise GateError("evidence no longer valid")
            self.db.execute("UPDATE work SET status='VERIFIED' WHERE id=?", (work_id,))
            self._event("verify", work_id=work_id, agent=agent, generation=generation,
                        at_tick=now, revision=item["revision"],
                        evidence_id=item["evidence_id"], artifact_sha256=ev["artifact"])

    def approve(self, work_id, reviewer):
        if not reviewer:
            raise GateError("reviewer required")
        with self._transaction():
            item = self._row(work_id)
            if item["status"] != "VERIFIED":
                raise GateError("only verified work may receive approval")
            if reviewer == item["owner"]:
                raise GateError("owner cannot self-approve")
            self.db.execute("UPDATE work SET approved_by=? WHERE id=?", (reviewer, work_id))
            self._event("approve", work_id=work_id, reviewer=reviewer,
                        revision=item["revision"], generation=item["generation"])

    def change_revision(self, work_id, revision):
        """Administrative synthetic source-change signal, not an authorization API.

        Retains an unexpired claim's owner/generation, clears stale proof and
        approval, and allows immediate resubmission on that same claim.
        """
        if not isinstance(revision, str) or not revision:
            raise GateError("revision required")
        with self._transaction():
            item = self._row(work_id)
            if item["status"] == "DONE":
                raise GateError("completed work is immutable")
            if item["revision"] == revision:
                return
            next_status = "READY" if item["status"] == "READY" else "CLAIMED"
            self.db.execute(
                "UPDATE work SET revision=?,status=?,evidence_id=NULL,"
                "approved_by=NULL,receipt=NULL WHERE id=?",
                (revision, next_status, work_id),
            )
            self._event(
                "revision_invalidated", work_id=work_id, previous_revision=item["revision"],
                revision=revision, previous_status=item["status"], status=next_status,
                generation=item["generation"], evidence_cleared=item["evidence_id"],
                approval_cleared=item["approved_by"],
            )

    def complete(self, work_id, agent, generation, now):
        self._observe_tick(now)
        with self._transaction():
            item = self._row(work_id)
            if item["status"] == "DONE" and item["owner"] == agent and item["generation"] == generation:
                return item["receipt"]
            self._fenced(item, agent, generation, now, "VERIFIED")
            if item["authority"] == "REVIEW_REQUIRED" and not item["approved_by"]:
                raise GateError("explicit approval required")
            ev = self.db.execute("SELECT * FROM evidence WHERE id=?", (item["evidence_id"],)).fetchone()
            if (ev is None or ev["work_id"] != work_id or ev["revision"] != item["revision"]
                    or not self._valid_attestation(ev)):
                raise GateError("source changed or evaluator receipt invalid; revalidate")
            receipt = hashlib.sha256(_canonical({
                "work_id": work_id, "generation": generation, "revision": item["revision"],
                "evidence_id": item["evidence_id"], "artifact": ev["artifact"],
            }).encode()).hexdigest()
            self.db.execute("UPDATE work SET status='DONE',receipt=? WHERE id=?", (receipt, work_id))
            self._event("complete", work_id=work_id, agent=agent, generation=generation,
                        at_tick=now, revision=item["revision"], authority=item["authority"],
                        evidence_id=item["evidence_id"], artifact_sha256=ev["artifact"],
                        approved_by=item["approved_by"], receipt=receipt)
            return receipt
