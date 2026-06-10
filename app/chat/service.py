from dataclasses import asdict

from app.chat.personas import get_persona
from app.config import Settings, get_settings
from app.db.database import save_chat_message
from app.ollama_client import OllamaClient
from app.rag.retriever import KnowledgeRetriever, get_retriever
from app.rag.vector_store import SearchResult


class RagChatService:
    """検索、プロンプト作成、Ollama 呼び出しをまとめるチャット用サービス。"""

    def __init__(
        self,
        settings: Settings | None = None,
        retriever: KnowledgeRetriever | None = None,
    ) -> None:
        # settings と retriever を引数で受け取れるようにして、テスト時に差し替えやすくする。
        self.settings = settings or get_settings()
        self.retriever = retriever or get_retriever()

    def reply(self, message: str, persona_key: str, limit: int | None = None) -> dict:
        """ユーザー入力に対して、RAG 検索結果つきのチャット応答を返す。"""

        # 1. ペルソナを決める 2. 関連 chunk を探す 3. それを文脈として LLM に渡す。
        persona = get_persona(persona_key)
        # results は RAG の参照元として UI にも返す。
        results = self.retriever.search(message, limit)
        context = _format_context(results)
        answer = self._generate_with_ollama(message, persona.instructions, context)
        context_dicts = [asdict(result) for result in results]

        # ユーザー発言と assistant 応答の両方を SQLite に保存する。
        user_record = save_chat_message(
            self.settings,
            role="user",
            content=message,
            persona=persona.key,
            contexts=[],
        )
        assistant_record = save_chat_message(
            self.settings,
            role="assistant",
            content=answer,
            persona=persona.key,
            contexts=context_dicts,
        )

        return {
            "answer": answer,
            "persona": persona.key,
            "generation_mode": "ollama",
            "contexts": context_dicts,
            "message_ids": {
                "user": user_record["id"],
                "assistant": assistant_record["id"],
            },
        }

    def _generate_with_ollama(self, message: str, persona_context: str, context: str) -> str:
        """Ollama に渡す system/prompt を組み立て、LLM の回答文字列を返す。"""

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
    """検索結果を LLM に渡しやすいテキスト形式へ変換する。"""

    # LLM が出典を見失わないよう、各 chunk に source と chunk 番号を付ける。
    return "\n\n".join(
        f"Source: {result.source_path} chunk {result.chunk_index}\n{result.content}"
        for result in results
    )
