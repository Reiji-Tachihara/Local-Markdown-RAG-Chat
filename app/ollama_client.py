import json
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import Settings


class OllamaConnectionError(RuntimeError):
    """Ollama 停止時やモデル未取得時に、利用者へ分かりやすく返す例外。"""


class OllamaClient:
    """Ollama の HTTP API を呼び出すための最小クライアント。"""

    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.chat_model = settings.ollama_chat_model
        self.embedding_model = settings.ollama_embedding_model
        self.timeout = settings.ollama_request_timeout

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
            if "HTTP 404" not in str(error):
                raise

        vectors: list[list[float]] = []
        for text in texts:
            data = self._post(
                "/embeddings",
                {"model": self.embedding_model, "prompt": text},
            )
            embedding = data.get("embedding")
            if not isinstance(embedding, list):
                raise OllamaConnectionError("Ollama の embedding レスポンスにベクトルが含まれていません。")
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
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise OllamaConnectionError(
                f"Ollama API が HTTP {error.code} を返しました。"
                f"モデル名と pull 済みかを確認してください。レスポンス: {body}"
            ) from error
        except URLError as error:
            raise OllamaConnectionError(
                "Ollama API に接続できません。Ollama が起動しているか、"
                f"{self.base_url} にアクセスできるか確認してください。詳細: {error.reason}"
            ) from error
        except (TimeoutError, socket.timeout) as error:
            raise OllamaConnectionError(
                f"Ollama API の応答が {self.timeout} 秒以内に返りませんでした。"
                "長い質問の場合は短く分けるか、OLLAMA_REQUEST_TIMEOUT を増やしてください。"
            ) from error
