"""
generate_bookings.py
--------------------
Creates a realistic DUMMY bookings dataset that mirrors the schema of the real
docDianaSanchez backend (backend/app.py -> /api/bookings).

We do NOT touch the real Postgres DB. This is purely for you to practice
data science & visualization on safe, fake data.

Run:  python generate_bookings.py
Output: bookings.csv  (one row per booking)
"""
import csv
import random
from datetime import datetime, timedelta

random.seed(42)  # reproducible data every run

# ---- Values pulled from the real backend constants in app.py ----
TIME_SLOTS = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]

SERVICES = [
    "Vitamin C IV", "B-Complex IV", "IV Rehydration", "Symptomatic IV",
    "Facial Harmonization", "General Consultation",
    "Consulta General", "Medicina Preventiva", "Enfermedades Crónicas",
    "Atención Pediátrica", "Consulta Virtual", "Visita Domiciliaria",
]

# Weight services so some are more popular (realistic skew)
SERVICE_WEIGHTS = [
    18, 14, 12, 9,            # IV therapies
    11, 8,                     # facial + general consultation
    10, 7, 6,                  # Spanish consult, preventive, chronic
    4, 5, 6,                   # pediatric, virtual, home visit
]

DEVICES = ["Mobile", "Desktop", "Tablet"]
DEVICE_WEIGHTS = [62, 32, 6]   # most bookings come from phones

# A small set of cities/countries for the geo field
CITIES = [
    ("Madrid", "ES"), ("Barcelona", "ES"), ("Valencia", "ES"),
    ("Ciudad de Mexico", "MX"), ("Guadalajara", "MX"),
    ("Bogota", "CO"), ("Medellin", "CO"),
    ("Buenos Aires", "AR"), ("Miami", "US"),
]

FIRST = ["Lucia", "Mateo", "Sofia", "Diego", "Camila", "Andres", "Valeria",
         "Sebastian", "Isabella", "Tomas", "Martina", "Joaquin", "Emma", "Hugo"]
LAST = ["Garcia", "Rodriguez", "Martinez", "Lopez", "Gonzalez", "Perez",
        "Sanchez", "Ramirez", "Torres", "Flores", "Diaz", "Moreno"]

def random_phone():
    # Fake but plausible phone number
    return f"+{random.choice([34, 52, 57, 54, 1])}{random.randint(100000000, 999999999)}"

def make_name():
    return f"{random.choice(FIRST)} {random.choice(LAST)}"

def random_email(name):
    user = name.lower().replace(" ", ".")
    dom = random.choice(["gmail.com", "hotmail.com", "yahoo.com", "outlook.com"])
    return f"{user}{random.randint(1,99)}@{dom}"

def pick_date():
    # Spread bookings over the last 180 days, with a weekend dip and a
    # slight upward trend (clinic growing).
    days_ago = random.randint(0, 180)
    d = datetime.now() - timedelta(days=days_ago)
    # Weekends (Sat=5, Sun=6) are less popular -> resample if hit
    if d.weekday() >= 5 and random.random() < 0.6:
        d = d - timedelta(days=random.randint(1, 2))
        d = d - timedelta(days=days_ago % 2)  # keep it moving forward-ish
    return d.replace(hour=0, minute=0, second=0, microsecond=0)

def build_rows(n=1500):
    rows = []
    for _ in range(n):
        dt = pick_date()
        device = random.choices(DEVICES, weights=DEVICE_WEIGHTS, k=1)[0]
        city, country = random.choices(CITIES, weights=[20, 16, 12, 14, 9, 13, 8, 10, 7], k=1)[0]
        name = make_name()
        rows.append({
            "name": name,
            "email": random_email(name),
            "phone": random_phone(),
            "preferred_date": dt.strftime("%Y-%m-%d"),
            "preferred_time": random.choice(TIME_SLOTS),
            "service": random.choices(SERVICES, weights=SERVICE_WEIGHTS, k=1)[0],
            "device_type": device,
            "device_os": random.choice(["iOS", "Android", "Windows", "macOS", "Linux"]),
            "device_browser": random.choice(["Safari", "Chrome", "Firefox", "Edge"]),
            "ip_city": city,
            "ip_country": country,
            "created_at": dt.strftime("%Y-%m-%d") + " " + random.choice(TIME_SLOTS),
        })
    return rows

def main():
    rows = build_rows(1500)
    cols = ["name", "email", "phone", "preferred_date", "preferred_time",
            "service", "device_type", "device_os", "device_browser",
            "ip_city", "ip_country", "created_at"]
    with open("bookings.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote bookings.csv with {len(rows)} dummy bookings.")

if __name__ == "__main__":
    main()
