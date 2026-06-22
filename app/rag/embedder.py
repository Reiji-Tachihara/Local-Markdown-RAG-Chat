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
    """Ollama なしで動作確認するための決定的な簡易 embedder。"""

    # name は API の rebuild 結果などで、どの backend を使ったか表示するための値。
    name = "hash"

    def __init__(self, dimensions: int = 384) -> None:
        # dimensions は hash embedding のベクトル次元数。
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        # _embed_one() を各 text に対して呼び出し、ベクトル一覧を作る。
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        # hash embedding は学習済みモデルではない。Ollama なしで動作確認するための簡易実装。
        # vector は文章を数値化した配列。最初は全要素 0.0。
        vector = [0.0] * self.dimensions
        for token in _features(text):
            # token を固定長 digest にし、同じ token は毎回同じ次元へ加算されるようにする。
            # digest は token から作った固定長バイト列。
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            # index は、この token を足し込むベクトル上の位置。
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0 if digest[4] % 2 else -1.0
        # コサイン類似度で比べやすいよう、ベクトルの長さを 1 に正規化する。
        # norm はベクトルの長さ。0 でなければ 1 に正規化する。
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


class OllamaEmbedder:
    """Ollama の embedding API を使う本番用 embedder。"""

    name = "ollama"

    def __init__(self, settings: Settings) -> None:
        # 実際の HTTP 通信は OllamaClient に集約し、ここは embedding 用の薄い窓口にする。
        self.client = OllamaClient(settings)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.client.embed(texts)


def create_embedder(settings: Settings) -> Embedder:
    """settings.embedding_backend の値に応じて embedder 実装を選ぶ。"""

    # backend は .env で指定された embedding 実装名を小文字にしたもの。
    backend = settings.embedding_backend.lower()
    # 既定は Ollama。hash は Ollama なしで構文確認したい時の退避経路。
    if backend == "ollama":
        return OllamaEmbedder(settings)
    if backend == "hash":
        return HashEmbedder(settings.hash_embedding_dimensions)
    raise ValueError(f"Unknown embedding backend: {settings.embedding_backend}")


def _features(text: str) -> list[str]:
    # hash embedding 用の特徴量。単語と日本語にも効きやすい文字 3-gram を混ぜる。
    # normalized は検索しやすいよう小文字化し、空白を1つにまとめた文字列。
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    # words は英数字や日本語の単語っぽいまとまり。
    words = re.findall(r"(?u)\w+", normalized)
    # compact は空白を消した文字列。日本語の文字 n-gram を作るために使う。
    compact = re.sub(r"\s+", "", normalized)
    # ngrams は3文字ずつの特徴量。単語境界が曖昧な日本語でも少し検索しやすくする。
    ngrams = [compact[index : index + 3] for index in range(max(len(compact) - 2, 0))]
    return words + ngrams
