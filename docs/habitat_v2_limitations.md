# Habitat v2 limitations

- Grammar is a small rule set, not broad NLP. Unsupported paraphrases reject or request clarification.
- Signed state covers a fixed predicate family and bounded negation forms.
- Event time is turn order only. There are no dates, durations, concurrent events, rollback, or arbitrary temporal logic.
- Containment answers expose declared chains only; they do not infer general physics.
- Shared ownership is not represented. Give transitions enforce one active owner.
- Causal inference is positive, monotonic, query-local, depth-four, and capped at 64 derived facts. It does not persist derived conclusions.
- Planning uses fixed schemas, open-topology movement between declared places, uniform cost, depth eight, and at most 512 explored states. It is not optimal planning for arbitrary domains.
- Unknown and conflicted states are conservative. A higher reject/repair rate is acceptable; unsupported acceptance is not.
- Persistent state lasts for the CLI process and is not a database.
- User premises are recorded as premises, not certified real-world truth.
- There is no external knowledge, training, embedding, transformer, or hidden language fallback.
- This is not a general chatbot, animal-brain analogue, AGI system, general theorem prover, or production operating system.
