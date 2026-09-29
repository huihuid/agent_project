from crossword_agent.domain.models import Candidate
from crossword_agent.domain.parser import find_crossings, load_puzzle
from crossword_agent.tools.constraint_solver import ConstraintSolverTool


def test_constraint_solver_finds_consistent_solution():
    puzzle = load_puzzle("data/eval/mini_001.json")
    candidates = {
        "A1": [Candidate("CAT", 0.9)],
        "A2": [Candidate("ARE", 0.9)],
        "A3": [Candidate("TEN", 0.9)],
        "D1": [Candidate("CAT", 0.9)],
        "D2": [Candidate("ARE", 0.9)],
        "D3": [Candidate("TEN", 0.9)],
    }
    result = ConstraintSolverTool().run(puzzle, find_crossings(puzzle), candidates)
    assert result.complete
    assert result.grid == ["CAT", "ARE", "TEN"]
