"""Revision-aware, sectorized synthetic context navigation.

This educational selector operates on human-authored metadata. It does not
authenticate sources, infer facts from prose, approve actions or call an LLM.
All selection costs are exact source-body characters, NOT tokenizer tokens.
"""
from copy import deepcopy

DEPTH = {"overview": 1, "focused": 2, "deep": 3}
MATURITY = {"draft", "historical", "observed", "validated"}
SIGNALS = {"supports", "contradicts"}


class NavigationError(ValueError):
    """The fixture or navigation request violates the public contract."""


def _nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _validate_source(doc):
    needed = {"id", "title", "body", "sector", "perspectives", "depth",
              "revision", "maturity", "tags", "depends_on", "signals"}
    if not isinstance(doc, dict) or not needed.issubset(doc):
        raise NavigationError("context source lacks required fields")
    for field in ("id", "title", "body", "sector", "revision"):
        if not _nonempty_string(doc[field]):
            raise NavigationError("source field must be nonempty: " + field)
    if doc["depth"] not in DEPTH or doc["maturity"] not in MATURITY:
        raise NavigationError("unknown depth or maturity")
    for field in ("perspectives", "tags", "depends_on"):
        if (not isinstance(doc[field], list)
                or not all(_nonempty_string(x) for x in doc[field])):
            raise NavigationError("source field must be a string list: " + field)
    if not doc["perspectives"] or not doc["tags"]:
        raise NavigationError("perspectives and tags must be nonempty")
    if (not isinstance(doc["signals"], dict)
            or not all(_nonempty_string(k) and v in SIGNALS
                       for k, v in doc["signals"].items())):
        raise NavigationError("diagnostic signals must be annotated stances")
    return deepcopy(doc)


