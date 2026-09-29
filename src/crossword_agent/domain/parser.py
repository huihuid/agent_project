from __future__ import annotations

import json
from pathlib import Path

from .models import Cell, Crossing, Puzzle, Slot


def load_puzzle(path: str | Path) -> Puzzle:
    data = json.loads(Path(path).read_text())
    slots = [
        Slot(
            id=item["id"],
            direction=item["direction"],
            row=int(item["row"]),
            col=int(item["col"]),
            length=int(item["length"]),
            clue=item["clue"],
        )
        for item in data["slots"]
    ]
    return Puzzle(id=data["id"], grid=data["grid"], slots=slots, metadata=data.get("metadata", {}))


def load_solution(path: str | Path) -> dict[str, str]:
    data = json.loads(Path(path).read_text())
    return {k: v.upper() for k, v in data["answers"].items()}


def find_crossings(puzzle: Puzzle) -> list[Crossing]:
    index: dict[Cell, list[tuple[str, int]]] = {}
    for slot in puzzle.slots:
        for i, cell in enumerate(slot.cells()):
            index.setdefault(cell, []).append((slot.id, i))

    crossings: list[Crossing] = []
    for cell, owners in index.items():
        if len(owners) < 2:
            continue
        for left in range(len(owners)):
            for right in range(left + 1, len(owners)):
                slot_a, index_a = owners[left]
                slot_b, index_b = owners[right]
                crossings.append(Crossing(slot_a, index_a, slot_b, index_b, cell.row, cell.col))
    return crossings
