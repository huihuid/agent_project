# Evaluation Methodology

The agent is evaluated at three levels:

- **Cell accuracy:** percentage of answer letters that match the gold solution.
- **Word accuracy:** percentage of clue answers that exactly match the gold answer.
- **Full-puzzle accuracy:** percentage of puzzles solved perfectly.

Operational metrics are also recorded:

- LLM/tool calls
- Wall-clock runtime
- Estimated cost
- Repair rounds
- Completion status

Recommended comparisons:

- **Direct baseline:** one-pass LLM-style solve with no crossing repair.
- **Independent clue baseline:** solve each clue independently and ignore global consistency.
- **Agentic solver:** clue tools plus crossing constraints plus repair loop.

This separates language reasoning quality from agent orchestration quality.
