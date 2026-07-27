from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MarkdownDocument:
    path: Path
    text: str


def load_markdown_documents(knowledge_dir: Path) -> list[MarkdownDocument]:
    """配下のMarkdownをUTF-8で再帰的に読み込む。"""

    return [
        MarkdownDocument(path=path, text=path.read_text(encoding="utf-8"))
        for path in sorted(knowledge_dir.rglob("*.md"))
    ]
