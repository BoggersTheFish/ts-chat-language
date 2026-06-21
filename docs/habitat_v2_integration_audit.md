# Habitat v2 integration audit

## Baseline lock

Audit date: 2026-06-21.

| Repository | Branch before work | Starting commit | Baseline |
|---|---|---|---|
| `TS-Reasoner-v0` | `main` | `182cd2dc0d5ce2bfc413d6082def1901222d596d` | 600 tests passed in 14.887 s |
| `ts-chat-language` | `master` | `a67c78885a29f11aafe4a219ca3797f1fa00803f` | 82 tests passed in 0.085 s |

The canonical v1 evaluation passed 30/30 with zero unsupported accepts, contamination, replay failures, renderer violations, or receipt failures. The frozen 165-case challenge passed with zero unsupported accepts, contamination, or execution errors. Both working trees were clean before the audit. Habitat work uses additive `habitat-v2` branches.

## Current component map

```text
text
  -> ts_vertical_slice.parser.parse_to_meaning_graph
  -> ts_lang.meaning_graph.MeaningGraph
  -> ts_vertical_slice.bridge.bridge_meaning_graph
  -> ts_reasoner.structured_request.ReasoningRequest
  -> StructuredRequestVerifier.verify
  -> ts_vertical_slice.renderer.render_verified
  -> TurnReceipt + VerifiedState
```

The parser creates deterministic node IDs from node kind, rule, and slots. `MeaningGraph` validates provenance and graph references. The bridge translates graph nodes into immutable Reasoner dataclasses. The Reasoner is the only authority that returns affirmative support IDs. The renderer asserts that every affirmative answer has support IDs present in the request. The session commits only accepted or deterministically repaired premises.

## Existing identity, memory, polarity, and projection

- Vertical-slice node identity is stable for equivalent slots, but its provenance ID is also the semantic node ID. Repeated observations therefore collapse too early and cannot retain observation-level provenance.
- `VerifiedState` stores flat lists of `StructuredRelation`, `StructuredClaim`, and `StructuredConstraint`. Deduplication uses the graph node ID, not an explicit semantic memory record.
- Every request currently receives all stored relations, claims, and constraints. There is no query-relevance projection.
- `StructuredRelation` and `StructuredClaim` already carry `positive` or `negative` polarity. The v1 parser blocks negation, and the verifier rejects simultaneous positive and negative facts as a generic contradiction.
- Repeated questions are not committed because only graph nodes matching fact/claim/constraint types enter memory.
- Boolean derivation is query-local and verifier-owned. Its loop has no explicit depth or fact-count bounds.
- The existing planning path verifies only explicit `before` constraints. It is not action search.

## Exact extension points

1. Add Habitat dataclasses and algorithms inside `TS-Reasoner-v0`, beside `structured_request.py`. These own four-valued projection, bounded causal closure, event transition validation, and bounded action planning.
2. Add a semantic world-memory module inside `ts-chat-language`. It owns stable semantic keys, observation provenance, active/superseded temporal items, and deterministic merge receipts.
3. Extend the existing bounded parser with explicit Habitat node kinds. Do not route Habitat turns through legacy TSLC rendering.
4. Insert cluster activation between semantic merge and bridge projection. Query seeds traverse exact entity, predicate, antecedent, effect, possession, containment, compatibility, and action-precondition edges with fixed depth and ordering.
5. Extend `ReasoningRequest` additively with Habitat fields. Existing positional construction and v1 fields remain valid.
6. Extend `VerifierDecision` and `StructuredAnswer` additively with decision subtype, signed state, derivations, transitions, and plan receipt.
7. Extend `TurnReceipt` additively and set `receipt_schema` to `ts-turn-receipt-v2` for Habitat sessions while preserving v1 fixture files.
8. Extend the current CLI with Habitat inspection commands; do not create a second application.

## Semantic migration strategy

The authoritative persistent substrate becomes a keyed semantic ledger. Each item has a stable key derived only from kind, subject, predicate, object, polarity, and rule/action operands. Observations retain turn-local provenance IDs. Equivalent observations merge counts and provenance. Opposite polarities remain separate ledger items and project into one four-valued proposition state. Explicit verified transition effects supersede prior temporal state; ordinary assertions never silently overwrite evidence.

For compatibility, the session exposes projected `relations`, `claims`, and `constraints` to the existing bridge and tests. Habitat queries instead project only their activated cluster. V1 single-turn behavior remains unchanged.

