from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.chat.router import router as chat_router
from app.config import get_settings
from app.db.database import initialize_database
from app.ollama_client import OllamaConnectionError
from app.rag.retriever import get_retriever


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    initialize_database(settings)
    # Ollama 未起動でも API 自体は立ち上げ、実行時に 503 を返せるようにする。
    try:
        get_retriever().rebuild_index()
    except OllamaConnectionError:
        pass
    yield


settings = get_settings()

app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
