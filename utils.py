"""
Pure logic functions used by bot.py handlers.
No Telegram-specific code here — keeps things testable and clean.
"""
import base64
import hashlib
import json
import random
import string
from datetime import date, datetime

import pytz
import requests

# ---------- Currency ----------

def convert_currency(amount: float, from_cur: str, to_cur: str) -> str:
    from_cur = from_cur.upper()
    to_cur = to_cur.upper()
    try:
        resp = requests.get(
            f"https://api.exchangerate-api.com/v4/latest/{from_cur}", timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        rates = data.get("rates", {})
        if to_cur not in rates:
            return f"Currency code '{to_cur}' not found."
        result = amount * rates[to_cur]
        return f"{amount:g} {from_cur} = {result:,.2f} {to_cur}"
    except Exception:
        return "Could not fetch exchange rates right now. Try again shortly."


# ---------- Unit conversion ----------

LENGTH_TO_M = {
    "m": 1, "km": 1000, "cm": 0.01, "mm": 0.001,
    "mi": 1609.34, "yd": 0.9144, "ft": 0.3048, "in": 0.0254,
}
WEIGHT_TO_KG = {
    "kg": 1, "g": 0.001, "mg": 0.000001,
    "lb": 0.453592, "oz": 0.0283495,
}
VOLUME_TO_L = {
    "l": 1, "ml": 0.001, "gal": 3.78541, "qt": 0.946353, "cup": 0.24,
}


def convert_temperature(value: float, from_u: str, to_u: str) -> float:
    from_u, to_u = from_u.lower(), to_u.lower()
    if from_u == to_u:
        return value
    if from_u == "f":
        celsius = (value - 32) * 5 / 9
    elif from_u == "k":
        celsius = value - 273.15
    else:
        celsius = value
    if to_u == "f":
        return celsius * 9 / 5 + 32
    elif to_u == "k":
        return celsius + 273.15
    return celsius


def convert_unit(value: float, from_u: str, to_u: str) -> str:
    from_u, to_u = from_u.lower(), to_u.lower()

    if from_u in ("c", "f", "k") and to_u in ("c", "f", "k"):
        result = convert_temperature(value, from_u, to_u)
        return f"{value:g}°{from_u.upper()} = {result:.2f}°{to_u.upper()}"

    for table, label in (
        (LENGTH_TO_M, "length"),
        (WEIGHT_TO_KG, "weight"),
        (VOLUME_TO_L, "volume"),
    ):
        if from_u in table and to_u in table:
            base_value = value * table[from_u]
            result = base_value / table[to_u]
            return f"{value:g} {from_u} = {result:.4g} {to_u}"

    return (
        "Unsupported unit pair. Supported:\n"
        "Length: m, km, cm, mm, mi, yd, ft, in\n"
        "Weight: kg, g, mg, lb, oz\n"
        "Volume: l, ml, gal, qt, cup\n"
        "Temperature: c, f, k"
    )


# ---------- Timezone ----------

def convert_timezone(time_str: str, from_tz: str, to_tz: str) -> str:
    try:
        from_zone = pytz.timezone(from_tz)
        to_zone = pytz.timezone(to_tz)
        naive = datetime.strptime(time_str, "%H:%M")
        today = date.today()
        localized = from_zone.localize(
            datetime(today.year, today.month, today.day, naive.hour, naive.minute)
        )
        converted = localized.astimezone(to_zone)
        return (
            f"{time_str} {from_tz} = {converted.strftime('%H:%M')} {to_tz}"
        )
    except pytz.UnknownTimeZoneError:
        return "Unknown timezone. Use names like 'Asia/Manila' or 'America/New_York'."
    except ValueError:
        return "Use time format HH:MM, e.g. 14:30"


# ---------- Base64 ----------

def b64_encode(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def b64_decode(text: str) -> str:
    try:
        return base64.b64decode(text.encode("utf-8")).decode("utf-8")
    except Exception:
        return "Invalid base64 input."


# ---------- Text tools ----------

def convert_case(text: str, mode: str) -> str:
    mode = mode.lower()
    if mode == "upper":
        return text.upper()
    if mode == "lower":
        return text.lower()
    if mode == "title":
        return text.title()
    if mode == "snake":
        return "_".join(text.split())
    return "Unsupported mode. Use: upper, lower, title, snake"


def count_text(text: str) -> str:
    words = len(text.split())
    chars = len(text)
    chars_no_space = len(text.replace(" ", ""))
    return (
        f"Words: {words}\n"
        f"Characters (with spaces): {chars}\n"
        f"Characters (no spaces): {chars_no_space}"
    )


# ---------- Password generator ----------

def generate_password(length: int = 12, use_symbols: bool = True) -> str:
    length = max(4, min(length, 64))
    pool = string.ascii_letters + string.digits
    if use_symbols:
        pool += "!@#$%^&*()-_=+"
    return "".join(random.choice(pool) for _ in range(length))


# ---------- URL shortener ----------

def shorten_url(url: str) -> str:
    try:
        resp = requests.get(
            "https://tinyurl.com/api-create.php", params={"url": url}, timeout=10
        )
        if resp.status_code == 200 and resp.text.startswith("http"):
            return resp.text
        return "Could not shorten that URL. Make sure it's a valid link."
    except Exception:
        return "URL shortening service is unavailable right now."


# ---------- JSON formatter ----------

def format_json(text: str) -> str:
    try:
        parsed = json.loads(text)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"


# ---------- Hashing ----------

def hash_text(text: str) -> str:
    data = text.encode("utf-8")
    return (
        f"MD5: {hashlib.md5(data).hexdigest()}\n"
        f"SHA1: {hashlib.sha1(data).hexdigest()}\n"
        f"SHA256: {hashlib.sha256(data).hexdigest()}"
    )


# ---------- Color converter ----------

def hex_to_rgb(hex_code: str) -> str:
    hex_code = hex_code.strip().lstrip("#")
    if len(hex_code) != 6:
        return "Enter a valid 6-digit hex code, e.g. #1E90FF"
    try:
        r = int(hex_code[0:2], 16)
        g = int(hex_code[2:4], 16)
        b = int(hex_code[4:6], 16)
        return f"HEX #{hex_code} = RGB({r}, {g}, {b})"
    except ValueError:
        return "Enter a valid 6-digit hex code, e.g. #1E90FF"


def rgb_to_hex(r: int, g: int, b: int) -> str:
    if not all(0 <= v <= 255 for v in (r, g, b)):
        return "RGB values must be between 0 and 255."
    return f"RGB({r}, {g}, {b}) = HEX #{r:02X}{g:02X}{b:02X}"


# ---------- Age / date calculator ----------

def calculate_age(birth_date_str: str) -> str:
    try:
        birth = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        today = date.today()
        years = today.year - birth.year - (
            (today.month, today.day) < (birth.month, birth.day)
        )
        days_total = (today - birth).days
        return f"Age: {years} years ({days_total} days total)"
    except ValueError:
        return "Use date format YYYY-MM-DD, e.g. 1998-05-20"
