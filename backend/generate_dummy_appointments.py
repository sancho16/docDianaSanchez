#!/usr/bin/env python3
"""
Generate dummy appointment data for visualization
Creates 200+ appointments with realistic distribution
"""

import psycopg2
import os
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

load_dotenv()

# Database connection - parse DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # Parse postgresql://user:pass@host/dbname
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^/]+)/(.+)', DATABASE_URL)
    if match:
        DB_USER, DB_PASS, DB_HOST, DB_NAME = match.groups()
        DB_PORT = "5432"
    else:
        print("❌ Could not parse DATABASE_URL")
        exit(1)
else:
    # Fallback to individual variables
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "diana_booking")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASS = os.getenv("DB_PASSWORD", "")

# Dummy data
FIRST_NAMES = [
    "Ana", "María", "José", "Luis", "Carlos", "Carmen", "Pedro", "Laura",
    "Miguel", "Isabel", "Francisco", "Rosa", "Antonio", "Elena", "Manuel",
    "Patricia", "David", "Cristina", "Daniel", "Mónica", "Jorge", "Andrea",
    "Rafael", "Beatriz", "Fernando", "Silvia", "Roberto", "Lucía", "Javier",
    "Natalia", "Ricardo", "Verónica", "Alberto", "Claudia", "Eduardo",
    "Diana", "Sergio", "Paula", "Andrés", "Sofía", "Ramón", "Julia",
    "Óscar", "Teresa", "Raúl", "Adriana", "Guillermo", "Marta", "Víctor", "Irene"
]

LAST_NAMES = [
    "García", "Rodríguez", "Martínez", "López", "González", "Fernández",
    "Sánchez", "Pérez", "Ramírez", "Torres", "Flores", "Rivera", "Gómez",
    "Díaz", "Cruz", "Morales", "Reyes", "Gutiérrez", "Ortiz", "Mendoza",
    "Jiménez", "Vargas", "Castro", "Romero", "Ruiz", "Herrera", "Medina",
    "Ramos", "Castillo", "Vega", "Aguilar", "Navarro", "Moreno", "Delgado"
]

SERVICES = [
    "General Consultation",
    "Medicina Preventiva",
    "Enfermedades Crónicas",
    "Consulta Virtual",
    "Atención Pediátrica",
    "B-Complex IV",
    "Vitamin C IV",
    "Facial Harmonization",
    "IV Rehydration",
    "Visita Domiciliaria"
]

MESSAGES = [
    "Necesito una consulta general, gracias.",
    "Solicito revisión de control de rutina.",
    "Me gustaría agendar una cita para examen físico.",
    "Necesito seguimiento de tratamiento crónico.",
    "Consulta para control de presión arterial.",
    "Revisión de laboratorios recientes.",
    "Consulta por síntomas recientes.",
    "Chequeo médico preventivo anual.",
    "Necesito receta médica para medicación crónica.",
    "Consulta virtual por facilidad de horario.",
    "Requiero consulta especializada.",
    "Seguimiento post-tratamiento.",
]

STATUSES = ["pending", "confirmed", "cancelled", "completed"]
STATUS_WEIGHTS = [0.4, 0.4, 0.1, 0.1]  # 40% pending, 40% confirmed, 10% cancelled, 10% completed

DEVICE_TYPES = ["Desktop", "Mobile", "Tablet"]
OS_TYPES = ["Windows 10", "macOS", "iOS", "Android", "Linux"]
BROWSERS = ["Chrome", "Safari", "Firefox", "Edge"]
CITIES = ["San José", "Alajuela", "Cartago", "Heredia", "Limón", "Puntarenas", "Guanacaste"]

def generate_phone():
    """Generate Costa Rican phone number"""
    return f"+506 {random.randint(6000,8999)}-{random.randint(1000,9999)}"

def generate_email(name):
    """Generate email from name"""
    domains = ["gmail.com", "outlook.com", "yahoo.com", "hotmail.com", "example.com"]
    clean_name = name.lower().replace(" ", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    return f"{clean_name}{random.randint(1,999)}@{random.choice(domains)}"

def generate_date_range():
    """Generate appointments over last 6 months and next 3 months"""
    start_date = datetime.now() - timedelta(days=180)  # 6 months ago
    end_date = datetime.now() + timedelta(days=90)     # 3 months ahead
    
    total_days = (end_date - start_date).days
    random_days = random.randint(0, total_days)
    
    appointment_date = start_date + timedelta(days=random_days)
    return appointment_date.strftime("%Y-%m-%d")

def generate_time():
    """Generate business hours appointment time"""
    hours = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
    return random.choice(hours)

def generate_ip():
    """Generate random IP address"""
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def connect_db():
    """Connect to PostgreSQL database"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def insert_dummy_appointments(num_appointments=200):
    """Insert dummy appointments into database"""
    conn = connect_db()
    cur = conn.cursor()
    
    print(f"🔄 Generating {num_appointments} dummy appointments...")
    
    inserted = 0
    for i in range(num_appointments):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        phone = generate_phone()
        email = generate_email(name)
        service = random.choice(SERVICES)
        preferred_date = generate_date_range()
        preferred_time = generate_time()
        message = random.choice(MESSAGES)
        status = random.choices(STATUSES, STATUS_WEIGHTS)[0]
        
        # Device tracking data
        ip_address = generate_ip()
        device_type = random.choice(DEVICE_TYPES)
        device_os = random.choice(OS_TYPES)
        device_browser = random.choice(BROWSERS)
        ip_city = random.choice(CITIES)
        ip_country = "Costa Rica"
        
        # Created date (distributed over past 6 months)
        created_days_ago = random.randint(0, 180)
        created_at = datetime.now() - timedelta(days=created_days_ago)
        
        try:
            query = """
                INSERT INTO bookings (
                    name, phone, email, service, preferred_date, preferred_time, 
                    message, status, is_dummy,
                    ip_address, device_type, device_os, device_browser,
                    ip_city, ip_country,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            cur.execute(query, (
                name, phone, email, service, preferred_date, preferred_time,
                message, status, True,  # is_dummy=True
                ip_address, device_type, device_os, device_browser,
                ip_city, ip_country,
                created_at, created_at
            ))
            
            inserted += 1
            if (i + 1) % 50 == 0:
                print(f"  ✅ Inserted {i + 1}/{num_appointments} appointments...")
                
        except Exception as e:
            print(f"  ❌ Error inserting appointment {i+1}: {e}")
            continue
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"\n✅ Successfully inserted {inserted} dummy appointments!")
    print(f"📊 Distribution:")
    print(f"   - Pending: ~40%")
    print(f"   - Confirmed: ~40%")
    print(f"   - Cancelled: ~10%")
    print(f"   - Completed: ~10%")
    print(f"\n🗓️  Date range: Last 6 months → Next 3 months")
    print(f"📍 Locations: {', '.join(CITIES[:4])}...")

if __name__ == "__main__":
    print("=" * 60)
    print("   Dummy Appointment Data Generator")
    print("   Dr. Diana Sánchez Booking System")
    print("=" * 60)
    print()
    
    try:
        insert_dummy_appointments(200)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        print("\n💡 Make sure:")
        print("   1. PostgreSQL is running")
        print("   2. .env file has correct DB credentials")
        print("   3. 'bookings' table exists with all required columns")
