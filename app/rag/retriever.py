from functools import lru_cache
from pathlib import Path

from app.config import get_settings
from app.rag.chunker import chunk_markdown
from app.rag.embedder import Embedder, create_embedder
from app.rag.loader import MarkdownDocument, load_markdown_documents
from app.rag.vector_store import SQLiteVectorStore, SearchResult


class KnowledgeRetriever:
    """RAG の索引作成と検索を担当する中心クラス。"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.embedder: Embedder = create_embedder(self.settings)
        self.store = SQLiteVectorStore(self.settings)

    def rebuild_index(self) -> dict:
        """knowledge/ 全体を読み直して、全 Markdown の chunk と embedding を保存し直す。"""

        documents = load_markdown_documents(self.settings.knowledge_dir)
        indexed_chunks = sum(self.index_document(document) for document in documents)
        self.store.delete_missing_sources({self._relative_path(document.path) for document in documents})
        return {
            "documents": len(documents),
            "chunks": indexed_chunks,
            "embedding_backend": self.embedder.name,
        }

    def index_path(self, path: Path) -> int:
        """指定された1ファイルだけを読み直して索引に追加・更新する。"""

        return self.index_document(
            MarkdownDocument(path=path, text=path.read_text(encoding="utf-8"))
        )

    def index_document(self, document: MarkdownDocument) -> int:
        """MarkdownDocument を chunk 化し、embedding を作って SQLite に保存する。"""

        chunks = chunk_markdown(
            document.text,
            chunk_size=self.settings.chunk_size,
            overlap=self.settings.chunk_overlap,
        )
        embeddings = self.embedder.embed(chunks) if chunks else []
        return self.store.replace_document(self._relative_path(document.path), chunks, embeddings)

    def search(self, query: str, limit: int | None = None) -> list[SearchResult]:
        """検索語を embedding 化し、近い Markdown chunk を返す。"""

        [embedding] = self.embedder.embed([query])
        return self.store.search(embedding, limit or self.settings.retrieval_limit)

    def _relative_path(self, path: Path) -> str:
        """knowledge_dir から見た相対パスへ変換する。"""

        return path.relative_to(self.settings.knowledge_dir).as_posix()


@lru_cache
def get_retriever() -> KnowledgeRetriever:
    """検索処理をプロセス内で1つだけ使い回す。"""
    return KnowledgeRetriever()
