from app.config import Settings
from app.db.connection import connect


def initialize_database(settings: Settings) -> None:
    """RAG、ノート、チャット履歴で使うローカル SQLite テーブルを作成する。"""

    with connect(settings) as connection:
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
