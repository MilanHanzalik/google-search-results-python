import re

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PHONE_REGEX = r"(?:\+421|0)?\s?(?:\d{2,3})\s?\d{3}\s?\d{3}"

def extract_emails(text: str) -> list:
    return re.findall(EMAIL_REGEX, text)

def extract_phones(text: str) -> list:
    phones = re.findall(PHONE_REGEX, text)
    # Odstráni medzery z telefónnych čísel (normalizácia)
    return [re.sub(r"\s+", "", phone) for phone in phones]
