from __future__ import annotations

from dataclasses import asdict
from time import perf_counter

from crossword_agent.agent.planner import Planner
from crossword_agent.agent.state import initial_state
from crossword_agent.agent.trace import TraceLogger
from crossword_agent.agent.verifier import Verifier
from crossword_agent.domain.models import AgentConfig, Puzzle, SolveResult
from crossword_agent.tools.clue_solver import ClueSolverTool
from crossword_agent.tools.conflict_detector import conflicted_slots
from crossword_agent.tools.constraint_solver import ConstraintSolverTool


class CrosswordAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.planner = Planner()
        self.verifier = Verifier()
        self.clue_solver = ClueSolverTool(config)
        self.constraint_solver = ConstraintSolverTool(config.beam_size)

    def solve(self, puzzle: Puzzle) -> tuple[SolveResult, TraceLogger]:
        started = perf_counter()
        state = initial_state(puzzle)
        trace = TraceLogger(self.config.trace_dir, puzzle.id)
        trace.log("observe_puzzle", puzzle_id=puzzle.id, slots=len(puzzle.slots), crossings=len(state.crossings))

        best: SolveResult | None = None
        for round_number in range(1, self.config.max_rounds + 1):
            trace.log("plan_round", round=round_number, conflicts=state.conflicts)
            for action in self.planner.plan_candidate_generation(state):
                slot = state.puzzle.slot_by_id()[action.slot_id]
                pattern = state.pattern_for(slot)
                trace.log(
                    "tool_call",
                    tool=action.tool,
                    slot=slot.id,
                    direction=slot.direction,
                    length=slot.length,
                    clue=slot.clue,
                    pattern=pattern,
                    reason=action.reason,
                )
                candidates = self.clue_solver.run(slot, pattern, state.stats)
                if candidates:
                    existing = {candidate.answer: candidate for candidate in state.candidates.get(slot.id, [])}
                    for candidate in candidates:
                        existing[candidate.answer] = candidate
                    state.candidates[slot.id] = sorted(existing.values(), key=lambda item: item.confidence, reverse=True)
                trace.log(
                    "tool_result",
                    tool=action.tool,
                    slot=slot.id,
                    candidates=[asdict(candidate) for candidate in state.candidates.get(slot.id, [])],
                )

            result = self.constraint_solver.run(state.puzzle, state.crossings, state.candidates)
            best = result if best is None or result.score > best.score else best
            state.assignments = result.assignments
            state.conflicts = conflicted_slots(state.crossings, result.assignments)
            verification = self.verifier.verify_solution(state, result, self.config.commit_confidence_threshold)
            state.conflicts = sorted(set(state.conflicts + verification.recommended_repairs))
            trace.log(
                "verify_solution",
                round=round_number,
                complete=verification.complete,
                accepted=verification.accepted,
                score=result.score,
                assignments=result.assignments,
                issues=verification.issues,
                low_confidence_slots=verification.low_confidence_slots,
                recommended_repairs=verification.recommended_repairs,
            )

            if verification.complete:
                break
            if state.stats.estimated_cost_usd > self.config.cost_budget_usd:
                trace.log("stop", reason="cost_budget_exceeded", estimated_cost_usd=state.stats.estimated_cost_usd)
                break

        assert best is not None
        elapsed = perf_counter() - started
        trace.write_json("final_solution.json", {"grid": best.grid, "answers": best.assignments, "complete": best.complete})
        trace.write_json(
            "metrics.json",
            {
                "wall_time_seconds": elapsed,
                "llm_calls": state.stats.llm_calls,
                "estimated_cost_usd": state.stats.estimated_cost_usd,
                "complete": best.complete,
                "score": best.score,
            },
        )
        return best, trace
