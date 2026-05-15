# Point 14 Autonomous Improvement Core

Goal: Eve generates improvements from audits, errors, dreams, research, lab results and user requests.

Implemented core:

- existing `self_improvement/improvement_planner.py`
- `improvement_candidate_to_lab_candidate()`
- `improvement_candidate_to_patch_plan()`

8.6 criterion: partially met. Next improvement: make `plan_autonomous_system_improvements()` consume all signal sources in one ranked queue.
