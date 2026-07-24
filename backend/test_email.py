#!/usr/bin/env python3
"""
Quick email configuration test for Dr. Diana Sánchez booking system
Run this to verify your SMTP setup is working before testing the full booking flow
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("Email Configuration Test")
print("Dr. Diana Sánchez Booking System")
print("=" * 60)
print()

# Check environment variables
print("1. Checking environment variables...")
print("-" * 60)

SMTP_SERVER = os.environ.get("SMTP_SERVER", "")
SMTP_PORT = os.environ.get("SMTP_PORT", "")
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", "")
DOCTOR_EMAIL = os.environ.get("DOCTOR_EMAIL", "")

config_ok = True

if not SMTP_SERVER:
    print("❌ SMTP_SERVER not set")
    config_ok = False
else:
    print(f"✓ SMTP_SERVER: {SMTP_SERVER}")

if not SMTP_PORT:
    print("❌ SMTP_PORT not set")
    config_ok = False
else:
    print(f"✓ SMTP_PORT: {SMTP_PORT}")

if not SMTP_USERNAME:
    print("❌ SMTP_USERNAME not set")
    config_ok = False
else:
    print(f"✓ SMTP_USERNAME: {SMTP_USERNAME}")

if not SMTP_PASSWORD:
    print("❌ SMTP_PASSWORD not set")
    config_ok = False
else:
    # Show first and last 2 chars only
    masked = SMTP_PASSWORD[:2] + "*" * (len(SMTP_PASSWORD) - 4) + SMTP_PASSWORD[-2:]
    print(f"✓ SMTP_PASSWORD: {masked} ({len(SMTP_PASSWORD)} characters)")

if not SMTP_FROM_EMAIL:
    print("❌ SMTP_FROM_EMAIL not set")
    config_ok = False
else:
    print(f"✓ SMTP_FROM_EMAIL: {SMTP_FROM_EMAIL}")

if not DOCTOR_EMAIL:
    print("❌ DOCTOR_EMAIL not set")
    config_ok = False
else:
    print(f"✓ DOCTOR_EMAIL: {DOCTOR_EMAIL}")

print()

if not config_ok:
    print("❌ Configuration incomplete!")
    print()
    print("Please set the missing variables in your .env file.")
    print("See EMAIL_SETUP_GUIDE.md for instructions.")
    sys.exit(1)

print("✓ All required variables are set")
print()

# Test SMTP connection
print("2. Testing SMTP connection...")
print("-" * 60)

try:
    import smtplib
    
    print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
    server = smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT), timeout=10)
    print("✓ Connected to SMTP server")
    
    print("Starting TLS...")
    server.starttls()
    print("✓ TLS started")
    
    print(f"Authenticating as {SMTP_USERNAME}...")
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    print("✓ Authentication successful")
    
    server.quit()
    print("✓ Connection closed")
    print()
    print("✅ SMTP configuration is working!")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ Authentication failed: {e}")
    print()
    print("Common causes:")
    print("1. Using regular password instead of App Password")
    print("2. 2-Step Verification not enabled on Google Account")
    print("3. Incorrect App Password")
    print()
    print("Solution: Generate a new App Password")
    print("See: https://myaccount.google.com/apppasswords")
    sys.exit(1)
    
except smtplib.SMTPException as e:
    print(f"❌ SMTP error: {e}")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Connection error: {e}")
    print()
    print("Common causes:")
    print("1. Incorrect SMTP server or port")
    print("2. Firewall blocking connection")
    print("3. No internet connection")
    sys.exit(1)

print()

# Ask if user wants to send test email
print("3. Send test email?")
print("-" * 60)
response = input(f"Send a test email to {DOCTOR_EMAIL}? (y/n): ").strip().lower()

if response != 'y':
    print()
    print("Test completed successfully (without sending email)")
    print()
    print("Next steps:")
    print("1. Test the booking form on your website")
    print("2. Check for emails in the doctor's inbox")
    print("3. Monitor backend logs for email status")
    sys.exit(0)

print()
print("Sending test email...")

try:
    import notify
    
    test_booking = {
        "name": "Test Patient",
        "email": DOCTOR_EMAIL,  # Send to doctor for testing
        "phone": "+506 8888-8888",
        "service": "Test Booking - Email System Verification",
        "preferred_date": "2026-07-25",
        "preferred_time": "10:00",
        "message": "This is a test booking to verify the email notification system is working correctly."
    }
    
    result = notify.send_booking_notice(test_booking)
    
    if result:
        print()
        print("✅ Test email sent successfully!")
        print()
        print(f"Check your inbox: {DOCTOR_EMAIL}")
        print()
        print("You should receive:")
        print("  1. Doctor notification email")
        print("  2. Patient confirmation email (to the same address)")
        print()
        print("If emails don't arrive within 1 minute:")
        print("  - Check spam/junk folder")
        print("  - Verify email address is correct")
        print("  - Check backend logs for errors")
    else:
        print()
        print("❌ Failed to send test email")
        print()
        print("Check the error messages above for details")
        sys.exit(1)
        
except ImportError:
    print("❌ Cannot import notify module")
    print()
    print("Make sure notify.py exists in the backend directory")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error sending test email: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("Email system test completed successfully!")
print("=" * 60)
print()
print("Your booking system is now ready to send emails.")
print("Visit your website and test a real booking.")
