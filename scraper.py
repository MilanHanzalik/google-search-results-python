# stage2_scrape_contacts.py
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import psycopg2
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from extractor import extract_emails, extract_phones

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def get_firmy_to_scrape():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT ico, web FROM firmy
        WHERE web IS NOT NULL AND web NOT LIKE '%finstat%';
    """)
    firmy = cur.fetchall()
    cur.close()
    conn.close()
    return firmy

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
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(separator=" ")

            email = extract_emails(text)
            phone = extract_phones(text)

            update_contacts(ico, email, phone)
            log_scraper_result(ico, url, "success", email, phone, None)
            print(f"✅ {ico} → {len(email)} emailov, {len(phone)} telefónov")

        except Exception as e:
            log_scraper_result(ico, url, "error", [], [], str(e))
            print(f"❌ Chyba pri {ico} ({url}): {e}")

if __name__ == "__main__":
    main()
