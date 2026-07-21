"""DB パッケージの互換用 export。

新しいコードでは app.db.connection、app.db.schema、各 repository モジュールを
直接 import する。このモジュールは既存連携を安定させるために残している。
"""

from app.db.chat_repository import list_chat_messages, save_chat_message
from app.db.connection import connect
from app.db.schema import initialize_database

__all__ = [
    "connect",
    "initialize_database",
    "list_chat_messages",
    "save_chat_message",
]
