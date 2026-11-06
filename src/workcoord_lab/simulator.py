"""Deterministic fictional notification delivery; no external integrations."""


def deliver(event_ids, idempotent=False):
    deliveries = []
    processed = set()
    for event_id in event_ids:
        if idempotent and event_id in processed:
            continue
        deliveries.append(event_id)
        processed.add(event_id)
    return deliveries


def semantic_oracle(event_ids, deliveries):
    """One delivery for each distinct logical event (order unimportant)."""
    return len(deliveries) == len(set(event_ids)) and set(deliveries) == set(event_ids)
