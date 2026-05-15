# Point 02 Transcripts Core

Goal: all Eve events use a shared transcript contract.

Implemented core:

- `memory/transcript_schema.py`
- `TranscriptEvent`
- `normalize_transcript_event()`
- `memory/transcript_index.py`
- `append_structured_transcript()`
- `search_transcripts()`
- channels: chat, console, interface, tools, actions, errors, autonomy, dream, research, arsi
- integration hook in `memory/daily_transcripts.py`

8.6 criterion: met at core level. Codex 2 must ensure every runtime tool path writes these events.
