import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone

from app.config import Settings
from app.db.database import connect


@dataclass(frozen=True)
class SearchResult:
    # source_path と chunk_index があれば、検索結果の出典を後から辿れる。
    source_path: str
    chunk_index: int
    content: str
    # score はコサイン類似度。1 に近いほど query と近い。
    score: float


class SQLiteVectorStore:
    """SQLite に chunk と embedding を保存し、類似検索する簡易ベクトルストア。"""

    def __init__(self, settings: Settings) -> None:
        # settings.database_path から SQLite の保存先を得る。
        self.settings = settings

    def replace_document(
        self,
        source_path: str,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> int:
        """1つの Markdown ファイル由来の chunk を DB 内で丸ごと入れ替える。"""

        timestamp = datetime.now(timezone.utc).isoformat()
        with connect(self.settings) as connection:
            # ファイル単位で入れ替える。更新前の古い chunk を残さないため。
            connection.execute("DELETE FROM chunks WHERE source_path = ?", (source_path,))
            connection.executemany(
                """
                INSERT INTO chunks(
                    source_path, chunk_index, content, embedding, checksum, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        source_path,
                        index,
                        content,
                        # SQLite にはベクトル型がないので JSON 文字列として保存する。
                        json.dumps(embedding),
                        hashlib.sha256(content.encode("utf-8")).hexdigest(),
                        timestamp,
                    )
                    for index, (content, embedding) in enumerate(zip(chunks, embeddings))
                ],
            )
        return len(chunks)

    def delete_missing_sources(self, source_paths: set[str]) -> None:
        """現在存在しない Markdown ファイル由来の古い chunk を削除する。"""

        with connect(self.settings) as connection:
            if not source_paths:
                # knowledge/ に Markdown が1つもない時は索引を空にする。
                connection.execute("DELETE FROM chunks")
                return
            # 今回読み込めたファイル以外の chunk は、削除済みファイル由来として消す。
            placeholders = ",".join("?" for _ in source_paths)
            connection.execute(
                f"DELETE FROM chunks WHERE source_path NOT IN ({placeholders})",
                tuple(sorted(source_paths)),
            )

    def search(self, query_embedding: list[float], limit: int) -> list[SearchResult]:
        """query embedding と保存済み embedding を比較し、近い順に返す。"""

        with connect(self.settings) as connection:
            # 最小構成なので全件を Python 側で比較する。大規模化したら専用ベクトルDBへ移す。
            rows = connection.execute(
                "SELECT source_path, chunk_index, content, embedding FROM chunks"
            ).fetchall()

        # 各 chunk の embedding と query embedding のコサイン類似度を計算する。
        results = [
            SearchResult(
                source_path=row["source_path"],
                chunk_index=row["chunk_index"],
                content=row["content"],
                score=_cosine_similarity(query_embedding, json.loads(row["embedding"])),
            )
            for row in rows
        ]
        results.sort(key=lambda result: result.score, reverse=True)
        return results[: max(1, limit)]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    """2つのベクトルのコサイン類似度を計算する。"""

    if len(left) != len(right):
        # embedding モデルを途中で変えた場合など、次元数が違うデータは比較できない。
        return -1.0
    dot = sum(left_value * right_value for left_value, right_value in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)
