"""Common public evaluator for a minimal adaptive navigation experiment.

The selector module receives no expected answers or evaluator fields. The
rubric is deliberately PUBLIC DEVELOPMENT DATA and cannot certify agents.
Results separate unsupported guesses from holds caused by insufficient access
and from avoidable stops with still-accessible sources.
"""
from copy import deepcopy


ORACLE_CLASSES = {
    "RESOLVABLE_WITH_PERMITTED_ACCESS",
    "INDETERMINATE_UNDER_ALLOWED_DEPTH",
    "BUDGET_INSUFFICIENT",
}


def visible_sources(documents, allowed_depth, depth_order):
    if allowed_depth not in depth_order:
        raise ValueError("unknown permitted access depth")
    return [
        deepcopy(doc) for doc in documents
        if depth_order[doc["depth"]] <= depth_order[allowed_depth]
    ]


def validate_counterfactual_pair(first_visible, second_visible, first_cause, second_cause):
    """The visible inputs must be byte-equivalent; hidden causes must differ."""
    if first_visible != second_visible:
        raise ValueError("counterfactual pair leaks different visible source records")
    if first_cause == second_cause:
        raise ValueError("counterfactual pair has no competing hidden world")
    return True


def grade_public_development_trace(record, gold):
    if gold["outcome_class"] not in ORACLE_CLASSES:
        raise ValueError("unknown evaluator access class")
    expected = gold["expected_label"]
    needed = set(gold["required_sources"])
    observed = set(record["selected_source_ids"])
    if not needed:
        raise ValueError("empty required source set")
    recovered = sorted(needed & observed)
    missing = sorted(needed - observed)
    decision = record["decision"]
    proposed = record.get("provisional_hypothesis")
    recall = round(len(recovered) / len(needed), 6)
    if decision == "PROVISIONAL":
        # A correct-sounding response is insufficient without required proof.
        category = ("SUPPORTED_PROVISIONAL" if proposed == expected and not missing
                    else "UNSUPPORTED_PROVISIONAL")
    elif decision == "HOLD":
        if gold["outcome_class"] == "INDETERMINATE_UNDER_ALLOWED_DEPTH":
            category = "JUSTIFIED_HOLD_UNDER_DECLARED_ACCESS"
        elif gold["outcome_class"] == "BUDGET_INSUFFICIENT":
            category = "RESOURCE_LIMITED_HOLD_NOT_SCORED_SUCCESS"
        else:
            category = "AVOIDABLE_HOLD"
    elif decision == "BUDGET_INFEASIBLE":
        category = "COMPARATOR_INFEASIBLE_UNDER_EQUAL_CAP"
    else:
        raise ValueError("unknown submission decision")
    return {
        "category": category,
        "expected_label": expected,
        "declared_access_class": gold["outcome_class"],
        "decisive_recall": recall,
        "recovered_required_sources": recovered,
        "missing_required_sources": missing,
        "proposed_label_matches": proposed == expected if proposed is not None else None,
        "final_causal_correctness_tested": False,
        "real_agent_quality_tested": False,
    }
