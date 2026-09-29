from crossword_agent.agent.state import initial_state
from crossword_agent.agent.verifier import Verifier
from crossword_agent.domain.models import Candidate, SolveResult
from crossword_agent.domain.parser import load_puzzle


def test_verifier_flags_low_confidence_assignment():
    puzzle = load_puzzle("data/eval/mini_001.json")
    state = initial_state(puzzle)
    state.candidates = {"A1": [Candidate("CAT", 0.2)]}
    result = SolveResult(assignments={"A1": "CAT"}, score=0.2, complete=False, conflicts=[], grid=[])

    report = Verifier().verify_solution(state, result, confidence_threshold=0.55)

    assert not report.accepted
    assert report.low_confidence_slots == ["A1"]
    assert report.recommended_repairs == ["A1"]