## Query-relevance location

Relevance is computed after parsing and merge, before `ReasoningRequest` construction. The query goal seeds exact semantic tokens. Traversal walks constraint antecedents/consequents, event effects, action preconditions/effects, entity co-reference, containment, location, ownership, and key compatibility. The activation receipt records every inclusion reason, dormant ID, bound, and truncation flag. The Reasoner sees only activated persistent items plus current-turn query structure.

## Planning authority boundary

The language layer may identify a planning goal and declared world/action structures. Only the Reasoner planner may search. Every emitted step includes verifier-approved precondition checks, declared effects, support IDs, and resulting state hash. The renderer consumes only a `PLAN_VERIFIED` answer. Missing preconditions produce repair or rejection; no renderer or parser may synthesize a plan step.

## Bypass risks and controls

| Risk | Control |
|---|---|
| Raw input copied into an affirmative answer | Habitat renderer accepts only structured answers and validates every support ID against request or verifier-produced derivation IDs. |
| Whole-memory leakage | The request stores activation metadata and asserts persistent IDs are a subset of the activated set. |
| Rejected/ambiguous input merged before verification | Merge is staged; only verifier-approved assertion/event/action IDs commit. Query-only and rejected structures never commit. |
| Contradiction overwritten | Opposite evidence is retained; projection returns `CONFLICTED`; ordinary assertion order has no overwrite authority. |
| Event bypasses preconditions | Transition engine emits no effect unless all declared checks pass. Session commits only approved effects. |
| Planner invents movement, keys, or actions | Fixed action schemas, deterministic BFS, explicit world facts, bounded depth, and per-step support validation. |
| Derived facts become trusted premises | Causal closure is query-local unless an explicit persistence policy is added later. |
| Legacy renderer called by Habitat path | Habitat session continues to call the verifier-gated renderer; tests monkeypatch/construct unsupported answers and require assertion failure. |
| Support duplication after semantic merge | Support IDs are semantic IDs, canonicalized and deduplicated before decisions and receipts. |
| Unbounded causal or planning work | Fixed depth, fact, state, and agenda limits plus cycle detection and deterministic ordering. |

## Behaviours that must remain unchanged

- The five v1 reasoning families and exact canonical outputs.
- Public `ACCEPT`, `REPAIR`, and `REJECT` categories.
- Existing `ReasoningRequest` construction and JSON serialization.
- Existing receipt fixtures and replay hashes when the v1 path is used.
- Rejected and unresolved turns do not mutate memory.
- Renderer support assertion remains mandatory.
- No external model, knowledge source, randomness, or network dependency.

## Expected additive schema changes

- Reasoner: `WorldFact`, `WorldEvent`, `ActionSchema`, `ActionInstance`, `SignedProposition`, `CausalDerivation`, `StateTransition`, `PlanReceipt`; optional Habitat tuples and bounds on `ReasoningRequest`; subtype and Habitat results on `VerifierDecision`.
- TSLC: `SemanticItem`, `SemanticObservation`, `SemanticMemory`, `ClusterActivation`; Habitat sections on `TurnReceipt`; schema version.
- Existing dataclass fields are not removed or reordered before defaults.

## Test plan

- Unit tests: semantic IDs, observation merge, signed projection, conflict preservation, activation traversal, transition supersession, causal limits, planner preconditions/effects, renderer enforcement, receipt serialization.
- Integration tests: each required signed-state, transfer, containment, causal, planning, dormant-cluster, replay, and contamination scenario through text-to-receipt.
- Frozen Habitat corpus: at least 20 cases in each of six required categories.
- Frozen adversarial corpus: at least 100 cases spanning all specified attacks; preserve the initial generated baseline before fixes.
- Regression: unchanged 600 Reasoner tests, 82+ TSLC tests, canonical 30 cases, frozen 165-case challenge, and v1 fixtures.
- Website: build, lint, stable source/evidence links, and cache-busted production HTML verification.

## Explicit non-goals

- General conversation, broad natural-language negation, probabilistic parsing, learned retrieval, embeddings, or external knowledge.
- Real-world truth certification of user premises.
- Physics simulation, unrestricted temporal logic, arbitrary quantification, shared ownership, arbitrary containment inference, optimal planning, or plans outside declared Habitat action schemas.
- Biological or animal-brain equivalence.
- Replacing MeaningGraph, ReasoningRequest, verifier authority, support-checked rendering, or deterministic receipts.
