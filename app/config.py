from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリ全体の設定を .env と既定値から読み込む。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Local Markdown RAG Chat"
    knowledge_dir: Path = Path("knowledge")
    data_dir: Path = Path("data")
    database_path: Path = Path("data/app.db")

    embedding_backend: str = "ollama"
    hash_embedding_dimensions: int = 384

    ollama_base_url: str = "http://localhost:11434/api"
    enforce_local_ollama: bool = True
    ollama_chat_model: str = "qwen3:8b"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_request_timeout: int = 180

    chunk_size: int = 900
    chunk_overlap: int = 120
    retrieval_limit: int = 4
    rag_context_max_chars: int = 12000
    chat_message_max_chars: int = 12000

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    def ensure_directories(self) -> None:
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        for directory in ("conversations", "notes", "seek"):
            (self.knowledge_dir / directory).mkdir(parents=True, exist_ok=True)

    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def validate_local_only(self) -> None:
        """外部公開につながる Ollama 設定を早い段階で検出する。"""

        if not self.enforce_local_ollama:
            return

        parsed = urlparse(self.ollama_base_url)
        allowed_hosts = {"localhost", "127.0.0.1", "::1"}
        if parsed.hostname not in allowed_hosts:
            raise ValueError(
                "ENFORCE_LOCAL_OLLAMA=true の場合、OLLAMA_BASE_URL は localhost / "
                f"127.0.0.1 / ::1 のいずれかにしてください。現在の値: {self.ollama_base_url}"
            )


@lru_cache
def get_settings() -> Settings:
    """設定を1回だけ作り、以後は同じ Settings を使い回す。"""

    settings = Settings()
    settings.validate_local_only()
    settings.ensure_directories()
    return settings
