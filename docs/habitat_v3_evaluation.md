# Habitat v3 evaluation

The frozen functional corpus has 240 cases: 30 each for topology/routes, persistent goals, tension, actions, effects, replanning, reflection/lessons and multi-agent behavior. The frozen adversarial corpus has 240 cases across 40 attack categories. The first adversarial report is preserved separately from the unchanged-corpus final rerun.

Run:

```bash
python3 scripts/build_habitat_v3_corpora.py  # deterministic reproduction only
PYTHONPATH=../TS-Reasoner-v0:$PYTHONPATH python3 -m ts_vertical_slice.habitat_v3_evaluation
```

Reports include all requested authorization, contamination, topology, tension, stale-plan, reflection, multi-agent, rendering, replay, timing, step and explored-state metrics. Safety hard gates require zero unsafe counts and 100% receipt generation. Conservative blocked, unreachable and budget outcomes are allowed. Expected-outcome match is reported separately from safety.

Baseline Habitat v2 commands are unchanged: the 30 original, 165 adversarial, 120 functional and 102 adversarial suites remain mandatory regressions.
