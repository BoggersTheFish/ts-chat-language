# Habitat v3 limitations

This is a deterministic symbolic simulation with bounded language and planning. It is not a general chatbot, biological model, AGI, autonomous real-world system or self-modifying intelligence. It uses no external model, embeddings, probabilistic parser, network knowledge, planning service or hidden generator.

Default caps are: 1,024 connections; 4,096 semantic items; 512 active-cluster items; 64 goals; 256 tension records; planner depth 12; 2,048 explored states; 8 replans; 64 loop iterations; 8 plans per goal; 32 actions; 64 causal derivations; 10 seconds; 1 MB receipt; 128 events; and 8 agents. Every enforced limit yields an explicit error, blocked/unreachable result or `BUDGET_EXHAUSTED`; it never implies success.

Language remains a closed regex grammar. Topology and action physics are declared, not learned. Social behavior is limited to ownership and explicit permission. Execution is serialized, not concurrent. Reflection has a small allowlist. The environment is in-process only and does not actuate the real world.
