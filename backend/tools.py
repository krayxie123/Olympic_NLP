import duckdb
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from typing import List, Dict, Optional

DB_PATH = "olympics.duckdb"

VALID_MEDALS = {"Gold", "Silver", "Bronze"}

def top_countries_by_medals(year: int, medal_type: str, n: int = 10, season: Optional[str] = None) -> List[Dict]:
    """
    Returns top N countries by count of medal rows (athlete-level) for a given year + medal.
    Optional season: 'Summer' or 'Winter' (e.g. for "winter olympics" queries).
    """
    medal_type = medal_type.title()
    if medal_type not in VALID_MEDALS:
        raise ValueError(f"medal_type must be one of {sorted(VALID_MEDALS)}")

    con = duckdb.connect(DB_PATH, read_only=True)

    if season:
        season_val = season.title()
        if season_val not in ("Summer", "Winter"):
            season_val = "Winter" if "winter" in str(season).lower() else "Summer"
        try:
            sql = """
            SELECT country, COUNT(DISTINCT event) AS medal_count
            FROM olympic_medals
            WHERE year = ? AND medal = ? AND season = ?
            GROUP BY country
            ORDER BY medal_count DESC
            LIMIT ?
            """
            rows = con.execute(sql, [year, medal_type, season_val, n]).fetchall()
        except duckdb.Error:
            sql = """
            SELECT country, COUNT(DISTINCT event) AS medal_count
            FROM olympic_medals
            WHERE year = ? AND medal = ?
            GROUP BY country
            ORDER BY medal_count DESC
            LIMIT ?
            """
            rows = con.execute(sql, [year, medal_type, n]).fetchall()
    else:
        sql = """
        SELECT country, COUNT(DISTINCT event) AS medal_count
        FROM olympic_medals
        WHERE year = ? AND medal = ?
        GROUP BY country
        ORDER BY medal_count DESC
        LIMIT ?
        """
        rows = con.execute(sql, [year, medal_type, n]).fetchall()
    return [{"country": r[0], "medals": int(r[1])} for r in rows]


def medal_rate(year: int, country: Optional[str] = None) -> Dict:
    """
    % of participating athletes who won any medal in a given year (optionally for a country).
    Note: athlete-level, not event-level.
    """
    con = duckdb.connect(DB_PATH, read_only=True)

    if country:
        sql = """
        SELECT
          SUM(CASE WHEN medal IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / NULLIF(COUNT(*), 0) AS rate,
          COUNT(*) AS participants,
          COALESCE(SUM(CASE WHEN medal IS NOT NULL THEN 1 ELSE 0 END), 0) AS medal_rows
        FROM olympics_all_participants
        WHERE year = ? AND country = ?
        """
        row = con.execute(sql, [year, country]).fetchone()
    else:
        sql = """
        SELECT
          SUM(CASE WHEN medal IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / NULLIF(COUNT(*), 0) AS rate,
          COUNT(*) AS participants,
          COALESCE(SUM(CASE WHEN medal IS NOT NULL THEN 1 ELSE 0 END), 0) AS medal_rows
        FROM olympics_all_participants
        WHERE year = ?
        """
        row = con.execute(sql, [year]).fetchone()

    rate, participants, medal_rows = row or (None, 0, 0)

    return {
        "year": year,
        "country": country,
        "participants": int(participants or 0),
        "medal_rows": int(medal_rows or 0),
        "medal_rate": float(rate) if rate is not None else None
    }

