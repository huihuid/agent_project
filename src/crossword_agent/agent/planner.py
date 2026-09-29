from __future__ import annotations

from dataclasses import dataclass

from crossword_agent.domain.models import AgentState, Slot


@dataclass(frozen=True)
class Action:
    tool: str
    slot_id: str
    reason: str


class Planner:
    def plan_candidate_generation(self, state: AgentState) -> list[Action]:
        slots = state.puzzle.slot_by_id()
        unsolved = [slot for slot in state.puzzle.slots if slot.id not in state.assignments]
        low_coverage = [slot for slot in state.puzzle.slots if not state.candidates.get(slot.id)]
        target_slots = {slot.id for slot in unsolved + low_coverage}
        for slot_id in state.conflicts:
            target_slots.add(slot_id)
        ordered = sorted((slots[slot_id] for slot_id in target_slots), key=lambda slot: (slot.length, slot.id))
        return [Action("solve_clue", slot.id, _reason(slot, state)) for slot in ordered]


def _reason(slot: Slot, state: AgentState) -> str:
    if slot.id in state.conflicts:
        return "repair_conflict"
    if not state.candidates.get(slot.id):
        return "no_candidates"
    return "unsolved"
