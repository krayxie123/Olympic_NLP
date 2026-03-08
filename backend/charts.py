from typing import List, Dict, Any

# Country colors for comparison charts (consistent across charts when specified)
COUNTRY_COLORS = {
    "United States": "#2563eb",
    "USA": "#2563eb",
    "China": "#dc2626",
    "Russia": "#ea580c",
    "Russian Federation": "#ea580c",
    "Germany": "#4b5563",
    "Great Britain": "#7c3aed",
    "United Kingdom": "#7c3aed",
    "France": "#0891b2",
    "Japan": "#ca8a04",
    "Australia": "#16a34a",
    "Italy": "#059669",
    "South Korea": "#9333ea",
    "Canada": "#0284c7",
    "Norway": "#0d9488",
    "Netherlands": "#e11d48",
}
DEFAULT_PALETTE = ["#2563eb", "#dc2626", "#16a34a", "#ea580c", "#7c3aed"]

def bar_chart_top_countries(title: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    # rows: [{"country": "...", "medals": 123}, ...]
    x = [r["country"] for r in rows]
    y = [r["medals"] for r in rows]

    return {
        "data": [
            {
                "type": "bar",
                "x": x,
                "y": y,
                "marker": {"color": "#1f77b4"},
            }
        ],
        "layout": {
            "title": {"text": title},
            "height": 420,
            "margin": {"t": 60, "b": 80, "l": 60, "r": 40},
            "xaxis": {"title": "Country", "automargin": True, "tickangle": -45},
            "yaxis": {"title": "Medal rows (athlete-level)"},
        },
    }

def indicator_medal_rate(title: str, medal_rate_obj: Dict[str, Any]) -> Dict[str, Any]:
    rate = medal_rate_obj.get("medal_rate")
    country = medal_rate_obj.get("country")
    year = medal_rate_obj.get("year")

    label = f"{country} {year}" if country else f"Overall {year}"
    val = round(rate * 100, 2) if rate is not None else 0

    return {
        "data": [
            {
                "type": "indicator",
                "mode": "number",
                "value": val,
                "title": {"text": f"{title}<br><span style='font-size:0.8em'>{label}</span>"},
                "number": {"suffix": "%", "font": {"size": 36}},
            }
        ],
        "layout": {
            "height": 180,
            "margin": {"t": 50, "b": 30, "l": 30, "r": 30},
        },
    }

def line_chart_trend(title: str, rows: List[Dict[str, Any]]):
    """Line chart for time series."""
    x = [r["year"] for r in rows]
    y = [r["medals"] for r in rows]
    return {
        "data": [
            {
                "type": "scatter",
                "mode": "lines+markers",
                "x": x,
                "y": y,
                "line": {"shape": "spline", "width": 3, "color": "#1f77b4"},
                "marker": {"size": 8},
            }
        ],
        "layout": {
            "title": {"text": title},
            "height": 420,
            "margin": {"t": 60, "b": 60, "l": 60, "r": 40},
            "xaxis": {"title": "Year", "dtick": 1},
            "yaxis": {"title": "Medals (event-level)"},
        },
    }


def bar_chart_sport_breakdown(title: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Bar chart for medals by sport (uses 'total' or 'medals' column)."""
    x = [r["sport"] for r in rows]
    y = [r.get("total", r.get("medals", 0)) for r in rows]
    return {
        "data": [{"type": "bar", "x": x, "y": y}],
        "layout": {
            "title": title,
            "xaxis": {"title": "Sport", "automargin": True, "tickangle": -45},
            "yaxis": {"title": "Medals"},
        },
    }


def line_chart_comparison(
    title: str,
    rows: List[Dict[str, Any]],
    countries: List[str] | None = None,
) -> Dict[str, Any]:
    """Multi-line trend chart comparing countries. Each country gets a distinct color."""
    from collections import defaultdict
    by_country = defaultdict(list)
    for r in rows:
        by_country[r["country"]].append((r["year"], r["medals"]))
    country_list = countries or sorted(by_country.keys(), key=lambda c: sum(v for _, v in by_country[c]), reverse=True)
    data = []
    for i, country in enumerate(country_list):
        pts = by_country.get(country, [])
        pts.sort(key=lambda x: x[0])
        color = COUNTRY_COLORS.get(country, DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)])
        data.append({
            "type": "scatter",
            "mode": "lines+markers",
            "name": country,
            "x": [p[0] for p in pts],
            "y": [p[1] for p in pts],
            "line": {"shape": "spline", "color": color},
            "marker": {"color": color},
        })
    return {
        "data": data,
        "layout": {
            "title": {"text": title},
            "height": 420,
            "margin": {"t": 60, "b": 60, "l": 60, "r": 40},
            "xaxis": {"title": "Year", "dtick": 1},
            "yaxis": {"title": "Medals"},
            "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02},
        },
    }


def radar_chart_countries(
    title: str,
    rows: List[Dict[str, Any]],
    countries: List[str] | None = None,
) -> Dict[str, Any]:
    """Radar chart comparing Gold/Silver/Bronze across countries."""
    if not rows:
        return {
            "data": [],
            "layout": {
                "title": {"text": title},
                "height": 260,
                "annotations": [{"text": "No data for this selection", "xref": "paper", "yref": "paper", "x": 0.5, "y": 0.5, "showarrow": False, "font": {"size": 14}}],
            },
        }
    categories = ["gold", "silver", "bronze"]
    country_list = countries or [r["country"] for r in rows]
    data = []
    for i, country in enumerate(country_list):
        row = next((r for r in rows if r["country"] == country), None)
        if not row:
            continue
        vals = [row.get(c, 0) for c in categories]
        color = COUNTRY_COLORS.get(country, DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)])
        data.append({
            "type": "scatterpolar",
            "name": country,
            "r": vals + [vals[0]],
            "theta": [c.capitalize() for c in categories] + ["Gold"],
            "fill": "toself",
            "line": {"color": color, "width": 2},
        })
    return {
        "data": data,
        "layout": {
            "title": {"text": title},
            "height": 320,
            "polar": {"radialaxis": {"visible": True}},
            "showlegend": True,
            "legend": {"orientation": "h", "yanchor": "bottom"},
        },
    }


def indicator_participants(title: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Big number display for participant count."""
    n = data.get("participants", 0)
    year = data.get("year", "")
    country = data.get("country")
    sport = data.get("sport")
    label = f"{year}"
    if country:
        label = f"{country} {label}"
    if sport:
        label = f"{label} ({sport})"
    return {
        "data": [
            {
                "type": "indicator",
                "mode": "number",
                "value": n,
                "title": {"text": f"{title}<br><span style='font-size:0.8em'>{label}</span>"},
            }
        ],
        "layout": {"title": ""},
    }