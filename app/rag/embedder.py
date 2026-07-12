import hashlib
import math
import re
from typing import Protocol

from app.config import Settings
from app.ollama_client import OllamaClient


class Embedder(Protocol):
    # Protocol にしておくと、Ollama 以外の embedding 実装へ差し替えやすい。
    name: str

    def embed(self, texts: list[str]) -> list[list[float]]:
        """入力テキストごとに embedding ベクトルを1つ返す。"""


class HashEmbedder:
    """Ollama なしで疎通確認するための決定的な簡易 embedder。"""

    name = "hash"

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _features(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0 if digest[4] % 2 else -1.0

        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


class OllamaEmbedder:
    """Ollama の embedding API を使う本番用 embedder。"""

    name = "ollama"

    def __init__(self, settings: Settings) -> None:
        self.client = OllamaClient(settings)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.client.embed(texts)


def create_embedder(settings: Settings) -> Embedder:
    """settings.embedding_backend の値に応じて embedder 実装を選ぶ。"""

    backend = settings.embedding_backend.lower()
    if backend == "ollama":
        return OllamaEmbedder(settings)
    if backend == "hash":
        return HashEmbedder(settings.hash_embedding_dimensions)
    raise ValueError(f"Unknown embedding backend: {settings.embedding_backend}")


def _features(text: str) -> list[str]:
    """hash embedding 用に、単語特徴量と文字 3-gram 特徴量を作る。"""

    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    words = re.findall(r"(?u)\w+", normalized)
    compact = re.sub(r"\s+", "", normalized)
    ngrams = [compact[index : index + 3] for index in range(max(len(compact) - 2, 0))]
    return words + ngrams
