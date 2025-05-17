import os
import psycopg2
from dotenv import load_dotenv
from serpapi import GoogleSearch

# Načíta premenné z .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

SERP_API_KEY = os.getenv("SERP_API_KEY")

def get_firmy():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("SELECT ico, nazovfirmy FROM firmy WHERE web IS NULL AND nazovfirmy not like '%v likvidácii' AND kraj = 'Bratislavský';")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def update_firma_web(firma_ico, web_url):
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()
    cur.execute(
        "UPDATE firmy SET web = %s WHERE ico = %s;",
        (web_url, firma_ico)
    )
    conn.commit()
    cur.close()
    conn.close()


def log_result(firma_id, nazov, web, zdroj, status, chyba):
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO crawler_logs (ico, nazovfirmy, vyhladany_web, zdroj, status, chyba)
        VALUES (%s, %s, %s, %s, %s, %s);
    """, (firma_id, nazov, web, zdroj, status, chyba))
    conn.commit()
    cur.close()
    conn.close()

def main():
    firmy = get_firmy()
    print(f"Načítaných firiem: {len(firmy)}")

    for ico, nazovfirmy in firmy:
        params = {
            "api_key": SERP_API_KEY,
            "engine": "google",
            "q": nazovfirmy,
            "google_domain": "google.sk",
            "gl": "sk",
            "hl": "sk",
            "uule": "Slovakia"
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()

            website = None
            zdroj = None

            # Primárny zdroj: knowledge_graph
            if 'knowledge_graph' in results and 'website' in results['knowledge_graph']:
                website = results['knowledge_graph']['website']
                zdroj = 'knowledge_graph'

            # Fallback: prvý odkaz z organických výsledkov
            elif 'organic_results' in results and results['organic_results']:
                website = results['organic_results'][0].get('link')
                zdroj = 'organic_results'

            if website:
                update_firma_web(ico, website)
                log_result(ico, nazovfirmy, website, zdroj, 'success', None)
                print(f"{nazovfirmy} → {website} [{zdroj}]")
            else:
                log_result(ico, nazovfirmy, None, None, 'not found', None)
                print(f"{nazovfirmy} → [web nenašiel]")

        except Exception as e:
            chyba_text = str(e)
            log_result(ico, nazovfirmy, None, None, 'error', chyba_text)
            print(f"❌ Chyba pri '{ico}' - '{nazovfirmy}': {chyba_text}")

if __name__ == "__main__":
    main()
