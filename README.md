# TS-Chat Language / TSLC v0.8

**TSLC** — Thinking System Language Compiler (language compiler core).

**DDS** — Deterministic Dialogue Substrate (in progress): language compiled into inspectable TS state.

**TS-Chat** — one application running on DDS.

A TS-native conversational language machine. Not token prediction. Not exposure training.

## Verifier-first vertical slice

The first complete TS language-to-verifier vertical slice runs end to end: deterministic text parsing, MeaningGraph construction, verifier-gated `ACCEPT`/`REPAIR`/`REJECT` decisions, deterministic response rendering, and unified turn receipts.

```bash
./scripts/run_vertical_slice.sh
```

It supports bounded relational, Boolean, ambiguity, unsupported-inference, and small planning cases. It is not a general-purpose chatbot and does not use an external language model. See [the vertical-slice guide](docs/vertical_slice.md), [integration audit](docs/vertical_slice_integration_audit.md), and [limitations](docs/vertical_slice_limitations.md).

```text
USER TEXT
  → Normalizer
  → Dialogue Act Compiler
  → Semantic Frame Compiler
  → TS Meaning Graph (`MeaningGraph` on `CompiledTurn`)
  → Conversation State Update
  → Response Planner
  → Surface Renderer
  → BOT TEXT
```

## Quick start

```bash
cd ts-chat-language
python3 -m unittest discover -v
python3 -m chat.cli --demo
python3 -m chat.cli --packs base_dialogue,ts_architecture
```

## v0.8: declarative graph and topic rules

Derived meaning-graph nodes and topic resolution now load from pack JSON — no hard-coded branches in `meaning_graph.py` or `infer_topic()`.

```text
semantic frames → graph_rules.json derivations → derived nodes/edges
known topics + act meaning → topic_rules.json → resolved topic
```

Pack files in `base_dialogue`:

- `graph_rules.json` — scope rejects/accepts, architecture constraints, focus shifts
- `topic_rules.json` — topic priority, act-meaning focus, fallback

Adding a domain can extend graph/topic behavior by shipping new rule files in a pack.

## v0.7: language pack system

Patterns, dialogue acts, semantic rules, lexicon, schemas, and templates load from **`ts_packs/`** — not hard-coded Python branches.

```text
load active packs → match dialogue acts → evaluate semantic_rules → emit frames → validate graph
```

Default packs: `base_dialogue` + `ts_architecture`. Override with `TSLC_PACKS` env or `--packs` CLI flag.

### Adding a domain (no compiler edits)

```text
ts_packs/my_domain/
├── pack.json
├── phrase_patterns.json
├── semantic_rules.json
└── templates.json
```

Activate: `TSLC_PACKS=base_dialogue,my_domain python3 -m chat.cli`

## v0.6: diff-memory-driven planning

Accumulated `graph_diff` history now drives response planning:

- `build_diff_memory()` aggregates prior rejects, accepts, and focus trajectory
- `memory_context` enriches `main_point` (e.g. "You already ruled out architecture parity; shifting focus...")
- Memory-aware templates: `confirm_shift_with_memory`, `provide_plan_with_memory`, `ack_correction_with_memory`

## v0.5: graph-diff memory receipts

Each `TurnReceipt` now includes a `graph_diff` against the previous turn's meaning graph:

- Added/removed semantic nodes (stable keys, not frame index)
- Focus, topic, and dialogue-act transitions
- Constraint deltas: rejects, accepts, prefers, avoids
- Serialized into turn history for multi-turn memory inspection

## v0.4: graph-driven state and planning

`ConversationState` and the response planner now read **`meaning_graph` nodes and edges** — not parallel `semantic_frames` iteration.

- State rejects come from `rejected_scope` graph nodes
- Accepted constraints are graph frame nodes (`node_id`, `kind`, `slots`, `provenance`)
- Response `main_point` and template selection query the graph via `ts_lang/graph_queries.py`

## v0.3: graph-normalized constraints + stable node identity

- **Normalized list slots** at frame-build time (`rejects`, `accepts`, `avoid`, `prefer`, `deprioritize`, `not_required`)
- **Deterministic node IDs** from semantic values and frame builder identity — not frame index
- **Deduped derived nodes** — same semantic constraint maps to one node
- **`validate_meaning_graph()`** — checks provenance, edge integrity, no Python repr strings, no duplicate semantic nodes

## v0.2: explicit meaning graph

Every compiled turn carries an explicit `MeaningGraph`:

- `MeaningNode` — dialogue act root, semantic frames, and derived scope/constraint/focus nodes
- `MeaningEdge` — `expresses`, `rejects`, `accepts`, `avoids`, `prefers`, `shifts_to`
- **Provenance** on every node and edge — which phrase pattern or frame builder created it

`TurnReceipt.compiled_turn.meaning_graph` is fully serializable via `to_dict()` (includes validation report).

## v0.1 boundary (still holds)

This is a conversational language compiler shell.

- No transformer
- No external LLM
- No reasoning engine integration
- Pattern-backed compilation with explicit receipts

Confidence is parse certainty, not proof.

## Golden example

Input:

```text
nah bro we just want the same usability
```

Output:

```text
Right. The target is usability parity, not architecture parity. The system should feel like a normal chatbot while compiling language into TS state underneath.
```

## Layout

- `ts_packs/` — loadable language packs (dialogue acts, rules, templates)
- `ts_lang/` — input compiler + declarative `frame_rules` engine
- `ts_state/` — conversation state machine + diff memory
- `ts_render/` — response planner + renderer
- `chat/` — CLI session loop
- `data/` — legacy resources (superseded by packs; kept for reference)
