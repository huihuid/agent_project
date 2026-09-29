from __future__ import annotations

from dataclasses import dataclass, field

from crossword_agent.domain.models import AgentState, SolveResult
from crossword_agent.tools.validator import validate_assignments


@dataclass
class VerificationReport:
    complete: bool
    accepted: bool
    issues: list[str] = field(default_factory=list)
    low_confidence_slots: list[str] = field(default_factory=list)
    recommended_repairs: list[str] = field(default_factory=list)


class Verifier:
    """Judge/evaluator/verifier layer for proposed agent actions."""

    def verify_solution(self, state: AgentState, result: SolveResult, confidence_threshold: float) -> VerificationReport:
        issues = validate_assignments(state.puzzle, state.crossings, result.assignments)
        low_confidence = self._low_confidence_slots(state, result, confidence_threshold)
        recommended = sorted(set(_slots_from_issues(issues) + low_confidence))
        return VerificationReport(
            complete=result.complete and not issues,
            accepted=not issues and not low_confidence,
            issues=issues,
            low_confidence_slots=low_confidence,
            recommended_repairs=recommended,
        )

    def _low_confidence_slots(self, state: AgentState, result: SolveResult, threshold: float) -> list[str]:
        low: list[str] = []
        for slot_id, answer in result.assignments.items():
            candidates = state.candidates.get(slot_id, [])
            confidence = next((candidate.confidence for candidate in candidates if candidate.answer == answer), 0.0)
            if confidence < threshold:
                low.append(slot_id)
        return low


def _slots_from_issues(issues: list[str]) -> list[str]:
    slots: list[str] = []
    for issue in issues:
        token = issue.split(":", 1)[0]
        if token:
            slots.append(token.split("[", 1)[0])
    return slots
