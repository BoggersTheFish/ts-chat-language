# Habitat v3 agent-loop integration audit

## Scope and frozen baseline

This audit describes the additive path from the compatible Habitat v2 checkpoints (`TS-Reasoner-v0` `68c77c63f93d0bc5a39d0924a1038b72f687446a`, `ts-chat-language` `c7863c25831da0183bc7c19ecb299c177a769844`) to Habitat v3. The v1/v2 parser, verifier, receipts, fixtures, and evaluations remain historical compatibility surfaces. Habitat v3 uses new modules and `ts-turn-receipt-v3`; it does not reinterpret v2 receipts.

## Exact component map and decision ownership

| Component | Current path | Current responsibility | v3 owner / authority |
|---|---|---|---|
| MeaningGraph schema | `ts_lang/meaning_graph.py` | Stable nodes, edges, provenance and validation | Parser proposes nodes; graph validation only validates structure |
| Bounded parser | `ts_vertical_slice/parser.py` | Regex grammar to MeaningGraph | Proposes topology, goals, events and commands; never authorizes |
| Semantic ledger | `ts_vertical_slice/habitat.py` | Semantic identity, provenance merge, activation and v2 commit | v2 preserved; v3 world store commits verifier-approved transactions only |
| Signed projection | `ts_reasoner/habitat.py` | Four-valued projection and causal closure | Verifier-owned truth projection |
| Cluster activation | `ts_vertical_slice/habitat.py:activate` | Bounded shared-token BFS | v3 activation adds topology/goal seeds and tension-selected bounded depth; no proof authority |
| Planner | `ts_reasoner/habitat.py:_plan` | Bounded BFS over symbolic action effects | v3 planner proposes complete plans against an immutable snapshot |
| Action schemas | `ts_reasoner/habitat.py:HABITAT_ACTION_SCHEMAS` | Five v2 schema contracts | v3 extends to ten closed, typed schemas; verifier checks every instantiated step |
| Verifier request | `ts_reasoner/structured_request.py:ReasoningRequest` | Typed bridge payload | v2 unchanged; v3 uses explicit verification records at goal, plan, action and effect gates |
| Verifier response | `ts_reasoner/structured_request.py:VerifierDecision` | Sole affirmative answer authority | v3 verifier is sole authority for goal lifecycle, plans, actions, effects, commits and lessons |
| Renderer gate | `ts_vertical_slice/renderer.py:render_verified` | Rejects affirmative output without known support | v3 renderer requires verified final-state support for success and exposes conflict/budget outcomes |
| Turn receipt | `ts_vertical_slice/receipt.py` | `ts-turn-receipt-v2` and turn replay hash | New v3 schema records the complete loop and run replay hash |
| Session state | `ts_vertical_slice/session.py` | In-memory relations, claims, constraints and semantic memory | New agent session owns environment, world, goals, tension, plans, lessons and run log |
| CLI | `ts_vertical_slice/chat.py` | Turn handling and v2 inspection | Explicit non-recursive `/step` and bounded `/run` controls |
| Evaluations | `ts_vertical_slice/evaluation.py`, `challenge.py`, `habitat_evaluation.py` | 30, 165, 120 and 102 frozen cases | Unchanged regressions plus frozen v3 functional/adversarial corpora |

Decision ownership is strict: parsing, merging, tension, activation, planning, reflection and rendering propose or present structures. `HabitatV3Verifier` alone approves trusted observations, goals and status changes, plan steps, action authorization, observed effects, transactional commits, and lesson approval.

## Current mutation pathways

1. `VerticalSliceSession.handle` stages graph nodes in `SemanticMemory.stage`.
2. `verify_reasoning_request` selects `approved_memory_ids`.
3. `SemanticMemory.commit` merges approved items, deactivates event-superseded items and updates statuses.
4. `_commit_current` mutates legacy relation/claim/constraint lists for non-Habitat turns.
5. `reset` replaces the complete in-memory state.

Habitat v3 does not call these paths for executed actions. Its environment owns untrusted physical state. A world transaction is built from an authorized action plus a subsequent observation, verified, then atomically installed with pre/post hashes. No plan writes world state.

## Planner/executor separation

The planner receives a canonical immutable snapshot and returns a plan containing origin world hash, relevant-cluster hash, goal, bounds, action proposals, required supports and expected intermediate hashes. The plan verifier independently replays all proposals. The executor accepts only a `VerifiedAction`, executes one action in the symbolic environment, observes the result, and passes expected/observed effects to the effect verifier. A mismatch cannot commit expected effects.

