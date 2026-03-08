import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.tools import top_countries_by_medals, medal_rate

print("Top 10 countries by Gold in 2008:")
print(top_countries_by_medals(2008, "Gold", 10))

print("\nMedal rate overall in 2008:")
print(medal_rate(2008))

print("\nMedal rate for Australia in 2008:")
print(medal_rate(2008, "Australia"))