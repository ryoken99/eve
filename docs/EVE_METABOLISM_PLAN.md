# Eve Metabolism Plan

## Objective

The Eve metabolism is the central recurring cycle that connects existing tools
instead of replacing them. It coordinates awareness, transcripts, diary,
memory, dreams, errors, research, lab candidates, improvement planning,
metrics, and reports.

The design goal is incremental integration: every step must be auditable, every
failure must be captured, and the loop must continue in degraded mode when a
module is missing or a step fails.

## Architecture

1. Awareness
   - Collect time, machine, system, active context, and available local state.
   - Source: `core.awareness_engine.collect_awareness`.

2. Diary and transcripts
   - Ensure daily transcript files exist for chat, console, interface, tools,
     actions, errors, autonomy, dream, research, and ARSI.
   - Source: `memory.daily_transcripts.ensure_daily_transcript_files`.

3. Diary consolidation
   - Convert diary noise into structured memory signals and daily summaries.
   - Source: `dream.diary_consolidator.consolidate`.

4. Layered memory
   - Keep short, medium, and long memory distinct.
   - Daily loop should never delete memory automatically.

5. Semantic memory
   - Rebuild or prefetch semantic context when useful.
   - Source: existing vector memory providers.

6. Dream cycle
   - Re-read memory and consolidation outputs, create dream reports, and queue
     lab ideas.
   - Source: `dream.dream_cycle.run_dream_cycle` and
     `dream.memory_reorganizer`.

7. Error review
   - Read recent errors, summarize recurrence, and expose improvement
     candidates.
   - Source now: `memory.errors.error_memory.recent_errors`.
   - Future Codex 2 source: `memory.errors.error_review`.

8. Research inbox
   - Gather pending research items from daily research outputs.
   - Future Codex 2 source: `research.research_inbox`.

9. World learning
   - Route non-technical learning to `memory/world/daily/DD-MM-YY.md`.

10. Technology learning
   - Route technical learning, AI, papers, open source, and tooling notes to
     `memory/technology/daily/DD-MM-YY.md`.

11. Personality/interests learning
   - Separate Sandro preferences from Eve preference candidates.
   - Future Codex 2 source: personality evolution helpers.

12. Lab candidates
   - Turn research, repeated errors, dream ideas, and self-chosen ideas into
     testable lab candidates.
   - Source: `lab.lab_manager`.

13. Improvement planner
   - Build safe improvement candidates from capability gaps and errors.
   - Source: `self_improvement.improvement_planner`.

14. Verified self-update
   - Core edits must go through candidate, tests, backup, and rollback-ready
     evidence.
   - Source: `self_improvement.verified_self_update`.

15. Autonomy report
   - Write a daily loop report with evidence, failures, and next actions.
   - Source: `autonomy.eve_daily_loop_report`.

16. Daily message/report to Sandro
   - Produce a short, human-readable summary. The loop does not publish or send
     messages externally unless a separate approved tool handles notification.

17. Metrics and evidence
   - Count transcripts, diary entries, memory changes, errors, research, lab,
     improvements, autonomy cycles, and 17-point capability scores.
   - Source: `core.evolution_metrics`.

## Execution Contract

`run_eve_daily_loop()` returns a structured dict and always records step-level
success/failure. A failing step must not stop later steps.

Dry-run mode must avoid destructive or external actions. It may still read
state and write local reports so the result is auditable.

## Scheduling

The loop should be scheduled via Eve's existing cron manager when possible. If
cron is unavailable, the schedule function must return a plan/error instead of
throwing.
