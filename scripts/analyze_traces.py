#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze agent traces and propose human-approved improvements.")
    parser.add_argument("runs_dir", nargs="?", default="runs")
    args = parser.parse_args()

    events = load_events(Path(args.runs_dir))

    if not events:
        print(json.dumps({"runs": 0, "recommendations": ["No traces found. Run scripts/solve.py first."]}, indent=2))
        return

    print(json.dumps(analyze_events(events), indent=2, sort_keys=True))


def load_events(runs_dir: Path) -> list[dict]:
    runs = sorted(runs_dir.glob("*/trace.jsonl"))
    events = []
    for path in runs:
        with path.open() as fh:
            for line in fh:
                record = json.loads(line)
                record["_run"] = str(path.parent)
                events.append(record)
    return events


def analyze_events(events: list[dict]) -> dict:
    tool_calls = Counter(event.get("tool") for event in events if event.get("event") == "tool_call")
    repair_reasons = Counter(event.get("reason") for event in events if event.get("event") == "tool_call")
    low_confidence = Counter()
    incomplete_runs = set()
    issues_by_run: dict[str, list[str]] = defaultdict(list)
    slot_metadata: dict[str, dict] = {}
    slot_candidate_counts: dict[str, list[int]] = defaultdict(list)
    slot_top_confidences: dict[str, list[float]] = defaultdict(list)
    slot_top_margins: dict[str, list[float]] = defaultdict(list)
    empty_candidate_slots = Counter()
    single_candidate_slots = Counter()
    low_margin_slots = Counter()
    low_margin_values: dict[str, list[float]] = defaultdict(list)
    source_counts = Counter()
    run_puzzle_ids: dict[str, str] = {}

    for event in events:
        if event.get("event") == "observe_puzzle":
            run_puzzle_ids[event["_run"]] = event.get("puzzle_id") or event["_run"]
        if event.get("event") == "tool_call":
            slot = event.get("slot")
            if slot:
                key = slot_key(event, run_puzzle_ids)
                existing = slot_metadata.get(key, {"slot": slot, "puzzle_id": run_puzzle_ids.get(event["_run"])})
                slot_metadata[key] = merge_metadata(
                    existing,
                    {
                        "slot": slot,
                        "puzzle_id": run_puzzle_ids.get(event["_run"]),
                        "clue": event.get("clue"),
                        "direction": event.get("direction"),
                        "length": event.get("length"),
                        "last_pattern": event.get("pattern"),
                    },
                )
        if event.get("event") != "tool_result":
            continue
        slot = event.get("slot")
        candidates = event.get("candidates", [])
        if not slot:
            continue
        key = slot_key(event, run_puzzle_ids)
        slot_candidate_counts[key].append(len(candidates))
        if not candidates:
            empty_candidate_slots[key] += 1
            continue
        source_counts.update(candidate.get("source", "unknown") for candidate in candidates)
        confidences = [float(candidate.get("confidence", 0.0)) for candidate in candidates]
        slot_top_confidences[key].append(confidences[0])
        if len(confidences) == 1:
            single_candidate_slots[key] += 1
            slot_top_margins[key].append(confidences[0])
        else:
            margin = confidences[0] - confidences[1]
            slot_top_margins[key].append(margin)
            if margin < 0.15:
                low_margin_slots[key] += 1
                low_margin_values[key].append(margin)

    for event in events:
        if event.get("event") != "verify_solution":
            continue
        if not event.get("complete"):
            incomplete_runs.add(event["_run"])
        for slot_id in event.get("low_confidence_slots", []):
            low_confidence[slot_key({"_run": event["_run"], "slot": slot_id}, run_puzzle_ids)] += 1
        issues_by_run[event["_run"]].extend(event.get("issues", []))

    prompt_recommendations = build_prompt_recommendations(
        slot_metadata,
        slot_candidate_counts,
        slot_top_confidences,
        slot_top_margins,
        low_margin_values,
        empty_candidate_slots,
        single_candidate_slots,
        low_margin_slots,
        low_confidence,
    )
    policy_recommendations = build_policy_recommendations(
        repair_reasons,
        incomplete_runs,
        issues_by_run,
        low_confidence,
        low_margin_slots,
    )
    evaluation_recommendations = build_evaluation_recommendations(events, incomplete_runs)
    recommendations = prompt_recommendations + policy_recommendations + evaluation_recommendations
    if low_confidence:
        recommendations.append("Review low-confidence slots before changing solver policy.")
    if repair_reasons.get("repair_conflict", 0):
        recommendations.append("Inspect conflict repairs; consider prioritizing high-degree crossing slots earlier.")
    if incomplete_runs:
        recommendations.append("Run eval before changing policy; accept only changes that improve word/full-puzzle accuracy.")
    if not recommendations:
        recommendations.append("Current traces show clean solves. Add harder puzzles before optimizing prompt or policy.")

    slot_diagnostics = {}
    for key, counts in slot_candidate_counts.items():
        slot_diagnostics[key] = {
            **slot_metadata.get(key, {"slot": key}),
            "calls": len(counts),
            "avg_candidates": round(mean(counts), 2),
            "avg_top_confidence": round(mean(slot_top_confidences[key]), 3) if slot_top_confidences.get(key) else None,
            "avg_top_margin": round(mean(slot_top_margins[key]), 3) if slot_top_margins.get(key) else None,
            "avg_low_margin": round(mean(low_margin_values[key]), 3) if low_margin_values.get(key) else None,
            "empty_candidate_calls": empty_candidate_slots[key],
            "single_candidate_calls": single_candidate_slots[key],
            "low_margin_calls": low_margin_slots[key],
            "low_confidence_verifications": low_confidence[key],
        }

    return {
        "runs": len({event["_run"] for event in events}),
        "events": len(events),
        "tool_calls": dict(tool_calls),
        "repair_reasons": dict(repair_reasons),
        "candidate_sources": dict(source_counts),
        "slot_diagnostics": slot_diagnostics,
        "low_confidence_slots": dict(low_confidence),
        "incomplete_runs": sorted(incomplete_runs),
        "issues_by_run": {run: issues for run, issues in issues_by_run.items() if issues},
        "prompt_recommendations": prompt_recommendations,
        "policy_recommendations": policy_recommendations,
        "evaluation_recommendations": evaluation_recommendations,
        "recommendations": recommendations,
    }


