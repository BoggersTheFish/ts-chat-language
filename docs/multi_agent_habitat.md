# Bounded multi-agent Habitat

Agents retain separate location, carried objects, owned objects, goals and policies. Environment observations derive each inventory from signed facts. Permission evidence gates taking another owner's object. Give/receive remains a closed transactional action.

Scheduling sorts selected-goal priority descending, tension descending and agent ID. Execution is serialized and turn-based; concurrent races are out of scope. Another agent's event invalidates affected plans with `AGENT_INTERFERENCE`. Opposed goals remain separate and become `CONFLICTED`, with scheduling/conflict evidence exposed rather than silently choosing a globally correct preference.

No emotion, deception, trust, social norm or intent is inferred.
