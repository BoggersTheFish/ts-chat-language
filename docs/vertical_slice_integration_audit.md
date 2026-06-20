# Vertical-slice integration audit

## Repository lock

- `ts-chat-language`: `/home/boggersthefish/TS-OS/ts-chat-language`, `master`, starting SHA `b077161b3279d7a519d3903bee6e8ce2ecc985f1`.
- `TS-Reasoner-v0`: `/home/boggersthefish/TS-OS/TS-Reasoner-v0`, `main`, starting SHA `5a06dd1328e9b43314894b33ad5b2c182c1757e2`.
- Both working trees were clean before integration work.

## Current language boundary

`ts-chat-language` accepts a Python `str` through `compile_utterance()` or `TSChatSession.handle()`. The compiler normalizes text, assigns a dialogue act, builds semantic frames, and emits `CompiledTurn`. Its canonical structured output is `CompiledTurn.meaning_graph`, a serialisable `MeaningGraph` containing provenance-bearing `MeaningNode` and `MeaningEdge` objects plus graph validation.

MeaningGraph already preserves dialogue act, topic, semantic-frame slots, phrase/rule provenance, explicit graph relations, validation results, and parse ambiguities. Existing graph-diff and conversation structures retain prior graph changes, but the current session mutates dialogue state before any external verifier runs.

## Current reasoner boundary

TS-Reasoner currently accepts `question: str` plus optional textual premises. `TSReasoner.run()` generates candidate chains, checks claim interaction, scores tension, performs bounded repair, and emits `ReasonerOutput` with selected chain, checks, repairs, final answer, and trace. `typed_support.py` and `support_path_verifier.py` provide canonical SHA-256 support objects for a narrow quantified-claim domain. `CommonGround` demonstrates verifier-gated accepted and rejected records, but its binary relation type cannot represent all required predicates and Boolean/planning constraints.

## Direct mappings

- MeaningGraph node IDs and edge IDs map to request provenance and source IDs.
- Frame schemas map to request intent, claims, relations, constraints, and ambiguities.
- Node labels/slots map to entities and predicate arguments.
- Existing graph validation maps to the bridge validation gate.
- TS-Reasoner typed-support hashes map to verifier check support certificates.
- Existing graph-diff concepts map to receipt and replay state transitions.

## Translation required

- TSLC currently lacks dynamic relational, Boolean, ambiguity, and planning frames; a bounded deterministic reasoning parser must add them without replacing the pack compiler.
- MeaningGraph permits generic slots, while TS-Reasoner requires explicit typed entities, relations, rules, queries, provenance, and requested output.
- Existing TS-Reasoner text candidates cannot safely express all milestone predicates; a narrow structured request/verifier surface is required.
- Existing TSLC response planning can render unverified `main_point` text, so the vertical-slice renderer must consume verifier-approved structured answers only.

## Concepts that cannot cross unchanged

- Emotion, styling, and legacy architecture-discussion frames are not reasoning evidence. They must produce explicit non-blocking bridge warnings or a blocking unsupported-domain result.
- Parse confidence is not proof and cannot become verifier support.
- Raw user wording cannot become final factual text.
- Existing TSLC accepted frames cannot enter reasoning memory before verification.
- Existing TS-Reasoner free-text `final_answer` is not sufficient authority for the new renderer.

## Smallest semantics-preserving bridge

Add frozen structured request types and a structured verifier in TS-Reasoner. Add a deterministic MeaningGraph adapter in `ts-chat-language` that imports those public types through an editable sibling dependency. Preserve both existing pipelines; the new `ts_vertical_slice` package composes them without changing their default CLIs.

The bridge is total: every graph node is translated, recorded as intentionally non-reasoning, or reported as blocking information loss. Canonical JSON hashes make repeated translation observable.

## Bypass audit

Potential bypasses are the existing TSLC renderer, state mutation before verification, textual TS-Reasoner answers, repaired claims entering memory directly, ignored bridge warnings, and response templates interpolating raw text. The vertical slice blocks these by using a separate verifier-gated session, immutable decisions, support-ID validation in the renderer, post-verification memory commits, a one-pass repair bound, and assertions that affirmative answer fields originate in approved structured results.

## Reuse versus implementation

Reuse MeaningGraph, CompiledTurn, normalization, provenance, graph validation, graph diffs, canonical typed-support hashing, and TS-Reasoner verifier philosophy. Implement the bounded reasoning parser, structured request contract, graph bridge, structured verifier, approved-answer renderer, unified receipt, verified conversation state, CLI, replay fixtures, and evaluation harness.

This milestone deliberately does not provide unrestricted grammar, a learned language model, broad conversation, external knowledge, or proof beyond the supplied premises and declared deterministic rules.