def build_prompt_recommendations(
    slot_metadata: dict[str, dict],
    slot_candidate_counts: dict[str, list[int]],
    slot_top_confidences: dict[str, list[float]],
    slot_top_margins: dict[str, list[float]],
    low_margin_values: dict[str, list[float]],
    empty_candidate_slots: Counter,
    single_candidate_slots: Counter,
    low_margin_slots: Counter,
    low_confidence: Counter,
) -> list[str]:
    recommendations: list[str] = []
    for slot, count in empty_candidate_slots.most_common(5):
        recommendations.append(f"Prompt: slot {describe_slot(slot, slot_metadata)} returned no candidates {count} time(s); add examples for respecting length/pattern and require at least 3 plausible alternatives.")
    for slot, count in single_candidate_slots.most_common(5):
        avg_candidates = mean(slot_candidate_counts[slot])
        if avg_candidates <= 1.5:
            recommendations.append(f"Prompt: slot {describe_slot(slot, slot_metadata)} averaged {avg_candidates:.1f} candidate(s); increase candidate_count or ask for synonyms, abbreviations, and tense variants.")
    for slot, count in low_margin_slots.most_common(5):
        avg_margin = mean(low_margin_values.get(slot, slot_top_margins[slot]))
        recommendations.append(f"Prompt: slot {describe_slot(slot, slot_metadata)} has low top-candidate margin ({avg_margin:.2f}) in {count} call(s); ask the model to calibrate confidence and explain why the top answer beats close alternatives.")
    for slot, count in low_confidence.most_common(5):
        avg_conf = mean(slot_top_confidences.get(slot, [0.0]))
        recommendations.append(f"Prompt: slot {describe_slot(slot, slot_metadata)} was low-confidence during verification {count} time(s), avg top confidence {avg_conf:.2f}; re-query with crossing letters earlier.")
    return dedupe(recommendations)


def build_policy_recommendations(
    repair_reasons: Counter,
    incomplete_runs: set,
    issues_by_run: dict[str, list[str]],
    low_confidence: Counter,
    low_margin_slots: Counter,
) -> list[str]:
    recommendations: list[str] = []
    if repair_reasons.get("repair_conflict", 0):
        recommendations.append("Policy: conflict repairs occurred; prioritize slots with the most crossings and lowest selected confidence before broad re-querying.")
    if low_confidence:
        recommendations.append("Policy: lower-confidence accepted answers should remain tentative until supported by at least one crossing or a second candidate-generation pass.")
    if low_margin_slots:
        recommendations.append("Policy: when top-two candidate confidence margin is below 0.15, defer commitment and let crossings decide instead of trusting rank order.")
    if incomplete_runs:
        recommendations.append("Policy: incomplete runs found; raise max_rounds by one only after checking whether failures are candidate-generation failures or solver pruning failures.")
    if any(issues_by_run.values()):
        recommendations.append("Policy: validator issues found; add failing assignments to a regression fixture before changing prompts.")
    return dedupe(recommendations)


def build_evaluation_recommendations(events: list[dict], incomplete_runs: set) -> list[str]:
    runs = {event["_run"] for event in events}
    recommendations: list[str] = []
    if len(runs) < 10:
        recommendations.append(f"Eval: only {len(runs)} run(s) analyzed; collect at least 10-20 held-out puzzles before treating trace trends as stable.")
    if not incomplete_runs:
        recommendations.append("Eval: current traces are all complete; add harder puzzles with black squares, abbreviations, and ambiguous clues before optimizing further.")
    recommendations.append("Eval gate: accept prompt/policy changes only if word accuracy, full-puzzle accuracy, and average tool calls do not regress versus baseline.")
    return recommendations


def describe_slot(slot: str, metadata: dict[str, dict]) -> str:
    item = metadata.get(slot, {})
    clue = item.get("clue")
    length = item.get("length")
    pattern = item.get("last_pattern")
    if clue:
        return f"{slot} ({length} letters, pattern {pattern}, clue: {clue!r})"
    return slot


def slot_key(event: dict, run_puzzle_ids: dict[str, str]) -> str:
    run = event.get("_run", "")
    puzzle_id = run_puzzle_ids.get(run) or Path(run).name
    return f"{puzzle_id}:{event.get('slot')}"


def merge_metadata(existing: dict, incoming: dict) -> dict:
    merged = dict(existing)
    for key, value in incoming.items():
        if value is not None:
            merged[key] = value
    return merged


def dedupe(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


if __name__ == "__main__":
    main()
