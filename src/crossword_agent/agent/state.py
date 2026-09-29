from __future__ import annotations

from crossword_agent.domain.models import AgentState, Puzzle
from crossword_agent.domain.parser import find_crossings


def initial_state(puzzle: Puzzle) -> AgentState:
    return AgentState(puzzle=puzzle, crossings=find_crossings(puzzle))
