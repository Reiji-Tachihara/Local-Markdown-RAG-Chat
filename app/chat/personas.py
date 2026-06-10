from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Persona:
    """LLM に渡すペルソナ定義。"""

    # key は API や UI で指定する識別子。
    key: str
    # label は人間向けに表示する名前。
    label: str
    # instructions は system prompt に入る振る舞いの指示。
    instructions: str


# PERSONA_DIR はペルソナ Markdown を置くディレクトリ。
PERSONA_DIR = Path("personas")

# 古い名前や別名を受け付けるための変換表。
PERSONA_ALIASES = {
    "user_twin": "user_clone",
}


@lru_cache
def load_personas() -> dict[str, Persona]:
    """personas/*.md を読み込み、Persona の辞書として返す。"""

    personas: dict[str, Persona] = {}
    for path in sorted(PERSONA_DIR.glob("*.md")):
        persona = _load_persona_markdown(path)
        personas[persona.key] = persona
    return personas


def get_persona(persona_key: str) -> Persona:
    """指定された key または alias から Persona を取得する。"""

    normalized_key = PERSONA_ALIASES.get(persona_key, persona_key)
    personas = load_personas()
    try:
        return personas[normalized_key]
    except KeyError as error:
        known = ", ".join(sorted(personas))
        raise ValueError(f"Unknown persona '{persona_key}'. Use one of: {known}.") from error


def get_persona_context(persona_key: str) -> dict[str, str]:
    """API/MCP で返しやすい dict 形式に Persona を変換する。"""

    persona = get_persona(persona_key)
    return {
        "key": persona.key,
        "label": persona.label,
        "instructions": persona.instructions,
    }


def list_persona_contexts() -> list[dict[str, str]]:
    """全ペルソナを API/MCP で返しやすい dict の一覧に変換する。"""

    return [get_persona_context(key) for key in load_personas()]


def _load_persona_markdown(path: Path) -> Persona:
    """1つの Markdown ファイルから key/label/instructions を読み取る。"""

    key = path.stem
    text = path.read_text(encoding="utf-8").strip()
    label = key
    instruction_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("label:"):
            label = line.removeprefix("label:").strip()
            continue
        if line.startswith("#"):
            continue
        instruction_lines.append(line)

    instructions = "\n".join(instruction_lines).strip()
    return Persona(key=key, label=label, instructions=instructions)
