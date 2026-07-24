#!/usr/bin/env python3
"""Quick email test to verify SMTP configuration"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
NOTIFY_TO = os.getenv("NOTIFY_TO")

print("=" * 60)
print("   Email Configuration Test")
print("=" * 60)
print(f"SMTP Host: {SMTP_HOST}")
print(f"SMTP Port: {SMTP_PORT}")
print(f"SMTP User: {SMTP_USER}")
print(f"Notify To: {NOTIFY_TO}")
print(f"Password: {'*' * len(SMTP_PASS) if SMTP_PASS else 'NOT SET'}")
print()

try:
    # Create test email
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = NOTIFY_TO
    msg["Subject"] = "✅ Test Email - Dr. Diana Sánchez System"
    
    body = """
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>✅ Email System Test</h2>
        <p>This is a test email from the Dr. Diana Sánchez booking system.</p>
        <p>If you're reading this, email notifications are working correctly!</p>
        <hr>
        <p style="color: #666; font-size: 12px;">
            Sent at: {datetime}<br>
            From: Backend Server
        </p>
    </body>
    </html>
    """.format(datetime=__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    msg.attach(MIMEText(body, "html"))
    
    print("🔄 Connecting to SMTP server...")
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    
    print("🔄 Logging in...")
    server.login(SMTP_USER, SMTP_PASS)
    
    print("🔄 Sending email...")
    server.send_message(msg)
    server.quit()
    
    print("\n✅ EMAIL SENT SUCCESSFULLY!")
    print(f"📧 Check {NOTIFY_TO} inbox")
    
except Exception as e:
    print(f"\n❌ EMAIL FAILED: {e}")
    print("\n💡 Troubleshooting:")
    print("   1. Check .env file has correct SMTP credentials")
    print("   2. Verify Gmail App Password is valid")
    print("   3. Check 2FA is enabled on Gmail account")
    print("   4. Verify 'Less secure app access' if needed")
