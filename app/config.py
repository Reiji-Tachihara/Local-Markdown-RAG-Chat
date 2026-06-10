from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリ全体の設定を .env と既定値から読み込むクラス。"""

    # pydantic-settings に .env を読ませるための設定。
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # FastAPI のタイトルや、ローカルファイルの置き場所。
    app_name: str = "Local Markdown RAG Chat"
    knowledge_dir: Path = Path("knowledge")
    data_dir: Path = Path("data")
    database_path: Path = Path("data/app.db")

    # 既定では Ollama embedding を使う。hash は疎通確認用の退避設定。
    embedding_backend: str = "ollama"
    hash_embedding_dimensions: int = 384

    # Ollama のモデル名と URL は .env で差し替え可能にする。
    ollama_base_url: str = "http://localhost:11434/api"
    # True の場合、Ollama URL は localhost / 127.0.0.1 / ::1 のみ許可する。
    enforce_local_ollama: bool = True
    ollama_chat_model: str = "qwen3:8b"
    ollama_embedding_model: str = "nomic-embed-text"

    # chunk_size は1つの検索単位の長さ、chunk_overlap は前後の文脈を少し重ねる幅。
    chunk_size: int = 900
    chunk_overlap: int = 120
    # retrieval_limit は検索で返す chunk 数の既定値。
    retrieval_limit: int = 4
    # React/Vite など、ブラウザから API を呼ぶ元 URL を限定する。
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

    def validate_local_only(self) -> None:
        """外部公開につながる設定を早い段階で検出する。"""

        if not self.enforce_local_ollama:
            return

        parsed = urlparse(self.ollama_base_url)
        allowed_hosts = {"localhost", "127.0.0.1", "::1"}
        if parsed.hostname not in allowed_hosts:
            raise ValueError(
                "OLLAMA_BASE_URL must point to localhost when ENFORCE_LOCAL_OLLAMA=true. "
                f"Current value: {self.ollama_base_url}"
            )


@lru_cache
def get_settings() -> Settings:
    """設定を1回だけ作り、以後は同じ Settings を使い回す。"""

    settings = Settings()
    settings.validate_local_only()
    settings.ensure_directories()
    return settings
