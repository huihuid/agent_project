from __future__ import annotations

from dataclasses import dataclass, asdict

from crossword_agent.domain.models import Puzzle


@dataclass
class PuzzleMetrics:
    puzzle_id: str
    cell_accuracy: float
    word_accuracy: float
    full_puzzle_solved: bool
    answered_words: int
    total_words: int

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_solution(puzzle: Puzzle, predicted: dict[str, str], gold: dict[str, str]) -> PuzzleMetrics:
    correct_words = sum(1 for slot_id, answer in gold.items() if predicted.get(slot_id) == answer)
    total_words = len(gold)

    correct_cells = 0
    total_cells = 0
    slots = puzzle.slot_by_id()
    for slot_id, gold_answer in gold.items():
        slot = slots[slot_id]
        predicted_answer = predicted.get(slot_id, "")
        for i in range(slot.length):
            total_cells += 1
            if i < len(predicted_answer) and predicted_answer[i] == gold_answer[i]:
                correct_cells += 1

    return PuzzleMetrics(
        puzzle_id=puzzle.id,
        cell_accuracy=correct_cells / total_cells if total_cells else 0.0,
        word_accuracy=correct_words / total_words if total_words else 0.0,
        full_puzzle_solved=correct_words == total_words,
        answered_words=len(predicted),
        total_words=total_words,
    )


def aggregate(metrics: list[PuzzleMetrics]) -> dict:
    if not metrics:
        return {}
    return {
        "puzzles": len(metrics),
        "cell_accuracy": sum(item.cell_accuracy for item in metrics) / len(metrics),
        "word_accuracy": sum(item.word_accuracy for item in metrics) / len(metrics),
        "full_puzzle_accuracy": sum(1 for item in metrics if item.full_puzzle_solved) / len(metrics),
    }
