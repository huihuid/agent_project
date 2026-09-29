from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Direction = Literal["across", "down"]


@dataclass(frozen=True)
class Cell:
    row: int
    col: int


@dataclass(frozen=True)
class Slot:
    id: str
    direction: Direction
    row: int
    col: int
    length: int
    clue: str

    def cells(self) -> list[Cell]:
        if self.direction == "across":
            return [Cell(self.row, self.col + i) for i in range(self.length)]
        return [Cell(self.row + i, self.col) for i in range(self.length)]


@dataclass(frozen=True)
class Crossing:
    slot_a: str
    index_a: int
    slot_b: str
    index_b: int
    row: int
    col: int


@dataclass
class Candidate:
    answer: str
    confidence: float
    source: str = "llm"
    rationale: str = ""


@dataclass
class Puzzle:
    id: str
    grid: list[str]
    slots: list[Slot]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def height(self) -> int:
        return len(self.grid)

    @property
    def width(self) -> int:
        return len(self.grid[0]) if self.grid else 0

    def slot_by_id(self) -> dict[str, Slot]:
        return {slot.id: slot for slot in self.slots}


@dataclass
class AgentConfig:
    model: str = "gpt-4.1-mini"
    mock: bool = True
    max_rounds: int = 3
    beam_size: int = 50
    candidates_per_clue: int = 8
    temperature: float = 0.2
    max_llm_calls: int = 80
    cost_budget_usd: float = 0.5
    commit_confidence_threshold: float = 0.55
    trace_dir: str = "runs"


@dataclass
class ToolCallStats:
    llm_calls: int = 0
    estimated_cost_usd: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass
class AgentState:
    puzzle: Puzzle
    crossings: list[Crossing]
    candidates: dict[str, list[Candidate]] = field(default_factory=dict)
    assignments: dict[str, str] = field(default_factory=dict)
    tentative: dict[str, str] = field(default_factory=dict)
    conflicts: list[str] = field(default_factory=list)
    stats: ToolCallStats = field(default_factory=ToolCallStats)

    def pattern_for(self, slot: Slot) -> str:
        chars = ["_"] * slot.length
        for other_id, answer in self.assignments.items():
            other_slot = self.puzzle.slot_by_id()[other_id]
            other_cells = other_slot.cells()
            for idx, cell in enumerate(slot.cells()):
                if cell in other_cells:
                    chars[idx] = answer[other_cells.index(cell)]
        return "".join(chars)


@dataclass
class SolveResult:
    assignments: dict[str, str]
    score: float
    complete: bool
    conflicts: list[str]
    grid: list[str]
