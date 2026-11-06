"""A minimal, inspectable adaptive reading policy for fictional incidents.

Inputs: allowed source documents, task entrypoint, risk tier and reading budget.
No evaluator, gold IDs, hidden-world labels or external services are consulted.
This is a scripted policy, not an LLM or a validated autonomous diagnosis.

Important: source tags/stances are author-provided development annotations.
The navigator's in-memory source repository is NOT an OS privacy boundary.
"""
from copy import deepcopy

from .context_comparison import common_annotated_reader
from .intelligence import ContextNavigator, DEPTH, NavigationError


class PolicyError(ValueError):
    """Malformed decision-policy case or impossible state."""


def _candidate_catalog(documents):
    """Expose only document metadata, never body or diagnostic stance.

    The metadata service is simulated with a local in-memory list. A real
    system would need an access-controlled catalog and measurable lookup costs.
    """
    return [{
        "id": doc["id"],
        "sector": doc["sector"],
        "perspectives": tuple(doc["perspectives"]),
        "depth": doc["depth"],
        "revision": doc["revision"],
        "tags": tuple(doc["tags"]),
    } for doc in documents]


def _current_support_sectors(selected, hypothesis, current_revision):
    """Count sector coverage, not independent provenance or causal proof."""
    if hypothesis is None:
        return set()
    return {
        doc["sector"] for doc in selected
        if doc["revision"] == current_revision
        and doc["maturity"] in ("observed", "validated")
        and doc["signals"].get(hypothesis) == "supports"
    }


def _next_deeper(catalog, *, current_sector, perspective, issue_tags,
                 last_depth, already_selected, attempted, max_access_depth):
    """Find the lowest next depth from allowed metadata, without reading body."""
    candidates = []
    for doc in catalog:
        if (doc["sector"] != current_sector
                or perspective not in doc["perspectives"]
                or not issue_tags.intersection(doc["tags"])
                or doc["id"] in already_selected
                or DEPTH[doc["depth"]] <= DEPTH[last_depth]
                or DEPTH[doc["depth"]] > DEPTH[max_access_depth]
                or (doc["sector"], doc["depth"]) in attempted):
            continue
        candidates.append((DEPTH[doc["depth"]], doc["depth"], doc["id"]))
    return sorted(candidates)[0][1] if candidates else None


