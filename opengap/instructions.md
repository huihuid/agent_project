# Instructions

When solving a puzzle:

1. Parse the puzzle into slots, clues, lengths, and crossings.
2. For each unresolved slot, call `solve_clue` with the clue, length, and known
   pattern.
3. Validate candidate answers before using them.
4. Use `solve_constraints` to search for a crossing-consistent assignment.
5. Use `validate_grid` before accepting a solution.
6. If conflicts or low-confidence answers remain, repair the most constrained or
   least confident slots first.
7. Stop when the puzzle is complete, the round budget is exhausted, or the cost
   budget is exceeded.
8. Report the final grid, unresolved slots if any, and run metrics.

Policy:

- Never commit an answer that violates length or known-pattern constraints.
- Never treat LLM output as authoritative without validation.
- Prefer fewer, clearer tool calls when the grid already provides enough
  information.
- Use traces as the source of truth for debugging.
- Accept prompt or policy changes only after evaluation does not regress.
