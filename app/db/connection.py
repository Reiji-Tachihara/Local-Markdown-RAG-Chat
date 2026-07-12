import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app.config import Settings


@contextmanager
def connect(settings: Settings) -> Iterator[sqlite3.Connection]:
    """SQLite 接続を開き、成功した処理を commit する。"""

    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()
