from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.chat.personas import list_persona_contexts
from app.chat.service import RagChatService
from app.config import get_settings
from app.db.database import list_chat_messages
from app.ollama_client import OllamaConnectionError
from app.rag.retriever import get_retriever


# router は API の住所一覧をまとめるオブジェクト。main.py で /api 配下に登録される。
router = APIRouter()


class SearchRequest(BaseModel):
    """Markdown 検索 API のリクエスト形式。"""

    # Field で入力制約を置くと、空文字や大きすぎる top_k を FastAPI が自動で弾く。
    # query は検索したい自然文。top_k は返す chunk 数。
    query: str = Field(min_length=1)
    top_k: int = Field(default=4, ge=1, le=20)


class ChatRequest(BaseModel):
    """RAG チャット API のリクエスト形式。"""

    # persona は指定なしなら相談相手を使う。
    # message はユーザー入力、top_k は RAG 文脈として使う chunk 数。
    message: str = Field(min_length=1)
    persona: str = "rational_advisor"
    top_k: int = Field(default=4, ge=1, le=20)


@router.post("/index/rebuild")
def rebuild_index() -> dict:
    """knowledge/ 配下を読み直して検索インデックスを再作成する。"""

    try:
        # get_retriever() で検索担当を取得し、rebuild_index() で索引を作り直す。
        return get_retriever().rebuild_index()
    except OllamaConnectionError as error:
        # Ollama 未起動やモデル未取得は 500 ではなく利用者が直せる 503 として返す。
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/search")
def search_knowledge(request: SearchRequest) -> dict:
    """ユーザー入力に近い Markdown chunk を返す。"""

    try:
        # API 層では検索ロジックを持たず、retriever に委譲する。
        # results は検索で見つかった Markdown chunk の一覧。
        results = get_retriever().search(request.query, request.top_k)
        # result.__dict__ は dataclass 風のオブジェクトを JSON にしやすい辞書へ変換する。
        return {"results": [result.__dict__ for result in results]}
    except OllamaConnectionError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/chat")
def chat(request: ChatRequest) -> dict:
    """検索した Markdown chunk を文脈にして Ollama で回答を生成する。"""

    try:
        # チャットの組み立ては RagChatService に集約し、router は HTTP 変換に集中する。
        # RagChatService() はチャット処理用クラスのインスタンスを作る呼び出し。
        # reply() が検索、プロンプト作成、Ollama 呼び出し、履歴保存まで行う。
        return RagChatService().reply(request.message, request.persona, request.top_k)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except OllamaConnectionError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/personas")
def list_personas() -> dict:
    """UI がペルソナ一覧を表示できるように、登録済みペルソナを返す。"""

    # list_persona_contexts() を呼ぶと、personas/*.md から読み込んだ一覧が返る。
    return {"personas": list_persona_contexts()}


@router.get("/chat/history")
def chat_history(limit: int = 50) -> dict:
    """SQLite に保存されたチャット履歴を新しい順に返す。"""

    # get_settings() で DB パスなどの設定を取り、list_chat_messages() に渡す。
    return {"messages": list_chat_messages(get_settings(), limit)}
