# stage2_scrape_contacts.py
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import psycopg2
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from extractor import extract_emails, extract_phones
from crawler import ZAKAZANE_DOMENY

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "sk-SK,sk;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com"
}

def get_firmy_to_scrape():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT ico, web FROM firmy
        WHERE web IS NOT NULL AND web NOT LIKE '%finstat%' AND kraj = 'Trnavský' limit 10;
    """)
    firmy = cur.fetchall()
    cur.close()
    conn.close()
    return firmy

def should_verify_ssl(url: str) -> bool:
    return not any(domain in url for domain in ZAKAZANE_DOMENY)

def update_contacts(ico, email, phone):
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("""
        UPDATE firmy
        SET email = %s,
            phone = %s
        WHERE ico = %s;
    """, (",".join(email), ",".join(phone), ico))
    conn.commit()
    cur.close()
    conn.close()

def log_scraper_result(ico, web, status, email, phone, chyba):
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO scraper_logs (ico, web, status, email, phone, chyba)
        VALUES (%s, %s, %s, %s, %s, %s);
    """, (
        ico,
        web,
        status,
        ",".join(email) if email else None,
        ",".join(phone) if phone else None,
        chyba
    ))
    conn.commit()
    cur.close()
    conn.close()

def main():
    firmy = get_firmy_to_scrape()
    print(f"Načítaných webov na scraping: {len(firmy)}")

    for ico, url in firmy:
        try:
            verify_ssl = should_verify_ssl(url)
            # session = requests.Session()
            # session.headers.update(headers)
            # response = session.get(url, timeout=10)
            response = requests.get(url, headers=HEADERS,timeout=10, verify=verify_ssl)  # verify=False pre ignorovanie SSL certifikátov, nepouzivaj v produkcii!
            response.raise_for_status()

            # Ulož do súboru scraped_html/{ico}.html
            with open(f"scraped_html/{ico}.html", "w", encoding="utf-8") as f:
                f.write(response.text)

            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(separator=" ")

            email = extract_emails(text)
            phone = extract_phones(text)

            update_contacts(ico, email, phone)
            log_scraper_result(ico, url, "success", email, phone, None)
            print(f"✅ {ico} → {len(email)} emailov, {len(phone)} telefónov")

        except requests.exceptions.SSLError as e:
            chyba = f"SSL Error: {e}"
        except requests.exceptions.HTTPError as e:
            chyba = f"HTTP Error {e.response.status_code}: {e}"
        except requests.exceptions.Timeout:
            chyba = "Request timed out"
        except requests.exceptions.RequestException as e:
            chyba = f"Request error: {e}"
        except Exception as e:
            chyba = f"General error: {e}"
        else:
            continue  # ak sme nemali chybu, skipni log chyby
        
        log_scraper_result(ico, url, "error", [], [], str(chyba))
        print(f"❌ Chyba pri {ico} ({url}): {chyba}")
        

if __name__ == "__main__":
    main()
