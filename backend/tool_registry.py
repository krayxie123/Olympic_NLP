from backend.tools import (
    top_countries_by_medals,
    medal_rate,
    medals_over_time,
    top_countries_by_sport,
    participant_count,
    medals_by_sport,
    sport_leaders,
    total_medals_by_year,
    compare_countries_over_time,
    compare_countries_radar,
)
from backend.charts import (
    bar_chart_top_countries,
    bar_chart_sport_breakdown,
    indicator_medal_rate,
    indicator_participants,
    line_chart_trend,
    line_chart_comparison,
    radar_chart_countries,
)

TOOLS = {
    "top_countries_by_medals": {
        "fn": top_countries_by_medals,
        "args_schema": {"year": "int", "medal_type": "str (Gold|Silver|Bronze)", "n": "int", "season": "str|null (Summer|Winter)"},
        "chart_builder": lambda data, a: bar_chart_top_countries(
            f"Top {a['n']} countries by {a['medal_type']} ({a['year']})"
            + (f" - {a.get('season', '')}" if a.get("season") else ""),
            data,
        ),
    },
    "medal_rate": {
        "fn": medal_rate,
        "args_schema": {"year": "int", "country": "str|null"},
        "chart_builder": lambda data, a: indicator_medal_rate("Medal rate (athlete-level)", data),
    },
    "medals_over_time": {
        "fn": medals_over_time,
        "args_schema": {
            "country": "str",
            "medal_type": "str (Gold|Silver|Bronze)",
            "start_year": "int",
            "end_year": "int",
            "sport": "str|null",
            "season": "str|null (Winter|Summer)",
        },
        "chart_builder": lambda data, a: line_chart_trend(
            f"{a['country']} {a['medal_type']} medals ({a['start_year']}-{a['end_year']})"
            + (f" - {a.get('season', '')}" if a.get("season") else "")
            + (f" ({a.get('sport', '')})" if a.get("sport") else ""),
            data,
        ),
    },
    "top_countries_by_sport": {
        "fn": top_countries_by_sport,
        "args_schema": {
            "year": "int",
            "sport": "str",
            "medal_type": "str (Gold|Silver|Bronze)",
            "n": "int",
        },
        "chart_builder": lambda data, a: bar_chart_top_countries(
            f"Top {a['n']} countries in {a['sport']} by {a['medal_type']} ({a['year']})", data
        ),
    },
    "participant_count": {
        "fn": participant_count,
        "args_schema": {"year": "int", "country": "str|null", "sport": "str|null"},
        "chart_builder": lambda data, a: indicator_participants("Participants", data),
    },
    "medals_by_sport": {
        "fn": medals_by_sport,
        "args_schema": {"country": "str", "year": "int"},
        "chart_builder": lambda data, a: bar_chart_sport_breakdown(
            f"{a['country']} medals by sport ({a['year']})", data
        ),
    },
    "sport_leaders": {
        "fn": sport_leaders,
        "args_schema": {"year": "int", "sport": "str", "n": "int"},
        "chart_builder": lambda data, a: bar_chart_top_countries(
            f"Top countries in {a['sport']} ({a['year']})",
            [{"country": r["country"], "medals": r["total_medals"]} for r in data],
        ),
    },
    "total_medals_by_year": {
        "fn": total_medals_by_year,
        "args_schema": {"country": "str|null", "start_year": "int", "end_year": "int"},
        "chart_builder": lambda data, a: line_chart_trend(
            f"Total medals by year ({a.get('start_year', 1992)}-{a.get('end_year', 2012)})"
            + (f" - {a.get('country', '')}" if a.get("country") else " (all countries)"),
            data,
        ),
    },
    "compare_countries_over_time": {
        "fn": compare_countries_over_time,
        "args_schema": {"countries": "list[str] (2-5)", "medal_type": "str", "start_year": "int", "end_year": "int"},
        "chart_builder": lambda data, a: line_chart_comparison(
            f"{a['medal_type']} medals comparison ({a.get('start_year', 1992)}-{a.get('end_year', 2012)})",
            data,
            a.get("countries"),
        ),
    },
    "compare_countries_radar": {
        "fn": compare_countries_radar,
        "args_schema": {"year": "int", "countries": "list[str] (2-5)", "season": "str|null"},
        "chart_builder": lambda data, a: radar_chart_countries(
            f"Gold/Silver/Bronze comparison ({a['year']})" + (f" - {a.get('season', '')}" if a.get("season") else ""),
            data,
            a.get("countries"),
        ),
    },
}