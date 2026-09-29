from crossword_agent.domain.parser import load_puzzle
from crossword_agent.evaluation.metrics import evaluate_solution


def test_evaluate_solution_reports_word_and_cell_accuracy():
    puzzle = load_puzzle("data/eval/mini_001.json")
    gold = {"A1": "CAT", "A2": "ARE", "A3": "TEN", "D1": "CAT", "D2": "ARE", "D3": "TEN"}
    predicted = {"A1": "CAT", "A2": "ARE", "A3": "TIN", "D1": "CAT", "D2": "ARE", "D3": "TEN"}
    metrics = evaluate_solution(puzzle, predicted, gold)
    assert metrics.word_accuracy == 5 / 6
    assert metrics.cell_accuracy == 17 / 18
    assert not metrics.full_puzzle_solved
