import re
from datetime import datetime, timezone
from pathlib import Path

from app.chat.personas import get_persona_context as load_persona_context
from app.config import get_settings
from app.db.note_repository import list_note_records, save_note_record
from app.db.schema import initialize_database
from app.rag.retriever import get_retriever


def search_knowledge(query: str, top_k: int = 4) -> list[dict]:
    """索引化済み Markdown chunk を意味的な近さで検索する。"""

    results = get_retriever().search(query, max(1, min(top_k, 20)))
    return [result.__dict__ for result in results]


def get_persona_context(persona: str) -> dict[str, str]:
    """指定されたペルソナの指示文を返す。"""

    return load_persona_context(persona)


def save_note(title: str, content: str) -> dict:
    """Markdown ノートを保存し、検索インデックスにも追加する。"""

    settings = get_settings()
    initialize_database(settings)

    note_path = _new_note_path(settings.knowledge_dir / "notes", title)
    note_path.write_text(f"# {title}\n\n{content.strip()}\n", encoding="utf-8")
    record = save_note_record(settings, title.strip(), content.strip(), note_path)
    record["indexed_chunks"] = get_retriever().index_path(note_path)
    return record


def list_notes(limit: int = 50) -> list[dict]:
    """ノート保存 tool で保存されたノート一覧を返す。"""

    settings = get_settings()
    initialize_database(settings)
    return list_note_records(settings, limit)


def _new_note_path(notes_dir: Path, title: str) -> Path:
    """ノートタイトルと現在時刻から衝突しにくい Markdown ファイル名を作る。"""

    notes_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", title.strip()).strip("-").lower()
    return notes_dir / f"{timestamp}-{slug or 'note'}.md"
