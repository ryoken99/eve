# PC1 Phase 2 Supervision

Generated: 2026-05-30 12:55 Europe/Lisbon

## Role

PC1 is now supervisor, auditor, and build machine for Eve.

PC2 is expected to activate and validate the recurring Eve metabolism runtime.
PC1 should not add new features while PC2 validates activation.

## Main State

- Current branch: `main`
- Current main commit: `2cb8e00`
- Confirmed tag: `eve-metabolism-v0.1`
- Integrated version: Eve Metabolism v0.1

## Local PC1 Validation

- `python -m pytest`: 175 passed
- `python scripts/run_capability_tests.py`: 21 passed
- `python scripts/check_fresh_clone_readiness.py`: ok true

Environment note:

- `tesseract_executable_on_path`: false
- This is not blocking for the core metabolism. Tesseract remains optional for OCR fallback.

## Metabolism v0.1 Modules

- `autonomy/eve_daily_loop.py`
- `autonomy/eve_daily_loop_report.py`
- `core/evolution_metrics.py`
- `research/research_inbox.py`
- `research/daily_research_runner.py`
- `memory/errors/error_review.py`
- `lab/autonomous_lab.py`
- `core/personality_engine.py`
- `core/eve_tool_registry.py`

Tool registry should expose:

- `eve_daily_loop`
- `evolution_metrics_report`
- `research_inbox_add`
- `research_inbox_process`
- `preference_candidate_record`
- `preference_mature`
- `error_review`
- `lab_review`
- `daily_research_collection`

## How To Verify PC2 Activation

On PC2, after pulling `main`, run:

```powershell
git checkout main
git pull origin main
python -m pytest
python scripts/run_capability_tests.py
python scripts/check_fresh_clone_readiness.py
python -c "from autonomy.eve_daily_loop import run_eve_daily_loop; r = run_eve_daily_loop(cycle_name='pc2_phase2_dry_run', dry_run=True); print(r); assert isinstance(r, dict); assert 'steps' in r; print('pc2 daily loop ok')"
```

Then test the individual dry-run components:

```powershell
python -c "from core.evolution_metrics import write_evolution_metrics_report; print(write_evolution_metrics_report())"
python -c "from research.daily_research_runner import run_daily_research_collection; print(run_daily_research_collection(dry_run=True, max_items=3))"
python -c "from memory.errors.error_review import run_error_review; print(run_error_review(limit=20, dry_run=True))"
python -c "from lab.autonomous_lab import run_lab_review; print(run_lab_review(max_candidates=3, dry_run=True))"
```

## Expected PC2 Files After Activation

Daily loop:

- `logs/autonomy/daily_loop/YYYY-MM-DD.md`

Evolution metrics:

- `memory/medium_term/evolution_metrics/YYYY-MM-DD.md`

Diary/consolidation outputs:

- `logs/transcripts/*/DD-MM-YY.jsonl`
- `memory/medium_term/daily_summary_YYYY-MM-DD.md`

Dream/memory review:

- `memory/dream_reports/dream_YYYY-MM-DD.md`
- `lab/reports/dream_YYYY-MM-DD.md`

Research and lab:

- `memory/technology/research_candidates.md`
- `memory/world/world_learning.md`
- `memory/technology/technology_learning.md`
- `lab/reports/candidate_decisions.jsonl`

Capability and state:

- `memory/medium_term/eve_capability_roadmap.md`
- `state/capability_metrics.json`
- `state/capability_roadmap_state.json`

These files are runtime/local evidence. They should stay local unless explicitly selected for migration or anonymized reporting.

## Failure Symptoms To Watch

- `pytest` import errors from optional packages that should degrade gracefully.
- `run_eve_daily_loop(..., dry_run=True)` raises instead of returning a dict.
- Daily loop returns no `steps`.
- A failed step stops the whole loop instead of recording `ok=false` and continuing.
- Tool registry missing any metabolism tool.
- Research dry-run attempts real online actions unexpectedly.
- Error review or lab review writes destructive changes in dry-run mode.
- Scheduled activation publishes online, opens accounts, or sends messages without explicit command.
- Private logs, state, transcripts, or memory get staged for Git commit.

## Comparison Procedure

Compare the PC2 output against PC1 baseline:

1. Daily loop report:
   - Confirm all main steps appear.
   - Confirm failures are recorded as degraded steps, not crashes.

2. Metrics report:
   - Confirm `autonomy_cycles_today` increments after runs.
   - Confirm `capability_average_score` is present.
   - Confirm weakest capability points are listed.

3. Research dry-run:
   - Confirm it returns structured research items or a dry-run plan.
   - Confirm it does not require browser posting or public actions.

4. Error review:
   - Confirm recent errors are grouped and summarized.
   - Confirm no core patch is applied in dry-run mode.

5. Lab review:
   - Confirm candidates are listed/planned.
   - Confirm dry-run does not promote or apply changes.

## Sandro Checklist

- [ ] PC2 is on `main`.
- [ ] PC2 has commit `2cb8e00` or newer.
- [ ] Tag `eve-metabolism-v0.1` exists locally or remotely.
- [ ] `python -m pytest` passed on PC2.
- [ ] `daily loop dry_run` passed on PC2.
- [ ] Metrics report was created.
- [ ] Research dry-run passed.
- [ ] Error review dry-run passed.
- [ ] Lab review dry-run passed.
- [ ] Schedule was created, or a schedule plan was created if scheduler integration is unavailable.
- [ ] Private logs remained local.
- [ ] Runtime state remained local.
- [ ] Nothing was published online.
- [ ] No email, X post, Telegram message, or browser account action happened unless explicitly requested.

## Recommended Next Step

PC2 should run the full dry-run checklist first. If all dry-runs pass, PC2 can create the recurring schedule for the metabolism loop and send back:

- daily loop report path
- metrics report path
- scheduler/task evidence
- git status
- any failed/degraded steps

PC1 should then compare PC2's evidence against this supervision checklist before approving real recurring autonomy.
