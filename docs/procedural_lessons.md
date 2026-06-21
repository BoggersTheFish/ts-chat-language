# Procedural lessons

Lessons are closed data with type, condition, recommended deterministic operation, evidence receipt IDs and status. Allowed types are `REVALIDATE_PRECONDITION`, `CHECK_ROUTE_BEFORE_MOVE`, and `VERIFY_EFFECT_IMMEDIATELY`; allowed policies only add verification timing/checks.

New lessons remain `PROPOSED`. `/approve-lesson` verifies type, operation, existing evidence and authority preservation. `/reject-lesson` records explicit rejection. Approved lessons cannot add effects, bypass preconditions or authorize actions. When applied, their ID appears in the action-precondition loop receipt. No source editing, generated code or automatic parser modification exists.
