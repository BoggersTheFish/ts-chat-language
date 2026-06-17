# TS-Chat Language / TSLC v0.4

**TSLC** — Thinking System Language Compiler.

A TS-native conversational language machine. Not token prediction. Not exposure training.

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
python3 -m chat.cli
```

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

- `ts_lang/` — input compiler
- `ts_state/` — conversation state machine
- `ts_render/` — response planner + renderer
- `chat/` — CLI session loop
- `data/` — compiled language resources (not training data)