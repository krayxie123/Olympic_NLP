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

#filtering

#print(df.head())
print(df.columns)
df = df[df["Season"] == "Summer"]
df["Medal"] = df["Medal"].replace("NaN", pd.NA)
## imputing small record of missing value for sake of completion
group_median_age = df.groupby(["NOC", "age","Games"])["Age"].transform("median")
group_median_height = df.groupby(["NOC", "Height", "Games"])["Height"].transform("median")
group_median_weight = df.groupby(["NOC", "Height", "Games"])["Weight"].transform("median")
df["Age"] = df["Age"].fillna(group_median_age)
df["Height"] = df["Height"].fillna(group_median_height)


f = df[[
    "Year",
    "Team",
    "NOC",
    "City",
    "Sport",
    "Event",
    "Sex",
    "Medal"
]].rename(columns={
    "Year": "year",
    "Team": "country",
    "NOC": "noc",
    "City": "city",
    "Sport": "sport",
    "Event": "event",
    "Sex": "sex",
    "Medal": "medal",
})


print("Connecting to DuckDB at:", DB_PATH)

con = duckdb.connect(str(DB_PATH))