# Vertical-slice limitations

- Grammar is a small deterministic collection of sentence patterns, not broad NLP.
- Supported reasoning is limited to direct binary relations, one declared transitive ordering predicate, conjunctive Boolean rules, explicit possibility rejection, possessive clarification, and one-step before/after planning.
- Pronouns are clarified rather than guessed when more than one antecedent exists.
- Negation is not represented in the milestone schema; it is explicitly blocked and sent to clarification rather than interpreted as affirmative evidence.
- Templates favour traceability over conversational fluency and do not paraphrase freely.
- Memory is in-process, bounded to verified structured premises, and reset between CLI launches.
- User-provided premises are recorded as premises, not certified as real-world facts.
- There is no external knowledge, network inference, embedding model, transformer, or hidden fallback.
- Processing-time metrics cover this deterministic local slice only.
- The remaining primary bypass risk is future code accidentally calling the legacy TSLC renderer; vertical-slice tests therefore instantiate only the verifier-gated session and assert support IDs before affirmative rendering.

This is not a general chatbot, AGI system, theorem prover, or production operating system.
