# Point 03 Consolidation Core

Goal: diary consolidation should produce structured memory decisions, not only summaries.

Implemented core:

- `dream/consolidation_schema.py`
- `ConsolidationInput`
- `ConsolidationSignal`
- `ConsolidationDecision`
- `ConsolidationReport`
- `dream/diary_consolidator.py` now emits markdown, JSON and `candidate_memories.jsonl`

Signal types: fact, preference, project_update, task, error, idea, relationship, technical_decision, future_followup.

8.6 criterion: mostly met. Future improvement: replace heuristic signal extraction with an LLM-assisted pass when token gate allows.
