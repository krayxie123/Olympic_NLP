import duckdb
import pandas as pd
from pathlib import Path
import duckdb
#con = duckdb.connect("test.duckdb")
#con.execute("CREATE TABLE test(x INTEGER)")
#con.execute("INSERT INTO test VALUES (1), (2), (3)")
#csv_path = Path('data/athlete_events.csv')
#print(con.execute("SELECT * FROM  test").fetchall())

df = pd.read_csv("data/athlete_events.csv")

#filtering (Summer + Winter - all sports)

#print(df.head())
print(df.columns)
df["Medal"] = df["Medal"].replace("NaN", pd.NA)
## imputing small record of missing value for sake of completion
group_median_age = df.groupby(["NOC", "Games"])["Age"].transform("median")
group_median_height = df.groupby(["NOC", "Games"])["Height"].transform("median")
group_median_weight = df.groupby(["NOC", "Games"])["Weight"].transform("median")
df["Age"] = df["Age"].fillna(group_median_age)
df["Height"] = df["Height"].fillna(group_median_height)


f = df[[
    "Year",
    "Season",
    "Team",
    "NOC",
    "City",
    "Sport",
    "Event",
    "Sex",
    "Medal"
]].rename(columns={
    "Year": "year",
    "Season": "season",
    "Team": "country",
    "NOC": "noc",
    "City": "city",
    "Sport": "sport",
    "Event": "event",
    "Sex": "sex",
    "Medal": "medal",
})


DB_PATH = Path(__file__).resolve().parent.parent / "olympics.duckdb"
print("Connecting to DuckDB at:", DB_PATH)

con = duckdb.connect(str(DB_PATH))
con.execute("DROP TABLE IF EXISTS olympic_medals")
con.execute("DROP TABLE IF EXISTS olympics_all_participants")
con.register("f", f)
con.execute("CREATE TABLE olympic_medals AS SELECT * FROM f")
con.execute("CREATE TABLE olympics_all_participants AS SELECT * FROM f")
print("Created olympic_medals and olympics_all_participants")