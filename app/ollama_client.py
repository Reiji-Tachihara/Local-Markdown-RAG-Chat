import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import Settings


class OllamaConnectionError(RuntimeError):
    """Ollama 停止時やモデル未取得時に、API 利用者へ分かりやすく返す例外。"""


class OllamaClient:
    """Ollama の HTTP API を呼び出すための最小クライアント。"""

    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.chat_model = settings.ollama_chat_model
        self.embedding_model = settings.ollama_embedding_model

    def generate(self, prompt: str, system: str) -> str:
        """Ollama の /generate を呼び出し、チャット回答を1つ返す。"""

        payload = {
            "model": self.chat_model,
            "prompt": prompt,
            "system": system,
            "stream": False,
        }
        data = self._post("/generate", payload)
        return str(data.get("response", "")).strip()

    def embed(self, texts: list[str]) -> list[list[float]]:
        """複数テキストを embedding ベクトルへ変換する。"""

        if not texts:
            return []

        try:
            data = self._post("/embed", {"model": self.embedding_model, "input": texts})
            embeddings = data.get("embeddings")
            if isinstance(embeddings, list):
                return embeddings
        except OllamaConnectionError as error:
            if "404" not in str(error):
                raise

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
        """Ollama API に JSON POST し、JSON レスポンスを dict として返す。"""

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
            raise OllamaConnectionError(
                f"Ollama API returned HTTP {error.code}. "
                f"Check model names and that required models are pulled. Response: {body}"
            ) from error
        except URLError as error:
            raise OllamaConnectionError(
                "Ollama API is not reachable. Start Ollama and confirm "
                f"{self.base_url} is available. Original error: {error.reason}"
            ) from error
        except TimeoutError as error:
            raise OllamaConnectionError(
                "Ollama API request timed out. Confirm Ollama is running and the model is loaded."
            ) from error
