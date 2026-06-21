# Semantic merge and cluster activation

Stable semantic IDs hash normalized kind, subject, predicate, object, polarity, and rule operands. Turn numbers and surface provenance are excluded. Repeated observations therefore update one ledger item with first/last turn, count, and every observation provenance ID.

Questions never enter persistent state. Rejected and unresolved staged items never commit.

For a query, exact subject, predicate, object, and goal tokens seed activation. A deterministic breadth-first traversal follows proposition keys, rule antecedents/consequents, shared entities, containment, ownership, locations, compatibility, and event effects to depth four. Ordering is lexical. The receipt lists seeds, activation edges, activated IDs, dormant IDs, the bound, and truncation.

Only activated persistent facts and rules enter the Habitat portion of `ReasoningRequest`. Dormant clusters remain inspectable in memory but cannot appear in verifier supports.
