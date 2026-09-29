# One-Minute Demo Script

0-10s: Show the puzzle JSON and explain that the agent receives grid structure plus clues.

10-25s: Run:

```bash
python scripts/solve.py data/puzzles/mini_001.json --mock
```

25-40s: Open the generated `runs/.../trace.jsonl` and show the observe-plan-tool-verify steps.

40-55s: Run evaluation:

```bash
python scripts/evaluate.py --puzzles data/eval --gold data/gold --method agent --mock
```

55-60s: Summarize: LLM/tooling proposes answers, constraints verify them, trace/eval make the agent measurable.
