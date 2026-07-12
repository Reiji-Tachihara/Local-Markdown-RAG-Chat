import json
from datetime import datetime, timezone

from app.config import Settings
from app.db.connection import connect
from app.db.schema import initialize_database


def save_chat_message(
    settings: Settings,
    role: str,
    content: str,
    persona: str,
    contexts: list[dict],
) -> dict:
    """チャットメッセージを1件保存し、保存したレコードを返す。"""

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
    """最近のチャットメッセージを新しい順に返す。"""

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
