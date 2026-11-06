"""Synthetic context selection, sandbox checks, and scoring boundaries."""

from pathlib import PurePosixPath

from .ledger import GateError


def discover(documents, keyword):
    """Return relevant validated docs; retain warnings about excluded history."""
    chosen, warnings = [], []
    for doc in documents:
        if keyword.lower() not in (doc["title"] + " " + doc["body"]).lower():
            continue
        if doc["authority"] != "validated":
            warnings.append({"id": doc["id"], "reason": "not validated authority"})
        else:
            chosen.append(doc["id"])
    return {"selected": chosen, "excluded_with_reason": warnings}


class FakeSandbox:
    """Virtual file interface. No filesystem or process execution."""

    def __init__(self, files):
        self.files = dict(files)
        self.denials = []

    def access(self, action, path):
        normalized = str(PurePosixPath(path))
        if (action not in {"read", "edit"} or normalized.startswith("/")
                or ".." in PurePosixPath(path).parts or normalized.startswith("oracle/")
                or normalized.startswith("evaluator/")):
            self.denials.append({"action": action, "path": path})
            raise GateError("outside synthetic sandbox scope")
        if action == "read":
            if normalized not in self.files:
                raise GateError("synthetic file not found")
            return self.files[normalized]
        if normalized not in self.files:
            raise GateError("edits require an existing synthetic file")
        return "edit allowed in synthetic sandbox only"


def preliminary_decision_label(resolvable, decision):
    """Toy routing label, not an external semantic benchmark scorer.

    Neither a HOLD nor a repair receives a final validity grade from this
    function. 'resolvable' is only illustrative synthetic fixture metadata.
    """
    if decision == "HOLD":
        return "INCOMPLETE" if resolvable else "REQUIRES_ABSTENTION_REVIEW"
    if decision == "REPAIR":
        return "REQUIRES_INDEPENDENT_TEST"
    return "INCOMPLETE"