class ContextNavigator:
    """Explicit bounded navigation; expansion is requested, never automatic."""

    def __init__(self, documents, *, current_revision, issue_tags, max_chars=2000):
        if not _nonempty_string(current_revision):
            raise NavigationError("current revision is required")
        if (not isinstance(issue_tags, (list, tuple))
                or not issue_tags or not all(_nonempty_string(x) for x in issue_tags)):
            raise NavigationError("issue tags must be nonempty strings")
        if type(max_chars) is not int or max_chars < 1:
            raise NavigationError("character budget must be a positive integer")
        if not isinstance(documents, list):
            raise NavigationError("documents must be a list")
        records = [_validate_source(doc) for doc in documents]
        if len(set(d["id"] for d in records)) != len(records):
            raise NavigationError("duplicate context source identifier")
        self.documents = {d["id"]: d for d in records}
        self.current_revision = current_revision
        self.issue_tags = frozenset(issue_tags)
        self.max_chars = max_chars
        self.selected = {}
        self.steps = []
        self.visited_sectors = set()

    def relevant_corpus_chars(self):
        return sum(len(doc["body"]) for doc in self.documents.values()
                   if self.issue_tags.intersection(doc["tags"]))

    def total_chars(self):
        return sum(len(doc["body"]) for doc in self.selected.values())

    def navigate(self, *, sector, perspective, depth, reason):
        if (not _nonempty_string(sector) or not _nonempty_string(perspective)
                or not _nonempty_string(reason) or depth not in DEPTH):
            raise NavigationError("sector, perspective, depth and reason are required")
        match = [
            doc for doc in self.documents.values()
            if doc["sector"] == sector
            and perspective in doc["perspectives"]
            and DEPTH[doc["depth"]] <= DEPTH[depth]
            and self.issue_tags.intersection(doc["tags"])
        ]
        maturity_order = {"validated": 0, "observed": 1, "historical": 2, "draft": 3}
        match.sort(key=lambda doc: (
            doc["revision"] != self.current_revision,
            maturity_order[doc["maturity"]],
            DEPTH[doc["depth"]], doc["id"],
        ))
        new_ids, already_ids, budget_excluded = [], [], []
        for doc in match:
            source_id = doc["id"]
            if source_id in self.selected:
                already_ids.append(source_id)
                continue
            if self.total_chars() + len(doc["body"]) > self.max_chars:
                budget_excluded.append(source_id)
                continue
            self.selected[source_id] = doc
            new_ids.append(source_id)
        self.visited_sectors.add(sector)
        linked = sorted({
            dep for doc in self.selected.values() for dep in doc["depends_on"]
            if dep not in self.visited_sectors
        })
        gap = {
            "no_matching_source": not bool(match),
            "unread_due_to_budget": budget_excluded,
            # Do not disclose stance/signals of evidence excluded by budget.
            # Unread source IDs are observable metadata, not an answer key.
            "dependency_sectors_not_visited": linked,
        }
        step = {
            "number": len(self.steps) + 1,
            "sector": sector,
            "perspective": perspective,
            "depth": depth,
            "reason": reason,
            "new_sources": new_ids,
            "already_read": already_ids,
            "gaps": gap,
            "new_chars": sum(len(self.documents[i]["body"]) for i in new_ids),
            "cumulative_unique_chars": self.total_chars(),
            "cumulative_budget_chars": self.max_chars,
        }
        self.steps.append(step)
        return deepcopy(step)

    def context(self):
        """Return source identity and limitations, not an authority escalation."""
        out = []
        for source_id, doc in self.selected.items():
            current = doc["revision"] == self.current_revision
            out.append({
                "id": source_id,
                "title": doc["title"],
                "body": doc["body"],
                "sector": doc["sector"],
                "perspectives": list(doc["perspectives"]),
                "depth": doc["depth"],
                "source_revision": doc["revision"],
                "current_revision": current,
                "maturity": doc["maturity"],
                "validated_for_current_revision": current and doc["maturity"] == "validated",
                "signals": deepcopy(doc["signals"]),
                "source_role": "investigation_only",
                "read_characters": len(doc["body"]),
            })
        return out

    def assess(self, hypotheses):
        """Illustrative metadata tally; never a diagnosis or completion oracle.

        Stances are human-annotated in the fixture, not inferred from prose.
        Weights are uncalibrated and published only to make changes inspectable.
        """
        if (not isinstance(hypotheses, (tuple, list)) or not hypotheses
                or not all(_nonempty_string(x) for x in hypotheses)
                or len(set(hypotheses)) != len(hypotheses)):
            raise NavigationError("hypotheses must be a unique nonempty list")
        scores = {name: 0 for name in hypotheses}
        support = {name: [] for name in hypotheses}
        contradict = {name: [] for name in hypotheses}
        for doc in self.selected.values():
            weight = (3 if doc["maturity"] == "validated"
                      else 2 if doc["maturity"] == "observed" else 1)
            if doc["revision"] != self.current_revision:
                weight = 1  # Former validation does not become current authority.
            for name, stance in doc["signals"].items():
                if name not in scores:
                    continue
                if stance == "supports":
                    scores[name] += weight
                    support[name].append(doc["id"])
                else:
                    scores[name] -= weight
                    contradict[name].append(doc["id"])
        best_score = max(scores.values())
        leaders = sorted(name for name, score in scores.items() if score == best_score)
        leader = leaders[0] if best_score > 0 and len(leaders) == 1 else None
        conflicts = [{
            "hypothesis": name, "supports": support[name],
            "contradicts": contradict[name],
        } for name in hypotheses if support[name] and contradict[name]]
        return {
            "status": "PROVISIONAL_INVESTIGATION_ONLY",
            "leading_hypothesis": leader,
            "illustrative_scores": scores,
            "conflicts": conflicts,
            "old_revision_sources": [
                doc["id"] for doc in self.selected.values()
                if doc["revision"] != self.current_revision
            ],
            "current_nonvalidated_sources": [
                doc["id"] for doc in self.selected.values()
                if doc["revision"] == self.current_revision
                and doc["maturity"] != "validated"
            ],
            "source_ids": list(self.selected),
            "requires_independent_test": True,
            "scoring_limit": "Human-annotated fixture stances and arbitrary illustrative weights; not an AI benchmark.",
        }
