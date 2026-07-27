import re


def chunk_markdown(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    """Markdown テキストを検索しやすい長さの chunk 配列に分割する。"""

    cleaned = text.replace("\r\n", "\n").strip()
    if not cleaned:
        return []

    # Markdown の段落境界を優先し、長い段落だけ文字数で分割する。
    blocks = [block.strip() for block in re.split(r"\n{2,}", cleaned) if block.strip()]
    chunks: list[str] = []
    current = ""

    for block in blocks:
        candidate = f"{current}\n\n{block}".strip() if current else block
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            # overlap があると、検索時に文脈の切れ目で情報が欠けにくい。
            chunks.append(current)
            prefix = current[-overlap:].strip() if overlap else ""
            current = f"{prefix}\n\n{block}".strip() if prefix else block
        else:
            current = block

        while len(current) > chunk_size:
            chunks.append(current[:chunk_size].strip())
            start = max(chunk_size - overlap, 1)
            current = current[start:].strip()

    if current:
        chunks.append(current)
    return chunks
