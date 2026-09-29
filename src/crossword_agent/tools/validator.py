from __future__ import annotations

from crossword_agent.domain.models import Crossing, Puzzle


def validate_assignments(puzzle: Puzzle, crossings: list[Crossing], assignments: dict[str, str]) -> list[str]:
    issues: list[str] = []
    slots = puzzle.slot_by_id()
    for slot_id, answer in assignments.items():
        slot = slots[slot_id]
        if len(answer) != slot.length:
            issues.append(f"{slot_id}: expected length {slot.length}, got {len(answer)}")
        if not answer.isalpha() or not answer.isupper():
            issues.append(f"{slot_id}: answer must be uppercase letters")

    for crossing in crossings:
        left = assignments.get(crossing.slot_a)
        right = assignments.get(crossing.slot_b)
        if not left or not right:
            continue
        if left[crossing.index_a] != right[crossing.index_b]:
            issues.append(
                f"{crossing.slot_a}[{crossing.index_a}]={left[crossing.index_a]} conflicts with "
                f"{crossing.slot_b}[{crossing.index_b}]={right[crossing.index_b]} at ({crossing.row},{crossing.col})"
            )
    return issues
