import os
import psycopg2
from dotenv import load_dotenv
from serpapi import GoogleSearch

# Paramery pre google_search - crawler
params = {
  "api_key": "5a4878198e466dfb74b91e3977434899026e471c42fbd14b7919451ab05d0582",
  "engine": "google",
  "q": "Gasotech, s.r.o.",
  "google_domain": "google.sk",
  "gl": "sk",
  "hl": "sk",
  "uule": "Slovakia"
}

# Načíta premenné z .env súboru
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def main():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()

        cur.execute("SELECT nazovfirmy, kraj FROM firmy WHERE kraj = 'Bratislavský';")
        rows = cur.fetchall()

        print("Zoznam firiem:")
        for row in rows:
            print(f"- {row[0]} ({row[1]})")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Chyba pri práci s databázou: {e}")

if __name__ == "__main__":
    main()

#Clawler

# search = GoogleSearch(params)
# results = search.get_dict()

# print(results['knowledge_graph']['website'])