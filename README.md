# Crossword Agent

An agentic crossword solver for a Forward Deployed Engineer take-home assignment.

The project treats crossword solving as an agent workflow:

1. Observe the puzzle structure and crossings.
2. Plan which clues need tool calls.
3. Generate clue candidates with an LLM or deterministic mock tool.
4. Use a constraint solver to verify crossing consistency.
5. Repair low-confidence or conflicting entries.
6. Emit trace logs, metrics, and a final solution.

The LLM is treated as a proposal engine, not as ground truth. Hard grid constraints and validators decide what can be committed.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/solve.py data/puzzles/mini_001.json --mock
```

## Reviewer Quick Demo

```bash
python scripts/solve.py data/puzzles/mini_004.json --mock
python scripts/evaluate.py --puzzles data/eval --gold data/gold --method agent --mock
python scripts/evaluate.py --puzzles data/eval --gold data/gold --method independent --mock
python scripts/summarize_run.py runs/<latest_run_dir>
```

Run evaluation:

```bash
python scripts/evaluate.py --puzzles data/eval --gold data/gold --method agent --mock
python scripts/evaluate.py --puzzles data/eval --gold data/gold --method independent --mock
```

Every agent run writes:

```text
runs/<timestamp>_<puzzle_id>/
  trace.jsonl
  final_solution.json
  metrics.json
```

## Real LLM Mode

Set an API key, then pass `--real`.

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY
set -a
source .env
set +a
python scripts/solve.py data/puzzles/mini_001.json --real --model gpt-4.1-mini
python scripts/evaluate.py --puzzles data/eval --gold data/gold --method agent --real
```

## Repository Layout

```text
src/crossword_agent/
  agent/         observe-plan-act-verify loop, planner, trace logger
  tools/         clue solver, constraint solver, validator, conflict detector
  domain/        puzzle models, parser, renderer
  evaluation/    cell/word/full-puzzle metrics
  baselines/     comparison methods
opengap/         OpenGAP-compatible agent description
data/            demo puzzles and gold answers
docs/            evaluation and demo notes
tests/           parser, solver, and metrics tests
```

## Puzzle Format

Puzzles are JSON files with explicit slots:

```json
{
  "id": "mini_001",
  "grid": ["...", "...", "..."],
  "slots": [
    {"id": "A1", "direction": "across", "row": 0, "col": 0, "length": 3, "clue": "Feline pet"}
  ]
}
```

Explicit slots keep the MVP reliable. A production version could add importers for `.puz`, AmuseLabs, or other crossword formats.

## Design Decisions

- **Agent first:** the solver is one tool in an observe-plan-act-verify loop.
- **Typed tool contracts:** tools accept structured inputs and return structured candidates/results.
- **Strict structured outputs:** real LLM mode requests a strict JSON schema and validates it locally.
- **Constraint validation:** answers must match length, pattern, and crossing constraints.
- **Traceability:** every run produces JSONL logs suitable for debugging and audit.
- **Evaluation harness:** quality is measured with cell accuracy, word accuracy, full-puzzle solve rate, cost, latency, and tool calls.
- **Mock mode:** reviewers can run the project without external credentials.

For the deeper interview-oriented design writeup, see
[`docs/design_discussion.md`](docs/design_discussion.md).
For a concise reviewer-facing summary, see [`SUBMISSION.md`](SUBMISSION.md).

Analyze traces for bounded improvement suggestions:

```bash
python scripts/analyze_traces.py runs
```

The analyzer reports prompt, policy, and evaluation-gating recommendations from
the run traces.

## Trade-offs

- The demo dataset is intentionally small and deterministic. This makes the agent architecture easy to inspect, but it is not a benchmark of real crossword difficulty.
- The current solver uses beam search over generated candidates. It is simple and explainable, but larger puzzles would benefit from richer candidate generation and pruning.
- OpenGAP is used as an agent-definition layer, while Python remains the source of truth for execution so the project can run without a framework dependency.
