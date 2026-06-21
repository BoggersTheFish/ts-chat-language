# Verified symbolic action execution

The in-process `EnvironmentAdapter` supports observation, one authorized action, event injection, snapshot and deterministic restore. It performs no shell, network, external filesystem or real-world action.

The lifecycle is `ACTION_PROPOSED → PRECONDITIONS_VERIFIED → ACTION_AUTHORIZED → ENVIRONMENT_EXECUTED → EFFECTS_OBSERVED → EFFECTS_VERIFIED → WORLD_COMMITTED`. Failures use `ACTION_REJECTED`, `ACTION_FAILED`, `EFFECT_MISMATCH`, and `REPLAN_REQUIRED`.

Supported closed action schemas are move, take, put, give, open, close, lock, unlock, activate and deactivate. Schema validation checks required fields and effect shape. Signed preconditions, topology and permission are checked immediately before execution. Transactions record action, pre/post trusted hashes, expected/observed effects, verification, support and provenance. A mismatch can update trusted state only from a separately verified observation; expected effects are never committed.
