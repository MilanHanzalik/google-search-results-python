import os
import json
import psycopg2
from dotenv import load_dotenv
from serpapi import GoogleSearch
import re
import unicodedata

# Načíta premenné z .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

SERP_API_KEY = os.getenv("SERPAPI_KEY")

ZAKAZANE_DOMENY = [
    'finstat.sk', 'orsr.sk', 'indexpodnikatela.sk', 'registeruz.sk', 'prever.to',
    'azet.sk', 'transparex.sk', 'finreg.sk', 'valida.sk', 'stavebnefirmy.sk', 'foaf.sk',
    'worki.sk', 'profesia.sk', 'firmy.sk', 'firmy.info', 'firmy.sme.sk', 'zoznam.sk',
    'kompass.com', 'register.peniaze.sk', 'workornot.sk', 'ekariera.sk', 'euromaster.cz',
]

def get_firmy():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT ico, nazovfirmy 
        FROM firmy
        WHERE web IS NULL
            AND nazovfirmy not like '%v likvidácii'
            AND nazovfirmy not like '%v likvidácií' AND nazovfirmy = 'LEA Team, s. r. o.'
            AND kraj = 'Trnavský' limit 10;
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def cisti_nazov_firmy(nazov: str) -> str:
    nazov = nazov.lower()
    # Odstránenie diakritiky
    nazov = unicodedata.normalize('NFKD', nazov).encode('ASCII', 'ignore').decode('utf-8')

    # Odstránenie právnych foriem
    pravne_formy = [
        r'\bs\.?r\.?o\.?\b',
        r'\bspol\.?\s*s\.?r\.?o\.?\b',
        r'\ba\.?s\.?\b',
        r'\bv\.?o\.?s\.?\b',
        r'\bk\.?s\.?\b',
        r'\bo\.?z\.?\b'
    ]
    for pattern in pravne_formy:
        nazov = re.sub(pattern, '', nazov)

    # Odstránenie bodiek, čiarok, spojovníkov, lomítok a medzier
    nazov = re.sub(r'[\s.,;:/\\\-]', '', nazov)

    # Odstránenie nadbytočných znakov (napr. zvyšky po čistení)
    nazov = re.sub(r'[^a-z0-9]', '', nazov)

    return nazov

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
            "uule": "Slovakia",
            "num": 20,
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            organic_results = results.get("organic_results", [])

            # Ulož do súboru results.json
            with open("googlesearch_results.json", "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            website = None
            zdroj = None

            # Primárny zdroj: knowledge_graph
            kg = results.get('knowledge_graph', {})
            website_kg = kg.get('website')

            if website_kg and all(blok not in results['knowledge_graph']['website'] for blok in ZAKAZANE_DOMENY):
                website = results['knowledge_graph']['website']
                zdroj = 'knowledge_graph'

            # Fallback: odkaz z organických výsledkov, kde link obsahuje názov firmy
            elif 'organic_results' in results and results['organic_results']:
                for result in organic_results:
                    link = result.get("link")

                    if link and all(blok not in link for blok in ZAKAZANE_DOMENY) and cisti_nazov_firmy(nazovfirmy) in link:
                        website = link
                        zdroj = 'organic_results'
                        break

            # Fallback: odkaz z organických výsledkov
            if website is None and 'organic_results' in results and results['organic_results']:
                for result in organic_results:
                    link = result.get("link")

                    if link and all(blok not in link for blok in ZAKAZANE_DOMENY):
                        website = link
                        zdroj = 'organic_results'
                        break

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
