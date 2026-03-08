import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.tools import top_countries_by_medals, medal_rate
from backend.charts import bar_chart_top_countries, indicator_medal_rate
import json

top = top_countries_by_medals(2008, "Gold", 10)
chart1 = bar_chart_top_countries("Top 10 countries by Gold (2008)", top)

rate_all = medal_rate(2008)
chart2 = indicator_medal_rate("Medal rate (athlete-level)", rate_all)

print("Bar chart JSON preview:")
print(json.dumps(chart1, indent=2)[:800], "...\n")

print("Indicator chart JSON preview:")
print(json.dumps(chart2, indent=2)[:800], "...\n")