from __future__ import annotations

from dataclasses import dataclass

from crossword_agent.domain.models import Candidate, Crossing, Puzzle, SolveResult
from crossword_agent.domain.renderer import render_grid
from crossword_agent.tools.validator import validate_assignments


@dataclass
class ConstraintSolverTool:
    beam_size: int = 50

    def run(self, puzzle: Puzzle, crossings: list[Crossing], candidates: dict[str, list[Candidate]]) -> SolveResult:
        slot_ids = [slot.id for slot in puzzle.slots]
        order = sorted(slot_ids, key=lambda sid: (len(candidates.get(sid, [])), -_crossing_count(sid, crossings)))
        beams: list[tuple[dict[str, str], float]] = [({}, 0.0)]

        for slot_id in order:
            choices = candidates.get(slot_id, [])
            if not choices:
                choices = [Candidate("_" * puzzle.slot_by_id()[slot_id].length, 0.0, "empty")]
            next_beams: list[tuple[dict[str, str], float]] = []
            for assignment, score in beams:
                for candidate in choices:
                    if "_" in candidate.answer:
                        continue
                    proposal = {**assignment, slot_id: candidate.answer}
                    conflicts = validate_assignments(puzzle, crossings, proposal)
                    if conflicts:
                        continue
                    next_beams.append((proposal, score + candidate.confidence))
            if not next_beams:
                next_beams = beams
            beams = sorted(next_beams, key=lambda item: item[1], reverse=True)[: self.beam_size]

        best, score = beams[0]
        conflicts = validate_assignments(puzzle, crossings, best)
        complete = len(best) == len(puzzle.slots) and not conflicts
        return SolveResult(best, score, complete, conflicts, render_grid(puzzle, best))


def _crossing_count(slot_id: str, crossings: list[Crossing]) -> int:
    return sum(1 for crossing in crossings if crossing.slot_a == slot_id or crossing.slot_b == slot_id)
