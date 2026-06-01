from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MarkdownDocument:
    # path はあとで検索結果に「どのファイル由来か」を出すために保持する。
    path: Path
    # text は Markdown ファイルの中身そのもの。chunk 化の入力になる。
    text: str


def load_markdown_documents(knowledge_dir: Path) -> list[MarkdownDocument]:
    # knowledge_dir 配下を再帰的に探すので、サブフォルダを自由に増やせる。
    documents: list[MarkdownDocument] = []
    for path in sorted(knowledge_dir.rglob("*.md")):
        # Markdown は日本語を扱う前提なので UTF-8 固定で読む。
        documents.append(
            MarkdownDocument(
                path=path,
                text=path.read_text(encoding="utf-8"),
            )
        )
    return documents
