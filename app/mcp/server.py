from mcp.server.fastmcp import FastMCP

from app.mcp import tools


mcp = FastMCP("local-markdown-rag")


@mcp.tool()
def search_knowledge(query: str, top_k: int = 4) -> list[dict]:
    """Search local Markdown knowledge chunks."""
    return tools.search_knowledge(query, top_k)


@mcp.tool()
def get_persona_context(persona: str) -> dict[str, str]:
    """Get instructions for user_clone or rational_advisor."""
    return tools.get_persona_context(persona)


@mcp.tool()
def save_note(title: str, content: str) -> dict:
    """Save a Markdown note under knowledge/notes and index it."""
    return tools.save_note(title, content)


@mcp.tool()
def list_notes(limit: int = 50) -> list[dict]:
    """List notes created through save_note."""
    return tools.list_notes(limit)


if __name__ == "__main__":
    mcp.run()
