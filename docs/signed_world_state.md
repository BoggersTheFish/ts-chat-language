# Signed world state

Facts use a canonical proposition key `(subject, predicate, object)` and separate positive and negative semantic items.

| State | Meaning |
|---|---|
| `SUPPORTED_TRUE` | Active positive support and no active negative support |
| `SUPPORTED_FALSE` | Active negative support and no active positive support |
| `CONFLICTED` | Both polarities have active support |
| `UNKNOWN` | Neither polarity has activated support |

Absence is never negative evidence. `CONFLICTED` and `UNKNOWN` cannot produce affirmative rendering. Ordinary contradictory premises remain active and provenance-linked; neither overwrites the other. Explicit verified events may supersede prior temporal evidence while retaining inactive ledger history.

Bounded negation covers `X is not Y`, supported state adjectives, `X does not own Y`, `X is no longer open`, and signed state questions. Other negation repairs or rejects conservatively.
