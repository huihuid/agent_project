from __future__ import annotations

from crossword_agent.domain.models import AgentConfig, Puzzle, ToolCallStats
from crossword_agent.tools.clue_solver import ClueSolverTool


def solve_independent(puzzle: Puzzle, config: AgentConfig) -> dict[str, str]:
    tool = ClueSolverTool(config)
    stats = ToolCallStats()
    answers: dict[str, str] = {}
    for slot in puzzle.slots:
        candidates = tool.run(slot, "_" * slot.length, stats)
        if candidates:
            answers[slot.id] = candidates[0].answer
    return answers


def solve_direct_mock(puzzle: Puzzle, config: AgentConfig) -> dict[str, str]:
    # A deliberately weak baseline: it guesses each clue independently and ignores crossings.
    return solve_independent(puzzle, config)
