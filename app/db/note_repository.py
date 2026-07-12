from datetime import datetime, timezone
from pathlib import Path

from app.config import Settings
from app.db.connection import connect


def save_note_record(settings: Settings, title: str, content: str, source_path: Path) -> dict:
    """knowledge/notes に保存された Markdown ノートのメタデータを保存する。"""

    created_at = datetime.now(timezone.utc).isoformat()
    with connect(settings) as connection:
        cursor = connection.execute(
            """
            INSERT INTO notes(title, content, source_path, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (title, content, source_path.as_posix(), created_at),
        )
        note_id = cursor.lastrowid
    return {
        "id": note_id,
        "title": title,
        "content": content,
        "source_path": source_path.as_posix(),
        "created_at": created_at,
    }


def list_note_records(settings: Settings, limit: int = 50) -> list[dict]:
    """最近保存されたノートのメタデータを新しい順に返す。"""

    safe_limit = max(1, min(limit, 200))
    with connect(settings) as connection:
        rows = connection.execute(
            """
            SELECT id, title, content, source_path, created_at
            FROM notes
            ORDER BY id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()
    return [dict(row) for row in rows]
