# Replanning and stale plans

Verified plans contain origin world and cluster hashes, goal, action sequence, support, limits, intermediate hashes, explored-state count and verification ID. Each action is revalidated against current signed state and topology.

Typed causes are `WORLD_CHANGED`, `PRECONDITION_LOST`, `ROUTE_BLOCKED`, `OBJECT_MOVED`, `OWNERSHIP_CHANGED`, `GOAL_CHANGED`, `CONFLICT_INTRODUCED`, `ACTION_EFFECT_MISMATCH`, and `AGENT_INTERFERENCE`.

Invalidation preserves completed action and transaction receipts, discards remaining executable actions, retains current verified world, raises stale-plan tension, reflects, reactivates the cluster and builds a fresh plan. Replan, plan-per-goal, action, state, iteration and wall-clock budgets prevent loops. Budget exhaustion is distinct from success and unreachable proof.
