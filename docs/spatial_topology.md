# Explicit spatial topology

Connections have stable identity, endpoints, `bidirectional` or `directed` direction, signed evidence, status, conditions, blockers, positive cost, support and provenance. Status is `OPEN`, `BLOCKED`, `LOCKED`, `UNKNOWN`, or `CONFLICTED`. Conflicting active status evidence resolves to `CONFLICTED` and is not traversable.

Only declared edges exist. Routing is stable, cycle-safe bounded BFS. Neighbours sort by location then connection ID. A move requires supported actor location, an existing destination, correct direction, `OPEN` status, satisfied required conditions and no blocking condition. Connection IDs/support participate in action authorization, cluster activation, world hashes and receipts.

Supported grammar includes ordinary, negated, named, directed, passage and route-status declarations. Duplicate declarations merge evidence and provenance rather than adding edges.
