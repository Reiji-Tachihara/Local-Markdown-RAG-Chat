from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.chat.personas import PERSONAS, get_persona_context
from app.chat.service import RagChatService
from app.ollama_client import OllamaConnectionError
from app.rag.retriever import get_retriever


router = APIRouter()


class SearchRequest(BaseModel):
    # Field で入力制約を置くと、空文字や大きすぎる top_k を FastAPI が自動で弾く。
    query: str = Field(min_length=1)
    top_k: int = Field(default=4, ge=1, le=20)


class ChatRequest(BaseModel):
    # persona は指定なしなら合理的な相談相手を使う。
    message: str = Field(min_length=1)
    persona: str = "rational_advisor"
    top_k: int = Field(default=4, ge=1, le=20)


@router.post("/index/rebuild")
def rebuild_index() -> dict:
    try:
        return get_retriever().rebuild_index()
    except OllamaConnectionError as error:
        # Ollama 未起動やモデル未取得は 500 ではなく利用者が直せる 503 として返す。
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/search")
def search_knowledge(request: SearchRequest) -> dict:
    try:
        # API 層では検索ロジックを持たず、retriever に委譲する。
        results = get_retriever().search(request.query, request.top_k)
        return {"results": [result.__dict__ for result in results]}
    except OllamaConnectionError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/chat")
def chat(request: ChatRequest) -> dict:
    try:
        # チャットの組み立ては RagChatService に集約し、router は HTTP 変換に集中する。
        return RagChatService().reply(request.message, request.persona, request.top_k)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except OllamaConnectionError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/personas")
def list_personas() -> dict:
    return {"personas": [get_persona_context(key) for key in PERSONAS]}
