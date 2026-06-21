# Deterministic tension control system

Fixed raw contributions are: unsatisfied goal `0.50`, blocked goal `0.30`, failed action `0.40`, missing precondition `0.20`, conflicted required state `0.35`, unexpected change `0.30`, stale plan `0.25`, unreachable route `0.30`, competing goal `0.20`, ambiguous world `0.20`, repeated repair `0.15`, and budget pressure `0.20`.

Propagation is bounded BFS with default depth 3, decay 0.5, stable ordering, best duplicate-path merge and total clamp 1.0. Every propagated contribution has a receipt. Resolved sources retain their prior record in history and become `RELAXED` with zero value.

Compute tiers are LOW (`cluster 2`, `plan 4`, `128 states`) below 0.40; MEDIUM (`4`, `8`, `512`) below 0.75; and HIGH (`6`, `12`, `2048`) otherwise. Runtime limits may lower these caps. Tension IDs are forbidden from action/claim support and never mutate state.
