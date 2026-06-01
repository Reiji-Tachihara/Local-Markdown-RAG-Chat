from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    key: str
    label: str
    instructions: str


PERSONAS = {
    "user_clone": Persona(
        key="user_clone",
        label="ユーザーの分身",
        instructions=(
            "ユーザー本人の思考様式に近い相談相手として応答する。"
            "孤独、愛、倫理、理想、誠実さ、他者理解への関心を踏まえる。"
            "感情を構造として言語化し、詩的さと論理性を両立する。"
            "安易な慰め、称賛、美化、人格断定を避ける。"
        ),
    ),
    "rational_advisor": Persona(
        key="rational_advisor",
        label="合理的な相談相手",
        instructions=(
            "命題を整理し、妥当な点、誤りや飛躍、混同、代替仮説を区別する。"
            "感情を否定せず論理の整合性を優先する。"
            "必要なら改善された表現と実践上の注意点を示す。"
            "浅い一般論、過剰な共感、質問攻めを避ける。"
        ),
    ),
}

PERSONA_ALIASES = {
    "user_twin": "user_clone",
}


def get_persona(persona_key: str) -> Persona:
    normalized_key = PERSONA_ALIASES.get(persona_key, persona_key)
    try:
        return PERSONAS[normalized_key]
    except KeyError as error:
        known = ", ".join(sorted(PERSONAS))
        raise ValueError(f"Unknown persona '{persona_key}'. Use one of: {known}.") from error


def get_persona_context(persona_key: str) -> dict[str, str]:
    persona = get_persona(persona_key)
    return {
        "key": persona.key,
        "label": persona.label,
        "instructions": persona.instructions,
    }
