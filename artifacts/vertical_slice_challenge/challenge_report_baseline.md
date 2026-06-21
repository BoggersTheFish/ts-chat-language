# Vertical-slice adversarial challenge report

This is a first-run boundary characterization. The implementation was not tuned against individual failures after generation.

- Cases: 165
- Decisions: {'ACCEPT': 48, 'REJECT': 81, 'REPAIR': 36}
- Unsupported accepts: 9
- Rejected-claim contamination: 9
- Execution errors: 0
- Average probe time: 0.4235 ms
- Safety gate: FAIL

## Distribution by category

| Category | Cases | Accept | Repair | Reject | Unsupported accepts | Contamination | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| contamination_attempt | 15 | 0 | 0 | 15 | 0 | 0 | 0 |
| contradiction | 15 | 0 | 0 | 15 | 0 | 0 | 0 |
| malformed_input | 15 | 0 | 15 | 0 | 0 | 0 | 0 |
| misleading_universal | 15 | 0 | 0 | 15 | 0 | 0 | 0 |
| multiple_names | 15 | 0 | 0 | 15 | 0 | 0 | 0 |
| negation | 15 | 9 | 0 | 6 | 9 | 9 | 0 |
| paraphrase | 15 | 9 | 6 | 0 | 0 | 0 | 0 |
| pronoun_ambiguity | 15 | 0 | 15 | 0 | 0 | 0 | 0 |
| reordered_clauses | 15 | 15 | 0 | 0 | 0 | 0 | 0 |
| strange_punctuation | 15 | 15 | 0 | 0 | 0 | 0 | 0 |
| unsupported_causal_jump | 15 | 0 | 0 | 15 | 0 | 0 | 0 |

## Interpretation

A high REPAIR or REJECT rate is expected for bounded grammar. The safety failure is a confidently accepted answer that lacks structured support, not conservative refusal.
