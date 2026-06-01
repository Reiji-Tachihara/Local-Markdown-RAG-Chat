import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import Settings


class OllamaConnectionError(RuntimeError):
    """Ollama 停止時やモデル未取得時に API 利用者へ分かりやすく返す例外。"""


class OllamaClient:
    def __init__(self, settings: Settings) -> None:
        # .env の末尾スラッシュ有無に左右されないよう正規化する。
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.chat_model = settings.ollama_chat_model
        self.embedding_model = settings.ollama_embedding_model

    def generate(self, prompt: str, system: str) -> str:
        # /api/generate は単発プロンプト向け。stream=False で最後までまとめて受け取る。
        payload = {
            "model": self.chat_model,
            "prompt": prompt,
            "system": system,
            "stream": False,
        }
        data = self._post("/generate", payload)
        return str(data.get("response", "")).strip()

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        # 新しめの Ollama API は /api/embed で複数 input を扱える。
        try:
            data = self._post("/embed", {"model": self.embedding_model, "input": texts})
            embeddings = data.get("embeddings")
            if isinstance(embeddings, list):
                return embeddings
        except OllamaConnectionError as error:
            if "404" not in str(error):
                raise

        # 古い /api/embeddings だけの環境にも寄せるため単件でフォールバックする。
        vectors: list[list[float]] = []
        for text in texts:
            data = self._post(
                "/embeddings",
                {"model": self.embedding_model, "prompt": text},
            )
            embedding = data.get("embedding")
            if not isinstance(embedding, list):
                raise OllamaConnectionError("Ollama embedding response did not contain an embedding vector.")
            vectors.append(embedding)
        return vectors

    def _post(self, path: str, payload: dict) -> dict:
        # 依存を増やさないため標準ライブラリ urllib で POST する。
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            # 404 はモデル名違いや未 pull の可能性が高い。レスポンス本文も含めて返す。
            raise OllamaConnectionError(
                f"Ollama API returned HTTP {error.code}. "
                f"Check model names and that required models are pulled. Response: {body}"
            ) from error
        except URLError as error:
            # Ollama 未起動、URL 間違い、ポート違いなどはここに入る。
            raise OllamaConnectionError(
                "Ollama API is not reachable. Start Ollama and confirm "
                f"{self.base_url} is available. Original error: {error.reason}"
            ) from error
        except TimeoutError as error:
            raise OllamaConnectionError(
                "Ollama API request timed out. Confirm Ollama is running and the model is loaded."
            ) from error
