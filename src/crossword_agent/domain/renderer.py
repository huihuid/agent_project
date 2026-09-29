from __future__ import annotations

from .models import Puzzle


def render_grid(puzzle: Puzzle, assignments: dict[str, str]) -> list[str]:
    cells = [list(row) for row in puzzle.grid]
    for slot in puzzle.slots:
        answer = assignments.get(slot.id)
        if not answer:
            continue
        for cell, char in zip(slot.cells(), answer):
            cells[cell.row][cell.col] = char
    return ["".join(row) for row in cells]


def render_solution(puzzle: Puzzle, assignments: dict[str, str]) -> str:
    lines = ["Solved Grid"]
    lines.extend(" ".join(row) for row in render_grid(puzzle, assignments))
    lines.append("")
    for direction in ("across", "down"):
        lines.append(direction.title())
        for slot in puzzle.slots:
            if slot.direction == direction:
                answer = assignments.get(slot.id, "?" * slot.length)
                lines.append(f"{slot.id}. {slot.clue} -> {answer}")
        lines.append("")
    return "\n".join(lines).rstrip()
