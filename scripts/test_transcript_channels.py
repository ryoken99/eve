from __future__ import annotations

from runtime_validation_lib import check, finalize

from memory.daily_transcripts import TRANSCRIPT_TYPES, append_transcript, ensure_daily_transcript_files, transcript_path


def main() -> dict:
    ensure_daily_transcript_files()
    events = {
        "chat": ("runtime_chat", {"role": "user", "content": "runtime transcript test"}),
        "console": ("runtime_console", {"stream": "stdout", "text": "console line"}),
        "interface": ("runtime_interface", {"source": "test", "target": "eve", "content": "interface line"}),
        "tools": ("runtime_tool", {"tool": "runtime_test", "result": {"ok": True}}),
        "errors": ("runtime_error", {"source": "runtime", "error": "synthetic"}),
        "actions": ("runtime_autonomy", {"kind": "autonomy", "status": "observed"}),
    }
    written = {kind: append_transcript(kind, event, payload) for kind, (event, payload) in events.items()}
    checks = []
    for kind in TRANSCRIPT_TYPES:
        path = transcript_path(kind)
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        checks.append(check(f"{kind} transcript file exists and has runtime event", path.exists() and f"runtime_" in text, {"path": str(path), "last_hash": written.get(kind, {}).get("hash")}, critical=True))
    return finalize("point_02_transcripts_runtime", "Point 02 Transcripts Runtime", "point_02_transcripts_runtime.md", checks, {"written": written})


if __name__ == "__main__":
    main()
