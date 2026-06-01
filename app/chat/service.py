from dataclasses import asdict

from app.chat.personas import get_persona
from app.config import Settings, get_settings
from app.ollama_client import OllamaClient
from app.rag.retriever import KnowledgeRetriever, get_retriever
from app.rag.vector_store import SearchResult


class RagChatService:
    def __init__(
        self,
        settings: Settings | None = None,
        retriever: KnowledgeRetriever | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.retriever = retriever or get_retriever()

    def reply(self, message: str, persona_key: str, limit: int | None = None) -> dict:
        # 1. ペルソナを決める 2. 関連 chunk を探す 3. それを文脈として LLM に渡す。
        persona = get_persona(persona_key)
        results = self.retriever.search(message, limit)
        context = _format_context(results)
        answer = self._generate_with_ollama(message, persona.instructions, context)

        return {
            "answer": answer,
            "persona": persona.key,
            "generation_mode": "ollama",
            "contexts": [asdict(result) for result in results],
        }

    def _generate_with_ollama(self, message: str, persona_context: str, context: str) -> str:
        client = OllamaClient(self.settings)
        # RAG の根拠とユーザー入力を分離して、モデルが文脈を取り違えにくくする。
        prompt = (
            f"Markdown context:\n{context or '(no retrieved context)'}\n\n"
            f"User message:\n{message}\n\n"
            "Answer in Japanese unless the user asks otherwise. "
            "Use the Markdown context only when it is relevant."
        )
        system = (
            "You are a local RAG chat assistant. Do not use external APIs. "
            "Do not invent details unsupported by the provided context.\n\n"
            f"Persona:\n{persona_context}"
        )
        return client.generate(prompt=prompt, system=system)


def _format_context(results: list[SearchResult]) -> str:
    # LLM が出典を見失わないよう、各 chunk に source と chunk 番号を付ける。
    return "\n\n".join(
        f"Source: {result.source_path} chunk {result.chunk_index}\n{result.content}"
        for result in results
    )
