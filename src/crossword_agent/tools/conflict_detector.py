from __future__ import annotations

from collections import Counter

from crossword_agent.domain.models import Crossing


def conflicted_slots(crossings: list[Crossing], assignments: dict[str, str]) -> list[str]:
    counts: Counter[str] = Counter()
    for crossing in crossings:
        left = assignments.get(crossing.slot_a)
        right = assignments.get(crossing.slot_b)
        if not left or not right:
            continue
        if left[crossing.index_a] != right[crossing.index_b]:
            counts[crossing.slot_a] += 1
            counts[crossing.slot_b] += 1
    return [slot for slot, _ in counts.most_common()]
