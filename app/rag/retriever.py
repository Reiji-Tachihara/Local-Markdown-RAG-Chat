from functools import lru_cache
from pathlib import Path

from app.config import get_settings
from app.db.database import initialize_database
from app.rag.chunker import chunk_markdown
from app.rag.embedder import Embedder, create_embedder
from app.rag.loader import MarkdownDocument, load_markdown_documents
from app.rag.vector_store import SQLiteVectorStore, SearchResult


class KnowledgeRetriever:
    def __init__(self) -> None:
        # retriever は「設定」「DB」「embedding」「検索ストア」を束ねる入口。
        self.settings = get_settings()
        initialize_database(self.settings)
        self.embedder: Embedder = create_embedder(self.settings)
        self.store = SQLiteVectorStore(self.settings)

    def rebuild_index(self) -> dict:
        # knowledge/ 配下の Markdown を全て読み直し、DB 内の chunk を作り直す。
        documents = load_markdown_documents(self.settings.knowledge_dir)
        indexed_chunks = sum(self.index_document(document) for document in documents)
        # 削除済み Markdown の古い chunk が検索に残らないよう掃除する。
        self.store.delete_missing_sources({self._relative_path(document.path) for document in documents})
        return {
            "documents": len(documents),
            "chunks": indexed_chunks,
            "embedding_backend": self.embedder.name,
        }

    def index_path(self, path: Path) -> int:
        # save_note など、1ファイルだけ追加された時に使う軽量な再索引。
        return self.index_document(
            MarkdownDocument(path=path, text=path.read_text(encoding="utf-8"))
        )

    def index_document(self, document: MarkdownDocument) -> int:
        # Markdown -> chunk -> embedding -> SQLite 保存、という RAG の準備処理。
        chunks = chunk_markdown(
            document.text,
            chunk_size=self.settings.chunk_size,
            overlap=self.settings.chunk_overlap,
        )
        embeddings = self.embedder.embed(chunks) if chunks else []
        return self.store.replace_document(self._relative_path(document.path), chunks, embeddings)

    def search(self, query: str, limit: int | None = None) -> list[SearchResult]:
        # ユーザー入力も同じ embedding 空間へ変換して、保存済み chunk と比較する。
        [embedding] = self.embedder.embed([query])
        return self.store.search(embedding, limit or self.settings.retrieval_limit)

    def _relative_path(self, path: Path) -> str:
        # 絶対パスではなく knowledge/ からの相対パスを保存し、環境差を小さくする。
        return path.relative_to(self.settings.knowledge_dir).as_posix()


@lru_cache
def get_retriever() -> KnowledgeRetriever:
    # FastAPI の各リクエストで毎回初期化しないよう、プロセス内で1つだけ使い回す。
    return KnowledgeRetriever()
