from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.paths import STATE_DIR, ensure_project_dirs


SESSION_DB = STATE_DIR / "sessions.sqlite3"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _connect() -> sqlite3.Connection:
    ensure_project_dirs()
    conn = sqlite3.connect(SESSION_DB)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at)")
    return conn


def add_session_message(session_id: str, role: str, content: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    with _connect() as conn:
        created_at = now_iso()
        cursor = conn.execute(
            "INSERT INTO messages(session_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, json.dumps(metadata or {}, ensure_ascii=False), created_at),
        )
        return {"id": cursor.lastrowid, "session_id": session_id, "role": role, "created_at": created_at}


def search_sessions(query: str, *, limit: int = 20) -> list[dict[str, Any]]:
    pattern = f"%{query}%"
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, session_id, role, content, metadata, created_at
            FROM messages
            WHERE content LIKE ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (pattern, int(limit)),
        ).fetchall()
    return [
        {
            "id": row[0],
            "session_id": row[1],
            "role": row[2],
            "content": row[3],
            "metadata": json.loads(row[4] or "{}"),
            "created_at": row[5],
        }
        for row in rows
    ]


def export_session(session_id: str, target: str | Path | None = None) -> dict[str, Any]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, session_id, role, content, metadata, created_at FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
    target_path = Path(target) if target else STATE_DIR / "session_exports" / f"{session_id}.jsonl"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(
                json.dumps(
                    {
                        "id": row[0],
                        "session_id": row[1],
                        "role": row[2],
                        "content": row[3],
                        "metadata": json.loads(row[4] or "{}"),
                        "created_at": row[5],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    return {"session_id": session_id, "messages": len(rows), "path": str(target_path)}

