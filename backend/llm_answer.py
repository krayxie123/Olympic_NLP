from backend.openrouter_client import chat

def write_answer(
    question: str,
    tool_name: str,
    tool_args: dict,
    data,
    notes: list[str],
    secondary: list[dict] | None = None,
) -> str:
    sec_block = ""
    if secondary:
        sec_block = "\n\nSecondary context (for reference):\n"
        for s in secondary:
            sec_block += f"- {s.get('tool_name', '?')}: {s.get('data', [])}\n"

    prompt = f"""
You are an Olympics analytics assistant.

User question:
{question}

Primary tool used:
{tool_name} args={tool_args}

Computed results (data):
{data}
{sec_block}

Notes to mention if relevant:
{notes}

Write a concise answer (2–6 sentences):
- use the computed numbers from primary (and secondary if helpful)
- be clear if counts are athlete-level
""".strip()

    return chat([{"role": "user", "content": prompt}], temperature=0.2, max_tokens=250)