# Event transition model

Supported events are open, close, lock, unlock, give, take, move, put, and remove. Events compile into deterministic preconditions, effects, and temporal supersession patterns.

- Open/close update signed `open` state.
- Lock/unlock update signed `locked` state.
- Give requires current ownership, supersedes current owners, removes giver ownership, and adds recipient ownership.
- Move supersedes the actor's current location.
- Put supersedes current containment; remove adds signed negative containment evidence.

The verifier checks event preconditions before approving effects. Only approved effect semantic IDs commit. Receipts retain the event, prior and resulting hashes, effects, superseded IDs, and provenance. Repeating an equivalent effect merges observations rather than duplicating state.
