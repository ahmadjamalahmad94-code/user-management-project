from __future__ import annotations

import re


def clean_csv_value(value):
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in ("nan", "none", "null"):
        return ""
    return text


def normalize_phone(phone):
    text = clean_csv_value(phone)
    if text.endswith(".0"):
        text = text[:-2]
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) == 9 and not digits.startswith("0"):
        digits = "0" + digits
    return digits


def normalize_search_ar(text):
    text = clean_csv_value(text)
    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ى": "ي",
        "ة": "ه",
        "ؤ": "و",
        "ئ": "ي",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


def split_full_name(name):
    parts = clean_csv_value(name).split()
    parts += [""] * (4 - len(parts))
    first = parts[0] if len(parts) > 0 else ""
    second = parts[1] if len(parts) > 1 else ""
    third = parts[2] if len(parts) > 2 else ""
    fourth = " ".join(parts[3:]).strip() if len(parts) > 3 else ""
    return first, second, third, fourth


def full_name_from_parts(first, second, third, fourth):
    return " ".join([part.strip() for part in [first, second, third, fourth] if clean_csv_value(part)]).strip()
