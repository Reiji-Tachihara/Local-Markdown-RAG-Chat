import re


def chunk_markdown(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    """Markdown テキストを検索しやすい長さの chunk 配列に分割する。"""

    # Windows 改行 CRLF を LF に揃えると、段落分割の条件が安定する。
    cleaned = text.replace("\r\n", "\n").strip()
    if not cleaned:
        return []

    # Markdown の段落境界を優先し、長い段落だけ文字数で分割する。
    blocks = [block.strip() for block in re.split(r"\n{2,}", cleaned) if block.strip()]
    # chunks は確定済みの chunk 一覧、current は作成中の chunk。
    chunks: list[str] = []
    current = ""

    for block in blocks:
        # まず現在の chunk に段落を足しても上限以内か試す。
        candidate = f"{current}\n\n{block}".strip() if current else block
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            # 上限を超えたら現在の chunk を確定し、末尾 overlap 文字を次へ引き継ぐ。
            # overlap があると、検索時に文脈の切れ目で情報が欠けにくい。
            chunks.append(current)
            prefix = current[-overlap:].strip() if overlap else ""
            current = f"{prefix}\n\n{block}".strip() if prefix else block
        else:
            current = block

        # 1段落だけで chunk_size を超える場合は、文字数で強制分割する。
        while len(current) > chunk_size:
            chunks.append(current[:chunk_size].strip())
            start = max(chunk_size - overlap, 1)
            current = current[start:].strip()

    if current:
        chunks.append(current)
    return chunks
