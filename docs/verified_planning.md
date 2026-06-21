# Verified planning

Habitat planning uses deterministic bounded breadth-first search with lexical action ordering, an eight-step depth limit, a 512-state limit, and cycle detection.

The initial action vocabulary is move, take, unlock, and open. Move operates over declared Habitat places using the documented open-topology mode; when explicit connection constraints are later supplied they must be checked. Take requires actor/object co-location through declared containment and container location. Unlock requires a locked target, a carried compatible key, and a declared `unlocks` relation. Open requires the target to be unlocked and the actor to be at the target.

Every accepted step contains passed precondition checks, declared effects, non-empty support IDs, and a resulting state hash. `PLAN_VERIFIED` is emitted only when the final state satisfies the explicit goal. Otherwise the outcome is `REJECT_UNREACHABLE`; missing or ambiguous language may instead request repair.

The planner does not persist simulated plan effects into trusted world memory.
