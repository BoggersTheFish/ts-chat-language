# Persistent verified goals

Goals use stable IDs and store owner, state predicate, desired polarity, status, priority, creation/update turns, dependencies, provenance and resolution support. Statuses are `PROPOSED`, `ACTIVE`, `SATISFIED`, `BLOCKED`, `UNREACHABLE`, `PAUSED`, `ABANDONED`, `BUDGET_EXHAUSTED`, and `CONFLICTED`.

The verifier checks creation, activation, status transition, abandonment and priority changes. `SATISFIED` requires the desired polarity in current signed state and copies its semantic support IDs. Plans and expected effects cannot satisfy goals.

Selection is deterministic: priority descending, tension descending, creation turn, then goal ID. Multi-agent scheduling first applies goal priority, tension and agent ID. Opposed active goals over one proposition are preserved and marked conflicted; no global truth preference is invented.
