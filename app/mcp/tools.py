import re
from datetime import datetime, timezone
from pathlib import Path

from app.chat.personas import get_persona_context as load_persona_context
from app.config import get_settings
from app.db.database import initialize_database, list_note_records, save_note_record
from app.rag.retriever import get_retriever


def search_knowledge(query: str, top_k: int = 4) -> list[dict]:
    """Search indexed Markdown chunks by semantic similarity."""
    # MCP から呼ばれても FastAPI と同じ retriever を使うので、検索結果の意味が揃う。
    results = get_retriever().search(query, max(1, min(top_k, 20)))
    return [result.__dict__ for result in results]


def get_persona_context(persona: str) -> dict[str, str]:
    """Return instructions for one supported chat persona."""
    return load_persona_context(persona)


def save_note(title: str, content: str) -> dict:
    """Save a Markdown note and add it to the searchable index."""
    settings = get_settings()
    initialize_database(settings)

    # ノートは Markdown ファイルとして残しつつ、DB の notes テーブルにも履歴を保存する。
    note_path = _new_note_path(settings.knowledge_dir / "notes", title)
    note_path.write_text(f"# {title}\n\n{content.strip()}\n", encoding="utf-8")
    record = save_note_record(settings, title.strip(), content.strip(), note_path)
    record["indexed_chunks"] = get_retriever().index_path(note_path)
    return record


def list_notes(limit: int = 50) -> list[dict]:
    """List notes saved through the note tool."""
    settings = get_settings()
    initialize_database(settings)
    return list_note_records(settings, limit)


def _new_note_path(notes_dir: Path, title: str) -> Path:
    notes_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # ファイル名に使いにくい文字は - に寄せる。空なら note という名前にする。
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", title.strip()).strip("-").lower()
    return notes_dir / f"{timestamp}-{slug or 'note'}.md"
