from mcp.server.fastmcp import FastMCP

from app.mcp import tools


mcp = FastMCP("local-markdown-rag")


@mcp.tool()
def search_knowledge(query: str, top_k: int = 4) -> list[dict]:
    """ローカル Markdown 知識 chunk を検索する。"""
    return tools.search_knowledge(query, top_k)


@mcp.tool()
def get_persona_context(persona: str) -> dict[str, str]:
    """user_clone または rational_advisor の指示文を取得する。"""
    return tools.get_persona_context(persona)


@mcp.tool()
def save_note(title: str, content: str) -> dict:
    """Markdown ノートを knowledge/notes に保存し、インデックスに追加する。"""
    return tools.save_note(title, content)


@mcp.tool()
def list_notes(limit: int = 50) -> list[dict]:
    """save_note で作成されたノート一覧を返す。"""
    return tools.list_notes(limit)


if __name__ == "__main__":
    mcp.run()
