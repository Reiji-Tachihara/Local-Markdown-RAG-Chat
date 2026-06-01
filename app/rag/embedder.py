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
        """Return one embedding vector for each input text."""


class HashEmbedder:
    """Small deterministic embedding for offline indexing and smoke tests."""

    name = "hash"

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        # hash embedding は学習済みモデルではない。Ollama なしで動作確認するための簡易実装。
        vector = [0.0] * self.dimensions
        for token in _features(text):
            # token を固定長 digest にし、同じ token は毎回同じ次元へ加算されるようにする。
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0 if digest[4] % 2 else -1.0
        # コサイン類似度で比べやすいよう、ベクトルの長さを 1 に正規化する。
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


class OllamaEmbedder:
    name = "ollama"

    def __init__(self, settings: Settings) -> None:
        # 実際の HTTP 通信は OllamaClient に集約し、ここは embedding 用の薄い窓口にする。
        self.client = OllamaClient(settings)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.client.embed(texts)


def create_embedder(settings: Settings) -> Embedder:
    backend = settings.embedding_backend.lower()
    # 既定は Ollama。hash は Ollama なしで構文確認したい時の退避経路。
    if backend == "ollama":
        return OllamaEmbedder(settings)
    if backend == "hash":
        return HashEmbedder(settings.hash_embedding_dimensions)
    raise ValueError(f"Unknown embedding backend: {settings.embedding_backend}")


def _features(text: str) -> list[str]:
    # hash embedding 用の特徴量。単語と日本語にも効きやすい文字 3-gram を混ぜる。
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    words = re.findall(r"(?u)\w+", normalized)
    compact = re.sub(r"\s+", "", normalized)
    ngrams = [compact[index : index + 3] for index in range(max(len(compact) - 2, 0))]
    return words + ngrams
