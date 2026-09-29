# Agent Policy

The agent follows these rules:

- Treat clue tool outputs as candidates, not facts.
- Reject candidates that violate length or known-pattern constraints.
- Commit assignments only when the constraint solver finds crossing consistency.
- Prefer repairing slots involved in conflicts or missing candidates.
- Stop when the puzzle is complete, the round budget is exhausted, or the cost budget is exceeded.
- Return the best partial solution if no complete solution is found.

The policy is intentionally conservative because enterprise agents should be debuggable and bounded.
