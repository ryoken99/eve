# Point 09 Lab Core

Goal: Eve needs a lab with hypotheses, tests, metrics and decisions.

Implemented core:

- `lab/lab_schema.py`
- `LabCandidate`
- lifecycle states: idea, planned, running, tested, accepted, rejected, archived
- `lab/lab_manager.py`
- `create_lab_candidate()`
- `record_lab_result()`
- `promote_lab_candidate()`
- `reject_lab_candidate()`

8.6 criterion: met at core level. Codex 2 should validate end-to-end lab candidate creation from runtime failures.