def run_adaptive_policy(documents, *, issue_tags, hypotheses,
                        current_revision, case):
    """Return a traceable decision using only permissible source material.

    A PROVISIONAL decision is never a verified outcome or authorization.
    HOLD can later be scored as justified or avoidable by a separate evaluator.
    """
    if case.get("risk_tier") not in ("low", "high"):
        raise PolicyError("risk_tier must be low or high")
    if case.get("max_access_depth") not in DEPTH:
        raise PolicyError("case requires a permitted source depth")
    if type(case.get("max_actions")) is not int or case["max_actions"] < 1:
        raise PolicyError("max_actions must be a positive integer")
    if type(case.get("max_hops")) is not int or case["max_hops"] < 0:
        raise PolicyError("max_hops must be a nonnegative integer")
    if type(case.get("max_chars")) is not int or case["max_chars"] < 1:
        raise PolicyError("max_chars must be a positive integer")
    start = case["start"]
    if start["depth"] not in DEPTH or DEPTH[start["depth"]] > DEPTH[case["max_access_depth"]]:
        raise PolicyError("initial depth exceeds permitted access")
    allowed = [
        deepcopy(doc) for doc in documents
        if DEPTH[doc["depth"]] <= DEPTH[case["max_access_depth"]]
    ]
    catalog = _candidate_catalog(allowed)
    nav = ContextNavigator(allowed, current_revision=current_revision,
                           issue_tags=issue_tags, max_chars=case["max_chars"])
    sector, perspective, depth = start["sector"], start["perspective"], start["depth"]
    attempted = {(sector, depth)}
    first = nav.navigate(sector=sector, perspective=perspective,
                         depth=depth, reason="Predeclared entrypoint; no gold labels.")
    trace = [{
        "action": "START", "sector": sector, "depth": depth,
        "new_sources": first["new_sources"],
        "read_characters": nav.total_chars(),
        "reason": "Task entrypoint",
    }]
    expanded_hops = 0
    decision = None
    stop_reason = None

    while len(trace) < case["max_actions"]:
        read = [deepcopy(doc) for doc in nav.selected.values()]
        reader = common_annotated_reader(read, hypotheses, current_revision)
        hypothesis = reader["provisional_hypothesis"]
        current_sectors = _current_support_sectors(read, hypothesis, current_revision)
        required_sectors = 1 if case["risk_tier"] == "low" else 2
        available_links = nav.steps[-1]["gaps"]["dependency_sectors_not_visited"]
        deeper = _next_deeper(
            catalog, current_sector=sector, perspective=perspective,
            issue_tags=set(issue_tags), last_depth=depth,
            already_selected=set(nav.selected), attempted=attempted,
            max_access_depth=case["max_access_depth"],
        )

        # Low-risk tasks may stop early on a single CURRENT annotated source.
        # High-risk tasks require coverage of >=2 sectors and no known gaps.
        # Neither policy is a calibrated decision-quality or independence test.
        if (hypothesis is not None
                and len(current_sectors) >= required_sectors
                and not available_links
                and deeper is None):
            decision = "PROVISIONAL"
            stop_reason = "OBSERVED_COVERAGE_CONDITION_MET_NOT_EXTERNALLY_VALIDATED"
            break
        if (case["risk_tier"] == "low" and hypothesis is not None
                and len(current_sectors) >= required_sectors
                and not available_links):
            decision = "PROVISIONAL"
            stop_reason = "LOW_RISK_EARLY_STOP_WITH_CURRENT_ANNOTATED_EVIDENCE"
            break

        # Escalation sees metadata only; it cannot choose by unseen stances.
        if deeper is not None:
            depth = deeper
            attempted.add((sector, depth))
            step = nav.navigate(
                sector=sector, perspective=perspective, depth=depth,
                reason="Inspect permitted deeper material in the current sector.",
            )
            trace.append({
                "action": "DEEPEN", "sector": sector, "depth": depth,
                "new_sources": step["new_sources"],
                "read_characters": nav.total_chars(),
                "reason": "Catalog indicates an unread deeper source.",
            })
            continue

        if available_links and expanded_hops < case["max_hops"]:
            sector = available_links[0]
            depth = case["expansion_depth"]
            if DEPTH[depth] > DEPTH[case["max_access_depth"]]:
                raise PolicyError("expansion depth exceeds permitted access")
            attempted.add((sector, depth))
            expanded_hops += 1
            step = nav.navigate(
                sector=sector, perspective=perspective, depth=depth,
                reason="Follow the first unvisited sector declared by read sources.",
            )
            trace.append({
                "action": "EXPAND", "sector": sector, "depth": depth,
                "new_sources": step["new_sources"],
                "read_characters": nav.total_chars(),
                "reason": "Follow a visible declared dependency, not a gold oracle.",
            })
            continue
        decision = "HOLD"
        if any(step["gaps"]["unread_due_to_budget"] for step in nav.steps):
            stop_reason = "BUDGET_EXHAUSTED_OR_SOURCE_DOES_NOT_FIT"
        elif hypothesis is None:
            stop_reason = "AMBIGUOUS_OR_NO_POSITIVE_ANNOTATED_EVIDENCE"
        elif len(current_sectors) < required_sectors:
            stop_reason = "INSUFFICIENT_CURRENT_SECTOR_COVERAGE"
        elif available_links:
            stop_reason = "UNRESOLVED_DEPENDENCY_AT_HOP_LIMIT"
        else:
            stop_reason = "NO_DISCRIMINATING_ACTION_REMAINING"
        break

    if decision is None:
        decision, stop_reason = "HOLD", "ACTION_BUDGET_EXHAUSTED"
    final_read = [deepcopy(doc) for doc in nav.selected.values()]
    final_reader = common_annotated_reader(final_read, hypotheses, current_revision)
    trace.append({
        "action": "STAY" if decision == "PROVISIONAL" else "HOLD",
        "reason": stop_reason,
        "sector": sector,
        "depth": depth,
        "new_sources": [],
        "read_characters": nav.total_chars(),
    })
    if nav.total_chars() > case["max_chars"]:
        raise PolicyError("selector exceeded the source-body reading cap")
    return {
        "policy": "adaptive_evidence_escalation/v0",
        "decision": decision,
        "reason": stop_reason,
        "provisional_hypothesis": final_reader["provisional_hypothesis"]
                                  if decision == "PROVISIONAL" else None,
        "uncommitted_hypothesis": final_reader["provisional_hypothesis"],
        "risk_tier": case["risk_tier"],
        "selected_source_ids": list(nav.selected),
        "read_characters": nav.total_chars(),
        "budget_characters": case["max_chars"],
        "expanded_hops": expanded_hops,
        "trace": trace,
        "unread_budget_source_ids": sorted({
            source for step in nav.steps
            for source in step["gaps"]["unread_due_to_budget"]
        }),
        "source_metadata_catalog_entries": len(catalog),
        "state": "INVESTIGATION_ONLY_NOT_APPROVED",
    }
