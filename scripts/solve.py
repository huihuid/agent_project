#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crossword_agent.agent.controller import CrosswordAgent
from crossword_agent.config import load_config
from crossword_agent.domain.parser import load_puzzle
from crossword_agent.domain.renderer import render_solution


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve a crossword puzzle with the agent.")
    parser.add_argument("puzzle")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--mock", action="store_true", help="Force deterministic mock clue solving.")
    parser.add_argument("--real", action="store_true", help="Force real LLM clue solving.")
    parser.add_argument("--model")
    parser.add_argument("--max-rounds", type=int)
    parser.add_argument("--beam-size", type=int)
    args = parser.parse_args()

    config = load_config(
        args.config,
        mock=False if args.real else True if args.mock else None,
        model=args.model,
        max_rounds=args.max_rounds,
        beam_size=args.beam_size,
    )
    puzzle = load_puzzle(args.puzzle)
    result, trace = CrosswordAgent(config).solve(puzzle)
    print(render_solution(puzzle, result.assignments))
    print()
    print(f"complete={result.complete} score={result.score:.2f}")
    print(f"trace_dir={trace.run_dir}")


if __name__ == "__main__":
    main()
