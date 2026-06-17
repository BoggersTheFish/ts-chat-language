# TS-Chat Language / TSLC v0.1

**TSLC** — Thinking System Language Compiler.

A TS-native conversational language machine. Not token prediction. Not exposure training.

```text
USER TEXT
  → Normalizer
  → Dialogue Act Compiler
  → Semantic Frame Compiler
  → TS Meaning Graph (CompiledTurn)
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

## v0.1 boundary

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