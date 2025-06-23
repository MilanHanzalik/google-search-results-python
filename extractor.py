import re

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PHONE_REGEX = r"(?:\+421|00421|0)\s*\d{2,3}[\s-]?\d{3}[\s-]?\d{3}"
#PHONE_REGEX = r"(?:\+421|0)?\s?(?:\d{2,3})\s?\d{3}\s?\d{3}"
#PHONE_REGEX = r"(?:\+421|0)\s*\d{2,3}[\s-]?\d{3}[\s-]?\d{3}"
#PHONE_REGEX = r"(?:\+421|0)\D*\d{2,3}\D*\d{3}\D*\d{3}"

def normalize_phone(raw: str) -> str:
    digits = re.sub(r"[^\d]", "", raw)
    if len(digits) < 9:
        return None  # príliš krátke → vynechať
    if digits.startswith("00421"):
        return "+421" + digits[5:]
    elif digits.startswith("421"):
        return "+421" + digits[3:]
    elif digits.startswith("0"):
        return "+421" + digits[1:]
    return None  # iné formáty nechceme

def extract_emails(text: str) -> list:
    return re.findall(EMAIL_REGEX, text)

def extract_phones(text: str) -> list:
    raw_matches = re.findall(PHONE_REGEX, text)
    #print(raw_matches)
    normalized = [normalize_phone(p) for p in raw_matches]
    return list({p for p in normalized if p})  # odstráň duplicitné a None
