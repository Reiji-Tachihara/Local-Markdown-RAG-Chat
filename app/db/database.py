import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from app.config import Settings


@contextmanager
def connect(settings: Settings) -> Iterator[sqlite3.Connection]:
    # sqlite3.Row を使うと row["column_name"] の形で読みやすく取り出せる。
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database(settings: Settings) -> None:
    with connect(settings) as connection:
        # chunks は RAG 検索用、notes は MCP の save_note/list_notes 用。
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_path TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT NOT NULL,
                checksum TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(source_path, chunk_index)
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_path TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


def save_note_record(settings: Settings, title: str, content: str, source_path: Path) -> dict:
    # DB にはメタデータを保存し、Markdown 本文自体は knowledge/notes/ にも残す。
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
    # limit を丸めることで、誤って大量取得するリクエストを避ける。
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
