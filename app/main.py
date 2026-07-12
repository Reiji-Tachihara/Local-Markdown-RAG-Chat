from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.chat.router import router as chat_router
from app.config import get_settings
from app.db.schema import initialize_database
from app.ollama_client import OllamaConnectionError
from app.rag.retriever import get_retriever


@asynccontextmanager
async def lifespan(_: FastAPI):
    # settings という変数に、.env と既定値から読み込んだ設定を入れる。
    settings = get_settings()
    # initialize_database 関数を呼び出して、SQLite に必要なテーブルを用意する。
    initialize_database(settings)
    # Ollama 未起動でも API 自体は立ち上げ、実行時に 503 を返せるようにする。
    try:
        # get_retriever() で検索担当オブジェクトを取得し、rebuild_index() で Markdown を索引化する。
        get_retriever().rebuild_index()
    except OllamaConnectionError:
        pass
    yield


# settings は、このファイル全体で使うアプリ設定。
settings = get_settings()

# app は FastAPI アプリ本体。uvicorn はこの変数を見つけてサーバとして起動する。
app = FastAPI(title=settings.app_name, lifespan=lifespan)
# add_middleware は、React から FastAPI を呼べるように CORS 設定を追加する関数呼び出し。
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# include_router は、app/chat/router.py に書いた API たちを /api 配下に登録する関数呼び出し。
app.include_router(chat_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    # health は疎通確認用の関数。サーバが動いていれば {"status": "ok"} を返す。
    return {"status": "ok"}
