# Point 10 Errors And Terminal Core

Goal: every error should become technical memory and a possible improvement.

Implemented core:

- `memory/errors/error_schema.py`
- `ErrorMemoryItem`
- `classify_error()`
- `error_to_lesson()`
- `error_to_lab_candidate()`
- `known_fix_lookup()`
- integration in `memory/errors/error_memory.py`

8.6 criterion: core met. Runtime should ensure terminal transcripts are always routed here.
