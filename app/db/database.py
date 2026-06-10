import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from app.config import Settings


@contextmanager
def connect(settings: Settings) -> Iterator[sqlite3.Connection]:
    """SQLite 接続を開き、処理後に commit と close を確実に行う。"""

    # sqlite3.Row を使うと row["column_name"] の形で読みやすく取り出せる。
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database(settings: Settings) -> None:
    """アプリ起動時に必要な SQLite テーブルを作成する。"""

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

            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                persona TEXT NOT NULL,
                contexts TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


def save_note_record(settings: Settings, title: str, content: str, source_path: Path) -> dict:
    """MCP の save_note で保存したノート情報を notes テーブルへ記録する。"""

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
    """保存済みノートを新しい順に取得する。"""

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


def save_chat_message(
    settings: Settings,
    role: str,
    content: str,
    persona: str,
    contexts: list[dict],
) -> dict:
    """チャットメッセージを SQLite に保存する。"""

    initialize_database(settings)
    created_at = datetime.now(timezone.utc).isoformat()
    with connect(settings) as connection:
        cursor = connection.execute(
            """
            INSERT INTO chat_messages(role, content, persona, contexts, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (role, content, persona, json.dumps(contexts, ensure_ascii=False), created_at),
        )
        message_id = cursor.lastrowid
    return {
        "id": message_id,
        "role": role,
        "content": content,
        "persona": persona,
        "contexts": contexts,
        "created_at": created_at,
    }


def list_chat_messages(settings: Settings, limit: int = 50) -> list[dict]:
    """保存済みチャット履歴を新しい順に取得する。"""

    initialize_database(settings)
    safe_limit = max(1, min(limit, 200))
    with connect(settings) as connection:
        rows = connection.execute(
            """
            SELECT id, role, content, persona, contexts, created_at
            FROM chat_messages
            ORDER BY id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()

    messages: list[dict] = []
    for row in rows:
        record = dict(row)
        record["contexts"] = json.loads(record["contexts"])
        messages.append(record)
    return messages
