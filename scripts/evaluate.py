#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crossword_agent.agent.controller import CrosswordAgent
from crossword_agent.baselines.independent import solve_direct_mock, solve_independent
from crossword_agent.config import load_config
from crossword_agent.domain.parser import load_puzzle, load_solution
from crossword_agent.evaluation.metrics import aggregate, evaluate_solution


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate crossword-solving methods.")
    parser.add_argument("--puzzles", default="data/eval")
    parser.add_argument("--gold", default="data/gold")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--method", choices=["agent", "independent", "direct"], default="agent")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--real", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config, mock=False if args.real else True if args.mock else None)
    metrics = []
    operational = []
    for puzzle_path in sorted(Path(args.puzzles).glob("*.json")):
        puzzle = load_puzzle(puzzle_path)
        gold = load_solution(Path(args.gold) / f"{puzzle.id}_solution.json")
        if args.method == "agent":
            result, trace = CrosswordAgent(config).solve(puzzle)
            predicted = result.assignments
            operational.append(json.loads((trace.run_dir / "metrics.json").read_text()))
        elif args.method == "independent":
            predicted = solve_independent(puzzle, config)
        else:
            predicted = solve_direct_mock(puzzle, config)
        metrics.append(evaluate_solution(puzzle, predicted, gold))

    payload = {"method": args.method, "aggregate": aggregate(metrics), "puzzles": [m.to_dict() for m in metrics]}
    if operational:
        payload["operational"] = {
            "avg_llm_calls": sum(item["llm_calls"] for item in operational) / len(operational),
            "avg_estimated_cost_usd": sum(item["estimated_cost_usd"] for item in operational) / len(operational),
            "avg_wall_time_seconds": sum(item["wall_time_seconds"] for item in operational) / len(operational),
        }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
