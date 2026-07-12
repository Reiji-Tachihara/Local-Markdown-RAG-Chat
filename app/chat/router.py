from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.chat.personas import list_persona_contexts
from app.chat.service import RagChatService
from app.config import get_settings
from app.db.chat_repository import list_chat_messages
from app.ollama_client import OllamaConnectionError
from app.rag.retriever import get_retriever


router = APIRouter()


class SearchRequest(BaseModel):
    """Markdown 検索 API のリクエスト形式。"""

    query: str = Field(min_length=1, max_length=12000)
    top_k: int = Field(default=4, ge=1, le=20)


class ChatRequest(BaseModel):
    """RAG チャット API のリクエスト形式。"""

    message: str = Field(min_length=1, max_length=12000)
    persona: str = "rational_advisor"
    top_k: int = Field(default=4, ge=1, le=20)


@router.post("/index/rebuild")
def rebuild_index() -> dict:
    """knowledge/ 配下を読み直して検索インデックスを再作成する。"""

    try:
        return get_retriever().rebuild_index()
    except OllamaConnectionError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/search")
def search_knowledge(request: SearchRequest) -> dict:
    """ユーザー入力に近い Markdown chunk を返す。"""

    try:
        results = get_retriever().search(request.query, request.top_k)
        return {"results": [result.__dict__ for result in results]}
    except OllamaConnectionError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/chat")
def chat(request: ChatRequest) -> dict:
    """検索した Markdown chunk を文脈にして Ollama で回答を生成する。"""

    try:
        return RagChatService().reply(request.message, request.persona, request.top_k)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except OllamaConnectionError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/personas")
def list_personas() -> dict:
    """UI がペルソナ一覧を表示できるように、登録済みペルソナを返す。"""

    return {"personas": list_persona_contexts()}


@router.get("/chat/history")
def chat_history(limit: int = 50) -> dict:
    """SQLite に保存されたチャット履歴を新しい順に返す。"""

    return {"messages": list_chat_messages(get_settings(), limit)}
