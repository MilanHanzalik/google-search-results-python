import json
from serpapi import GoogleSearch

SERP_API_KEY = os.getenv("SERP_API_KEY")

# Paramery pre google_search - crawler
params = {
  "api_key": SERP_API_KEY,
  "engine": "google",
  "q": "MC POWER GROUP, s. r. o.",
  "google_domain": "google.sk",
  "gl": "sk",
  "hl": "sk",
  "uule": "Slovakia"
}

search = GoogleSearch(params)
results = search.get_dict()


# Primárne: knowledge_graph
website = None
if "knowledge_graph" in results and "website" in results["knowledge_graph"]:
    website = results["knowledge_graph"]["website"]
# Fallback: organic_results
elif "organic_results" in results and results["organic_results"]:
    website = results["organic_results"][0].get("link")

# Výpis a uloženie
print("Nájdená stránka:", website if website else "[nenájdená]")

print(results)

# Ulož do súboru results.json
with open("googlesearch_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("✅ Výsledky uložené do results.json")