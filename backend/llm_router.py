import json
import re
from backend.tool_registry import TOOLS
from backend.openrouter_client import chat

def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError(f"Model did not return JSON. Got: {text[:200]}")
    return json.loads(m.group(0))

def choose_tools(question: str) -> dict:
    """LLM picks 1-3 tools: one primary (main focus) and 0-2 secondary (context)."""
    tool_list = "\n".join(
        [f"- {name}: args={meta['args_schema']}" for name, meta in TOOLS.items()]
    )

    prompt = f"""
You are a routing engine for an Olympics analytics dashboard.

Pick 1-4 tools. One must be "primary" (main answer). Others are "secondary" (suggest up to 3 complementary charts/tables).

Allowed tools:
{tool_list}

Return JSON only. No markdown.
{{
  "tools": [
    {{ "tool_name": "medals_over_time", "arguments": {{"country": "China", "medal_type": "Gold", "start_year": 1992, "end_year": 2012}}, "role": "primary" }},
    {{ "tool_name": "medal_rate", "arguments": {{"year": 2008, "country": "China"}}, "role": "secondary" }},
    {{ "tool_name": "compare_countries_radar", "arguments": {{"year": 2008, "countries": ["United States", "China", "Russia"]}}, "role": "secondary" }}
  ]
}}

Rules:
- primary: direct answer to the question (trend, top, rate, etc.).
- secondary: suggest 2-3 complementary visualizations. If primary focuses on a country (e.g. Canada), include that country in compare_countries_radar.
- max 4 tools total (1 primary + up to 3 secondary).
- country: use full name (United States not USA, China not PRC).
- year defaults: 2008 for single-year tools; 1992-2012 for trends if unspecified.
- "winter olympics" / "winter games": use year 2014 (dataset typically ends 2016) AND season: "Winter".
- "summer olympics": use season: "Summer" if distinguishing.

Routing:
- "trend", "over time" -> medals_over_time (primary). Add season: "Winter" when "winter" mentioned. Add sport filter if sport mentioned.
- "compare", "vs", "versus", "canada vs america" -> compare_countries_over_time (primary) for trends, or compare_countries_radar for single-year. Use medal_type from question (Silver, Gold, Bronze). "America" = United States.
- "top", "rank", "most medals" -> top_countries_by_medals or top_countries_by_sport (if sport mentioned). Suggest compare_countries_radar, medal_rate as secondary.
- "percentage", "rate" -> medal_rate (primary).
- "participants", "how many athletes" -> participant_count. Add country/sport if specified.
- "by sport", "table tennis", "swimming" -> top_countries_by_sport or sport_leaders or medals_by_sport.
- "total medals", "all medals" -> total_medals_by_year.

User question: {question}
""".strip()

    raw = chat([{"role": "user", "content": prompt}], temperature=0.0, max_tokens=600)
    parsed = _extract_json(raw)

    # Deduplicate tools (same tool_name + args)
    if "tools" in parsed:
        seen = set()
        unique = []
        for t in parsed["tools"]:
            key = (t.get("tool_name"), str(sorted((t.get("arguments") or {}).items())))
            if key not in seen:
                seen.add(key)
                unique.append(t)
        parsed["tools"] = unique

    # Backward compat: if old format {tool_name, arguments}, wrap in tools list
    if "tools" not in parsed and "tool_name" in parsed:
        parsed = {"tools": [{"tool_name": parsed["tool_name"], "arguments": parsed["arguments"], "role": "primary"}]}
    return parsed