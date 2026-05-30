# Eve Metabolism Main Merge Report

Generated: 2026-05-30 12:45 Europe/Lisbon

## Merge

- Target branch: `main`
- Integrated branch: `integration/eve-metabolism-full`
- Integrated commit: `85e6adc`
- Merge type: fast-forward
- Conflicts: none during merge into `main`

## Final Validation On Main

- `python -m pytest`: 175 passed
- `python scripts/run_capability_tests.py`: 21 passed
- `python scripts/check_fresh_clone_readiness.py`: ok true
- `python -c "from autonomy.eve_daily_loop import run_eve_daily_loop; ..."`: ok

## Daily Loop Dry Run

The final dry run executed successfully on `main` with:

- awareness
- daily transcript file checks
- diary consolidation
- dream and memory review
- recent error review
- research inbox summary
- research routing
- lab candidate planning
- improvement planning
- capability audit
- evolution metrics
- daily loop report path

## New Capabilities In Main

- Central Eve daily metabolism loop: `autonomy/eve_daily_loop.py`
- Daily loop markdown reporting: `autonomy/eve_daily_loop_report.py`
- Evolution metrics collection: `core/evolution_metrics.py`
- Research inbox: `research/research_inbox.py`
- Daily research runner: `research/daily_research_runner.py`
- Error review: `memory/errors/error_review.py`
- Autonomous lab review: `lab/autonomous_lab.py`
- Personality preference maturation hooks in `core/personality_engine.py`
- Tool registry entries for:
  - `eve_daily_loop`
  - `evolution_metrics_report`
  - `research_inbox_add`
  - `research_inbox_process`
  - `preference_candidate_record`
  - `preference_mature`
  - `error_review`
  - `lab_review`
  - `daily_research_collection`

## Local Files Left Out Of Commit

The final dry run updated local runtime/memory files. These were intentionally not committed:

- `lab/reports/candidate_decisions.jsonl`
- `memory/long_term/stable_memories.md`
- `memory/medium_term/autonomous_capability_improvements.md`
- `memory/medium_term/eve_17_point_goal_harness.md`
- `memory/medium_term/eve_capability_roadmap.md`
- `memory/memory_lifecycle_registry.json`
- `memory/personality/interest_evolution_seed.md`
- `memory/personality/preference_candidates.json`
- `memory/personality/preference_lifecycle.json`
- `memory/semantic_vector/embedding_index.json`
- `memory/technology/research_candidates.md`
- `state/admin_sessions.json`
- `state/capability_metrics.json`
- `state/capability_roadmap_state.json`
- `state/eve_status.json`
- `state/self_improvement_changes.json`

## Recommended Next Step

Activate and schedule the real recurring Eve metabolism loop on the primary runtime PC after confirming the PC2 runtime environment is ready.