def medals_over_time(country: str, medal_type: str, start_year: int, end_year: int, sport: Optional[str] = None, season: Optional[str] = None) -> List[Dict]:
    """Medal count by year for a country. Optional: sport, season (Winter|Summer) to filter by Olympics type."""
    medal_type = medal_type.title()
    if medal_type not in VALID_MEDALS:
        raise ValueError(f"medal_type must be one of {sorted(VALID_MEDALS)}")
    con = duckdb.connect(DB_PATH, read_only=True)

    conds = ["country = ?", "medal = ?", "year BETWEEN ? AND ?"]
    params: list = [country, medal_type, start_year, end_year]
    if sport:
        conds.append("LOWER(sport) = LOWER(?)")
        params.append(sport)
    if season:
        season_val = "Winter" if "winter" in str(season).lower() else "Summer"
        conds.append("season = ?")
        params.append(season_val)

    where = " AND ".join(conds)
    sql = f"""
    SELECT year, COUNT(DISTINCT event) AS medals
    FROM olympic_medals
    WHERE {where}
    GROUP BY year ORDER BY year ASC
    """
    WINTER_YEARS = {1992, 1994, 1998, 2002, 2006, 2010, 2014}
    try:
        rows = con.execute(sql, params).fetchall()
    except duckdb.Error:
        # Fallback if season column missing: query without season, then filter to Winter years
        if season and "winter" in str(season).lower():
            conds = [c for c in conds if "season" not in c]
            params = [country, medal_type, start_year, end_year] + ([sport] if sport else [])
            where = " AND ".join(conds)
            sql = f"SELECT year, COUNT(DISTINCT event) AS medals FROM olympic_medals WHERE {where} GROUP BY year ORDER BY year ASC"
            rows = con.execute(sql, params).fetchall()
            rows = [(y, c) for y, c in rows if y in WINTER_YEARS]
        else:
            rows = con.execute(sql, params).fetchall()
    return [{"year": r[0], "medals": int(r[1])} for r in rows]


def top_countries_by_sport(year: int, sport: str, medal_type: str = "Gold", n: int = 10) -> List[Dict]:
    """Top N countries by medals in a specific sport for a year."""
    medal_type = medal_type.title()
    if medal_type not in VALID_MEDALS:
        raise ValueError(f"medal_type must be one of {sorted(VALID_MEDALS)}")
    con = duckdb.connect(DB_PATH, read_only=True)
    sql = """
    SELECT country, COUNT(DISTINCT event) AS medals
    FROM olympic_medals
    WHERE year = ? AND medal = ? AND LOWER(sport) = LOWER(?)
    GROUP BY country
    ORDER BY medals DESC
    LIMIT ?
    """
    rows = con.execute(sql, [year, medal_type, sport, n]).fetchall()
    return [{"country": r[0], "medals": int(r[1])} for r in rows]


def participant_count(year: int, country: Optional[str] = None, sport: Optional[str] = None) -> Dict:
    """Total participant count for a year (optionally by country and/or sport)."""
    con = duckdb.connect(DB_PATH, read_only=True)
    conditions = ["year = ?"]
    params = [year]
    if country:
        conditions.append("country = ?")
        params.append(country)
    if sport:
        conditions.append("LOWER(sport) = LOWER(?)")
        params.append(sport)

    where = " AND ".join(conditions)
    sql = f"""
    SELECT COUNT(*) AS participants, COUNT(DISTINCT event) AS events
    FROM olympics_all_participants
    WHERE {where}
    """
    row = con.execute(sql, params).fetchone()
    return {
        "year": year,
        "country": country,
        "sport": sport,
        "participants": int(row[0]),
        "events": int(row[1]),
    }


def medals_by_sport(country: str, year: int) -> List[Dict]:
    """Medal breakdown by sport for a country in a year."""
    con = duckdb.connect(DB_PATH, read_only=True)
    sql = """
    SELECT sport, medal, COUNT(DISTINCT event) AS count
    FROM olympic_medals
    WHERE country = ? AND year = ?
    GROUP BY sport, medal
    ORDER BY sport, medal
    """
    rows = con.execute(sql, [country, year]).fetchall()

    by_sport: Dict[str, Dict] = {}
    for sport, medal, count in rows:
        if sport not in by_sport:
            by_sport[sport] = {"sport": sport, "gold": 0, "silver": 0, "bronze": 0}
        by_sport[sport][medal.lower()] = int(count)

    result = []
    for s in sorted(by_sport.keys()):
        r = by_sport[s]
        r["total"] = r["gold"] + r["silver"] + r["bronze"]
        result.append(r)
    return result


