import inspect
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.tool_registry import TOOLS
from backend.llm_router import choose_tools
from backend.llm_answer import write_answer

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

@app.get("/health")
def health():
    return {"ok": True}

COUNTRY_ALIASES = {
    "america": "United States",
    "usa": "United States",
    "u.s.a.": "United States",
    "us": "United States",
    "united states of america": "United States",
    "great britain": "United Kingdom",
    "britain": "United Kingdom",
    "uk": "United Kingdom",
    "russian federation": "Russia",
    "people's republic of china": "China",
}

def _normalize_country(name: str) -> str:
    if not name or not isinstance(name, str):
        return name
    k = name.strip().lower()
    return COUNTRY_ALIASES.get(k, name.strip())

def _normalize_args(tool_name: str, args: dict, question: str = "") -> dict:
    """Fill defaults and fix common LLM arg naming for each tool."""
    args = dict(args or {})

    # Ensure countries is a list (before normalization)
    if "countries" in args:
        if isinstance(args["countries"], str):
            args["countries"] = [c.strip() for c in args["countries"].split(",") if c.strip()]

    # Country name normalization (America -> United States, etc.)
    if "country" in args and args["country"]:
        args["country"] = _normalize_country(args["country"])
    if "countries" in args and args["countries"]:
        args["countries"] = [_normalize_country(str(c)) for c in args["countries"]]

    # Common aliases (LLM may use camelCase)
    for old, new in [("medalType", "medal_type"), ("startYear", "start_year"), ("endYear", "end_year")]:
        if old in args and new not in args:
            args[new] = args.pop(old)

    # Pad countries if fewer than 2 for comparison tools
    if "countries" in args and isinstance(args["countries"], list) and len(args["countries"]) < 2 and tool_name in ("compare_countries_over_time", "compare_countries_radar"):
            extra = ["United States", "China", "Russia"]
            args["countries"] = list(args["countries"]) + [c for c in extra if c not in args["countries"]][: 2]

    tool_defaults = {
        "top_countries_by_medals": {"year": 2008, "medal_type": "Gold", "n": 10},
        "medal_rate": {"year": 2008},
        "medals_over_time": {"medal_type": "Gold", "start_year": 1992, "end_year": 2012},
        "top_countries_by_sport": {"year": 2008, "medal_type": "Gold", "n": 10},
        "participant_count": {"year": 2008},
        "sport_leaders": {"year": 2008, "n": 5},
        "total_medals_by_year": {"start_year": 1992, "end_year": 2012},
        "compare_countries_over_time": {"countries": ["United States", "China", "Russia"], "medal_type": "Gold", "start_year": 1992, "end_year": 2012},
        "compare_countries_radar": {"year": 2008, "countries": ["United States", "China", "Russia"]},
    }
    defaults = tool_defaults.get(tool_name, {})
    for k, v in defaults.items():
        if k not in args or args[k] is None:
            args[k] = v

    q = (question or "").lower()

    # Medal type from question if specified (override defaults for compare queries)
    if "silver" in q:
        args["medal_type"] = "Silver"
    elif "bronze" in q:
        args["medal_type"] = "Bronze"

    # Winter Olympics: 1992,1994,1998,2002,2006,2010,2014. Dataset often ends at 2016, so use 2014 not 2018
    season_val = (args.get("season") or "").strip().lower()
    if "winter" in q or season_val == "winter":
        args["season"] = "Winter"
        year = args.get("year")
        summer_only = {1996, 2000, 2004, 2008, 2012, 2016}
        if not year or year in summer_only or year > 2016:
            args["year"] = 2014

    return args


def _run_tool(tool_name: str, args: dict, question: str = ""):
    """Run a single tool and return data + chart. Returns None on error."""
    if tool_name not in TOOLS:
        return None
    args = _normalize_args(tool_name, args, question)
    tool_fn = TOOLS[tool_name]["fn"]
    sig = inspect.signature(tool_fn)
    valid_params = {p for p in sig.parameters if p != "self"}
    tool_args = {k: v for k, v in args.items() if k in valid_params}
    data = tool_fn(**tool_args)
    chart = TOOLS[tool_name]["chart_builder"](data, args)
    return {"tool_name": tool_name, "tool_args": args, "data": data, "chart": chart}

@app.post("/query")
def query(req: QueryRequest):
    choice = choose_tools(req.question)
    tools_list = choice.get("tools", [])

    if not tools_list:
        return {"error": "No tools selected", "choice": choice}

    results = []
    for t in tools_list:
        tool_name = t.get("tool_name")
        args = t.get("arguments", {})
        role = t.get("role", "primary")

        if tool_name not in TOOLS:
            continue
        out = _run_tool(tool_name, args, question=req.question)
        if out:
            out["role"] = role
            results.append(out)

    if not results:
        return {"error": "All tools failed", "choice": choice}

    primary = next((r for r in results if r["role"] == "primary"), results[0])
    secondary = [r for r in results if r["role"] == "secondary"]

    notes = [
        "Counts are athlete-level medal rows (team sports inflate totals).",
        "Medal rate is athlete-level: medal_rows / participants.",
    ]
    answer = write_answer(
        req.question,
        primary["tool_name"],
        primary["tool_args"],
        primary["data"],
        notes,
        secondary=[{"tool_name": s["tool_name"], "data": s["data"], "args": s["tool_args"]} for s in secondary],
    )

    return {
        "answer": answer,
        "primary": {
            "tool_used": primary["tool_name"],
            "tool_args": primary["tool_args"],
            "data": primary["data"],
            "chart": primary["chart"],
        },
        "secondary": [
            {"tool_used": s["tool_name"], "tool_args": s["tool_args"], "data": s["data"], "chart": s["chart"]}
            for s in secondary
        ],
        "notes": notes,
    }