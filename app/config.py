from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Local Markdown RAG Chat"
    knowledge_dir: Path = Path("knowledge")
    data_dir: Path = Path("data")
    database_path: Path = Path("data/app.db")

    # 既定では Ollama embedding を使う。hash は疎通確認用の退避設定。
    embedding_backend: str = "ollama"
    hash_embedding_dimensions: int = 384

    # Ollama のモデル名と URL は .env で差し替え可能にする。
    ollama_base_url: str = "http://localhost:11434/api"
    ollama_chat_model: str = "qwen3:8b"
    ollama_embedding_model: str = "nomic-embed-text"

    chunk_size: int = 900
    chunk_overlap: int = 120
    retrieval_limit: int = 4
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    def ensure_directories(self) -> None:
        # 初回起動でも knowledge/data 配下が存在する前提にしない。
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        for directory in ("conversations", "notes", "seek"):
            (self.knowledge_dir / directory).mkdir(parents=True, exist_ok=True)

    def cors_origin_list(self) -> list[str]:
        # .env ではカンマ区切り文字列として扱い、FastAPI には list[str] で渡す。
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
