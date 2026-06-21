# TurnReceipt v3 and bounded reflection

`ts-turn-receipt-v3` contains turn, parse, MeaningGraph, merge, cluster, signed world, goals, tension, planning, loop steps, transactions, environment events, replanning, reflection, lessons, multi-agent state, decision, rendering, memory update and replay sections.

Each loop receipt identifies phase, selected goal/plan/action, pre/post hashes, tension, decision and support. The run replay hash covers the initial snapshot, input sequence, scheduled events, configuration, approved lessons, compatible SHAs and every transition.

Reflection is a closed receipt analysis. Triggers include action failure, stale plan, external event, effect mismatch, satisfaction, unreachable and budget exhaustion. It records typed summary codes, factors and assumptions. It cannot state facts, authorize actions or modify policy.