## Persistent goals

Goals live in a deterministic `GoalStore`, keyed by stable semantic goal ID and owned by an agent. Goal creation and every lifecycle transition produce verification records. Satisfaction is evaluated only from signed current state. Selection sorts by descending explicit priority, descending current tension, creation turn and goal ID. Conflicting goals remain separate.

## Tension control model

Tension records retain raw and propagated contributions with fixed constants. Propagation is bounded BFS over semantic, topology and goal-dependency edges with deterministic decay, duplicate-node maximum merge and a total clamp. Tension selects capped cluster/planner tiers and scheduling urgency. It is excluded from verifier support sets and cannot alter facts, connections, goals or policy.

## Environment boundary and replanning

`EnvironmentAdapter` exposes observe, execute, inject, snapshot and replay restore. The in-process adapter is deterministic and cannot access shell, network or external state. Scheduled events are closed-schema environment transitions with provenance and receipts. Before every action, the agent checks goal status, origin compatibility, required signed propositions, topology, location, inventory and ownership. Any change invalidates remaining actions, preserves completed receipts, records a typed stale cause, increases tension and requests a new verified plan.

## Reflection and lessons

Reflection is a closed mapping from receipt patterns to summary codes and structured proposed lessons. It cannot execute code or mutate policy. Lessons remain `PROPOSED` until `/approve-lesson`; approval checks schema allowlists, receipt existence, deterministic operation and verifier preservation. Rejection and approval produce receipts. Approved lessons may only add mandatory verification timing or bounded effort preferences; they cannot authorize actions.

## Multi-agent extension points

The world uses agent-scoped location, inventory, ownership, observations, goals, plans and receipts. Scheduling is descending selected-goal priority, descending tension, then agent ID. A committed transaction is serialized in one deterministic turn; concurrency and races are explicit non-goals. Another agent's change invalidates affected plans with `AGENT_INTERFERENCE`. Permission facts gate take/give/use operations.

## Receipt migration

`ts-turn-receipt-v3` is additive. It embeds familiar parse, graph, merge, cluster, signed-state, decision, rendering, memory and replay sections, plus goals, tension, planning, loop steps, action transactions, environment events, replanning, reflection, lessons and multi-agent data. v1/v2 dataclasses and frozen fixtures remain unchanged. A v3 run hash covers initial snapshot, every input, scheduled event, configuration, approved lesson, loop receipt and repository compatibility SHA.

## Bypass, rollback and determinism risks

- **Plan treated as execution:** v2 plan steps simulate effects. V3 plan objects cannot call commit and render only as plans.
- **Expected effect trusted:** v2 events stage declared effects. V3 requires a post-execution observation and effect-verifier equality before commit.
- **Stale plan remains active:** every action revalidates origin compatibility and preconditions; invalidation clears remaining executable steps.
- **Rejected event contaminates state:** observations and events are staged separately; rejected structures never enter the trusted snapshot.
- **Tension becomes proof:** support validation accepts only semantic/environment receipt IDs, never tension IDs.
- **Reflection changes policy:** only verified explicit approval changes lesson status; proposed lessons are inert.
- **Agent overwrite:** all mutations are transactions with pre-state hash and agent/action identity; scheduler serializes them.
- **Rollback ambiguity:** replay restore replaces only environment snapshots; trusted world is rebuilt from verified receipts.
- **Nondeterminism:** all iteration, routes, candidates, ties and receipts use stable sorting and canonical hashes; wall-clock is only a hard budget input and is excluded from semantic decisions.
- **Hash incompatibility:** topology, goals and trusted agent state are included in v3 world hashes; repository SHAs are included in run replay metadata.

## Test strategy

Preserve and rerun all v1/v2 suites. Add unit tests for topology signs/direction, goal transitions, tension propagation/relaxation, plan verification, per-action transactions, effect mismatch, stale causes, reflection approval, scheduling and replay. Generate frozen 240-case functional and 240-case adversarial corpora before tuning; preserve the first report and rerun the identical files. Add ten end-to-end demos and explicit limit tests for every configured maximum.

## Explicit non-goals

No external model, embeddings, probabilistic parser, network knowledge, real-world actuation, generated code, self-modifying rules, hidden text generation, unbounded search, parallel agent execution, inferred emotion/intent/trust, biological equivalence or AGI claim. Language, topology, actions, causal rules, reflection and policies remain closed and bounded.