def sport_leaders(year: int, sport: str, n: int = 5) -> List[Dict]:
    """Top countries in a sport by total medals (any type) for a year."""
    con = duckdb.connect(DB_PATH, read_only=True)
    sql = """
    SELECT country, COUNT(DISTINCT event) AS total_medals
    FROM olympic_medals
    WHERE year = ? AND LOWER(sport) = LOWER(?)
    GROUP BY country
    ORDER BY total_medals DESC
    LIMIT ?
    """
    rows = con.execute(sql, [year, sport, n]).fetchall()
    return [{"country": r[0], "total_medals": int(r[1])} for r in rows]


def total_medals_by_year(country: Optional[str] = None, start_year: int = 1992, end_year: int = 2012) -> List[Dict]:
    """Total medals (all types) per year, optionally for a country."""
    con = duckdb.connect(DB_PATH, read_only=True)
    if country:
        sql = """
        SELECT year, COUNT(DISTINCT event) AS medals
        FROM olympic_medals
        WHERE country = ? AND year BETWEEN ? AND ?
        GROUP BY year ORDER BY year ASC
        """
        rows = con.execute(sql, [country, start_year, end_year]).fetchall()
    else:
        sql = """
        SELECT year, COUNT(DISTINCT event) AS medals
        FROM olympic_medals
        WHERE year BETWEEN ? AND ?
        GROUP BY year ORDER BY year ASC
        """
        rows = con.execute(sql, [start_year, end_year]).fetchall()
    return [{"year": r[0], "medals": int(r[1])} for r in rows]


def compare_countries_over_time(
    countries: List[str],
    medal_type: str = "Gold",
    start_year: int = 1992,
    end_year: int = 2012,
) -> List[Dict]:
    """Compare medal trends for 2-5 countries over time. Returns [{year, country, medals}, ...]."""
    medal_type = medal_type.title()
    if medal_type not in VALID_MEDALS:
        raise ValueError(f"medal_type must be one of {sorted(VALID_MEDALS)}")
    if not countries or len(countries) > 5:
        raise ValueError("Provide 2-5 countries to compare")
    con = duckdb.connect(DB_PATH, read_only=True)
    placeholders = ", ".join("?" * len(countries))
    sql = f"""
    SELECT year, country, COUNT(DISTINCT event) AS medals
    FROM olympic_medals
    WHERE country IN ({placeholders}) AND medal = ? AND year BETWEEN ? AND ?
    GROUP BY year, country
    ORDER BY year ASC, country
    """
    rows = con.execute(sql, list(countries) + [medal_type, start_year, end_year]).fetchall()
    return [{"year": r[0], "country": r[1], "medals": int(r[2])} for r in rows]


def compare_countries_radar(year: int, countries: List[str], season: Optional[str] = None) -> List[Dict]:
    """Gold/Silver/Bronze breakdown for 2-5 countries in a year. For radar chart."""
    if not countries or len(countries) > 5:
        raise ValueError("Provide 2-5 countries to compare")
    con = duckdb.connect(DB_PATH, read_only=True)
    placeholders = ", ".join("?" * len(countries))
    base_sql = f"""
    SELECT country, medal, COUNT(DISTINCT event) AS count
    FROM olympic_medals
    WHERE country IN ({placeholders}) AND year = ? AND medal IS NOT NULL
    GROUP BY country, medal
    """
    params: list = list(countries) + [year]
    if season:
        try:
            sql = base_sql.rstrip() + " AND season = ?"
            params.append("Winter" if "winter" in str(season).lower() else "Summer")
            rows = con.execute(sql, params).fetchall()
        except duckdb.Error:
            rows = con.execute(base_sql, list(countries) + [year]).fetchall()
    else:
        rows = con.execute(base_sql, params).fetchall()
    by_country: Dict[str, Dict] = {}
    for country, medal, cnt in rows:
        if medal is None:
            continue
        if country not in by_country:
            by_country[country] = {"country": country, "gold": 0, "silver": 0, "bronze": 0}
        by_country[country][medal.lower()] = int(cnt)
    return [by_country[c] for c in countries if c in by_country]

