from scripts.analyze_traces import analyze_events


def test_trace_analyzer_emits_specific_prompt_and_policy_recommendations():
    events = [
        {
            "_run": "runs/demo",
            "event": "tool_call",
            "tool": "solve_clue",
            "slot": "A1",
            "direction": "across",
            "length": 3,
            "clue": "Feline pet",
            "pattern": "C__",
            "reason": "no_candidates",
        },
        {
            "_run": "runs/demo",
            "event": "tool_result",
            "tool": "solve_clue",
            "slot": "A1",
            "candidates": [
                {"answer": "CAR", "confidence": 0.51, "rationale": "near miss", "source": "llm"},
                {"answer": "CAT", "confidence": 0.5, "rationale": "feline", "source": "llm"},
            ],
        },
        {
            "_run": "runs/demo",
            "event": "verify_solution",
            "complete": False,
            "issues": ["A1: expected length 3, got 2"],
            "low_confidence_slots": ["A1"],
            "recommended_repairs": ["A1"],
        },
    ]

    report = analyze_events(events)

    assert report["prompt_recommendations"]
    assert report["policy_recommendations"]
    assert report["evaluation_recommendations"]
    assert "demo:A1" in report["slot_diagnostics"]
