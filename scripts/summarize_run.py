#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Print a compact timeline for one agent run.")
    parser.add_argument("run_dir", help="Path like runs/20260929_083206_mini_004")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    trace_path = run_dir / "trace.jsonl"
    final_path = run_dir / "final_solution.json"
    metrics_path = run_dir / "metrics.json"

    events = [json.loads(line) for line in trace_path.read_text().splitlines()]
    final = json.loads(final_path.read_text()) if final_path.exists() else {}
    metrics = json.loads(metrics_path.read_text()) if metrics_path.exists() else {}

    print(f"Run: {run_dir}")
    print()
    print("Timeline")
    for event in events:
        kind = event.get("event")
        step = event.get("step")
        if kind == "observe_puzzle":
            print(f"{step}. observe puzzle={event.get('puzzle_id')} slots={event.get('slots')} crossings={event.get('crossings')}")
        elif kind == "plan_round":
            print(f"{step}. plan round={event.get('round')} conflicts={event.get('conflicts')}")
        elif kind == "tool_call":
            clue = event.get("clue")
            slot = event.get("slot")
            pattern = event.get("pattern")
            reason = event.get("reason")
            print(f"{step}. solve {slot} pattern={pattern} reason={reason} clue={clue!r}")
        elif kind == "tool_result":
            candidates = event.get("candidates", [])
            preview = ", ".join(f"{item.get('answer')}:{float(item.get('confidence', 0)):.2f}" for item in candidates[:3])
            print(f"{step}. candidates {event.get('slot')} [{preview}]")
        elif kind == "verify_solution":
            print(
                f"{step}. verify complete={event.get('complete')} accepted={event.get('accepted')} "
                f"repairs={event.get('recommended_repairs')}"
            )
        elif kind == "stop":
            print(f"{step}. stop reason={event.get('reason')}")

    if final:
        print()
        print("Final Grid")
        for row in final.get("grid", []):
            print(" ".join(row))
        print(f"complete={final.get('complete')}")

    if metrics:
        print()
        print("Metrics")
        print(f"llm_calls={metrics.get('llm_calls')}")
        print(f"estimated_cost_usd={metrics.get('estimated_cost_usd')}")
        print(f"wall_time_seconds={metrics.get('wall_time_seconds'):.3f}")


if __name__ == "__main__":
    main()
