"""
Email notification module for Dr. Diana Sánchez booking system
Sends appointment confirmation emails to patients and notifications to the doctor
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


# Email configuration from environment variables
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", "drasanchezd94@gmail.com")
SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "Dr. Diana Sánchez")
DOCTOR_EMAIL = os.environ.get("DOCTOR_EMAIL", "drasanchezd94@gmail.com")

# Fallback to WhatsApp if email not configured
WHATSAPP_NOTIFICATION = os.environ.get("WHATSAPP_NOTIFICATION", "true").lower() == "true"
DOCTOR_WHATSAPP = os.environ.get("DOCTOR_WHATSAPP", "+50683493378")


def send_booking_notice(booking_data: dict) -> bool:
    """
    Send appointment booking notification emails
    
    Args:
        booking_data: Dictionary with booking information (name, email, phone, service, etc.)
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Check if SMTP is configured
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("[notify] SMTP not configured - email notifications disabled")
        print(f"[notify] To enable: Set SMTP_USERNAME and SMTP_PASSWORD in .env")
        print(f"[notify] WhatsApp fallback: {DOCTOR_WHATSAPP}")
        return False
    
    try:
        # Extract booking data
        patient_name = booking_data.get("name", "Patient")
        patient_email = booking_data.get("email")
        patient_phone = booking_data.get("phone", "N/A")
        service = booking_data.get("service", "General Consultation")
        preferred_date = booking_data.get("preferred_date", "Not specified")
        preferred_time = booking_data.get("preferred_time", "Not specified")
        message = booking_data.get("message", "")
        
        # Create HTML email for doctor notification
        doctor_html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Nueva Cita - Dr. Diana Sánchez</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f0f4f8; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.1); overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #00a8b5 0%, #008891 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
                .content {{ padding: 30px; }}
                .info-box {{ background: #f8fafb; border-left: 4px solid #00a8b5; padding: 15px; margin: 20px 0; border-radius: 6px; }}
                .info-row {{ margin: 10px 0; display: flex; }}
                .info-label {{ font-weight: 600; color: #334e68; min-width: 140px; }}
                .info-value {{ color: #102a43; }}
                .message-box {{ background: #fff8e6; border: 1px solid #ffd666; padding: 15px; margin: 20px 0; border-radius: 6px; }}
                .footer {{ background: #f8fafb; padding: 20px; text-align: center; font-size: 13px; color: #627d98; }}
                .cta-button {{ display: inline-block; background: #00a8b5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
                .cta-button:hover {{ background: #008891; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✚ Nueva Solicitud de Cita</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">docdianasanchez.com</p>
                </div>
                <div class="content">
                    <p style="font-size: 16px; color: #102a43; margin-bottom: 20px;">
                        Hola Doctora Diana,
                    </p>
                    <p style="color: #334e68;">
                        Has recibido una nueva solicitud de cita a través de tu sitio web.
                    </p>
                    
                    <div class="info-box">
                        <h3 style="margin-top: 0; color: #00a8b5;">Información del Paciente</h3>
                        <div class="info-row">
                            <span class="info-label">Nombre:</span>
                            <span class="info-value">{patient_name}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Teléfono:</span>
                            <span class="info-value">{patient_phone}</span>
                        </div>
                        {f'<div class="info-row"><span class="info-label">Email:</span><span class="info-value">{patient_email}</span></div>' if patient_email else ''}
                        <div class="info-row">
                            <span class="info-label">Servicio:</span>
                            <span class="info-value">{service}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Fecha Preferida:</span>
                            <span class="info-value">{preferred_date}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Hora Preferida:</span>
                            <span class="info-value">{preferred_time}</span>
                        </div>
                    </div>
                    
                    {f'<div class="message-box"><h4 style="margin-top: 0; color: #856404;">Mensaje del Paciente:</h4><p style="color: #533f03; margin: 0;">{message}</p></div>' if message else ''}
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://api.docdianasanchez.com/admin" class="cta-button">
                            Ver Panel de Administración
                        </a>
                    </div>
                    
                    <p style="color: #627d98; font-size: 14px; margin-top: 30px;">
                        <strong>Próximos pasos:</strong><br>
                        1. Revisa la solicitud en tu panel de administración<br>
                        2. Contacta al paciente para confirmar la cita<br>
                        3. Actualiza el estado de la cita en el sistema
                    </p>
                </div>
                <div class="footer">
                    <p style="margin: 5px 0;">Dr. Diana Carolina Sánchez Dávila</p>
                    <p style="margin: 5px 0;">Médico General · Costa Rica</p>
                    <p style="margin: 5px 0;">
                        <a href="https://docdianasanchez.com" style="color: #00a8b5; text-decoration: none;">docdianasanchez.com</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send notification to doctor
        doctor_msg = MIMEMultipart("alternative")
        doctor_msg["Subject"] = f"🏥 Nueva Cita: {patient_name} - {service}"
        doctor_msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        doctor_msg["To"] = DOCTOR_EMAIL
        doctor_msg.attach(MIMEText(doctor_html, "html"))
        
        # Connect to SMTP server and send
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(doctor_msg)
        
        print(f"[notify] ✓ Doctor notification sent to {DOCTOR_EMAIL}")
        
        # Send confirmation to patient if email provided
        if patient_email:
            patient_html = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Confirmación de Cita</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f0f4f8; margin: 0; padding: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.1); overflow: hidden; }}
                    .header {{ background: linear-gradient(135deg, #00a8b5 0%, #008891 100%); color: white; padding: 30px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
                    .content {{ padding: 30px; }}
                    .success-icon {{ font-size: 48px; text-align: center; margin: 20px 0; }}
                    .info-box {{ background: #f8fafb; border-left: 4px solid #00a8b5; padding: 15px; margin: 20px 0; border-radius: 6px; }}
                    .info-row {{ margin: 10px 0; display: flex; }}
                    .info-label {{ font-weight: 600; color: #334e68; min-width: 140px; }}
                    .info-value {{ color: #102a43; }}
                    .footer {{ background: #f8fafb; padding: 20px; text-align: center; font-size: 13px; color: #627d98; }}
                    .whatsapp-btn {{ display: inline-block; background: #25D366; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
                    .whatsapp-btn:hover {{ background: #20BA5A; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✚ Solicitud de Cita Recibida</h1>
                        <p style="margin: 10px 0 0 0; opacity: 0.9;">Dr. Diana Sánchez</p>
                    </div>
                    <div class="content">
                        <div class="success-icon">✓</div>
                        
                        <p style="font-size: 16px; color: #102a43; text-align: center; margin-bottom: 20px;">
                            Hola <strong>{patient_name}</strong>,
                        </p>
                        <p style="color: #334e68; text-align: center;">
                            Tu solicitud de cita ha sido recibida exitosamente. Nos pondremos en contacto contigo pronto para confirmar tu consulta.
                        </p>
                        
                        <div class="info-box">
                            <h3 style="margin-top: 0; color: #00a8b5;">Detalles de tu Solicitud</h3>
                            <div class="info-row">
                                <span class="info-label">Servicio:</span>
                                <span class="info-value">{service}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Fecha Preferida:</span>
                                <span class="info-value">{preferred_date}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Hora Preferida:</span>
                                <span class="info-value">{preferred_time}</span>
                            </div>
                        </div>
                        
                        <div style="background: #e6f7ff; border: 1px solid #91d5ff; padding: 15px; margin: 20px 0; border-radius: 6px; text-align: center;">
                            <p style="color: #0050b3; margin: 0;"><strong>⏱️ Tiempo de respuesta estimado:</strong> 24-48 horas</p>
                        </div>
                        
                        <p style="color: #334e68; margin-top: 30px;">
                            Si necesitas atención más inmediata, puedes contactarnos directamente por WhatsApp:
                        </p>
                        
                        <div style="text-align: center;">
                            <a href="https://wa.me/{DOCTOR_WHATSAPP.replace('+', '')}?text=Hola%20Dra.%20Diana%2C%20me%20gustaría%20confirmar%20mi%20cita" class="whatsapp-btn">
                                💬 Contactar por WhatsApp
                            </a>
                        </div>
                        
                        <p style="color: #627d98; font-size: 14px; margin-top: 30px; text-align: center;">
                            📞 Teléfono: {DOCTOR_WHATSAPP}<br>
                            ✉️ Email: {DOCTOR_EMAIL}
                        </p>
                    </div>
                    <div class="footer">
                        <p style="margin: 5px 0;">Dr. Diana Carolina Sánchez Dávila</p>
                        <p style="margin: 5px 0;">Médico General · Costa Rica</p>
                        <p style="margin: 5px 0;">
                            <a href="https://docdianasanchez.com" style="color: #00a8b5; text-decoration: none;">docdianasanchez.com</a>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            patient_msg = MIMEMultipart("alternative")
            patient_msg["Subject"] = f"✓ Solicitud de Cita Recibida - Dr. Diana Sánchez"
            patient_msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
            patient_msg["To"] = patient_email
            patient_msg.attach(MIMEText(patient_html, "html"))
            
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(patient_msg)
            
            print(f"[notify] ✓ Patient confirmation sent to {patient_email}")
        
        return True
        
    except Exception as e:
        print(f"[notify] ✗ Email sending failed: {e}")
        print(f"[notify] Booking data: name={booking_data.get('name')}, email={booking_data.get('email')}")
        return False


def send_visit_completion_notice(visit_data: dict, patient_email: str, doctor_email: str) -> bool:
    """
    Send visit completion summary to patient and doctor
    
    Args:
        visit_data: Dictionary with visit information
        patient_email: Patient's email address
        doctor_email: Doctor's email address
        
    Returns:
        bool: True if email sent successfully
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("[notify] SMTP not configured - visit completion email not sent")
        return False
    
    try:
        patient_name = visit_data.get("patient_name", "Patient")
        visit_date = visit_data.get("visit_date", "")
        diagnosis = visit_data.get("diagnosis", "")
        treatment_plan = visit_data.get("treatment_plan", "")
        follow_up = visit_data.get("follow_up_instructions", "")
        medications = visit_data.get("medications", [])
        
        # Build medications list
        medications_html = ""
        if medications and len(medications) > 0:
            medications_html = "<ul style='color: #334e68; margin: 10px 0;'>"
            for med in medications:
                if med and med.strip():
                    medications_html += f"<li>{med}</li>"
            medications_html += "</ul>"
        else:
            medications_html = "<p style='color: #627d98; font-style: italic;'>No medications prescribed</p>"
        
        patient_html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Resumen de Consulta</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f4f8; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.1); overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #00a8b5 0%, #008891 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .section {{ margin: 25px 0; padding: 20px; background: #f8fafb; border-left: 4px solid #00a8b5; border-radius: 6px; }}
                .section-title {{ color: #00a8b5; font-weight: 700; margin: 0 0 10px 0; font-size: 16px; }}
                .footer {{ background: #f8fafb; padding: 20px; text-align: center; font-size: 13px; color: #627d98; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📋 Resumen de Consulta</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Dr. Diana Sánchez</p>
                </div>
                <div class="content">
                    <p style="font-size: 16px; color: #102a43;">Hola <strong>{patient_name}</strong>,</p>
                    <p style="color: #334e68;">Aquí está el resumen de tu consulta del {visit_date}:</p>
                    
                    <div class="section">
                        <h3 class="section-title">Diagnóstico</h3>
                        <p style="color: #334e68; margin: 0;">{diagnosis}</p>
                    </div>
                    
                    <div class="section">
                        <h3 class="section-title">Plan de Tratamiento</h3>
                        <p style="color: #334e68; margin: 0;">{treatment_plan}</p>
                    </div>
                    
                    <div class="section">
                        <h3 class="section-title">Medicamentos Prescritos</h3>
                        {medications_html}
                    </div>
                    
                    {f'<div class="section"><h3 class="section-title">Instrucciones de Seguimiento</h3><p style="color: #334e68; margin: 0;">{follow_up}</p></div>' if follow_up else ''}
                    
                    <p style="color: #627d98; font-size: 14px; margin-top: 30px; text-align: center;">
                        Si tienes preguntas, contáctanos:<br>
                        📞 {DOCTOR_WHATSAPP} · ✉️ {doctor_email}
                    </p>
                </div>
                <div class="footer">
                    <p>Dr. Diana Carolina Sánchez Dávila · Médico General</p>
                    <a href="https://docdianasanchez.com" style="color: #00a8b5;">docdianasanchez.com</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Resumen de tu Consulta - Dr. Diana Sánchez"
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg["To"] = patient_email
        msg.attach(MIMEText(patient_html, "html"))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"[notify] ✓ Visit summary sent to {patient_email}")
        return True
        
    except Exception as e:
        print(f"[notify] ✗ Visit summary email failed: {e}")
        return False


# Test function for debugging
if __name__ == "__main__":
    print("Testing email notification system...")
    print(f"SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"SMTP Username: {'***' if SMTP_USERNAME else 'NOT SET'}")
    print(f"SMTP Password: {'***' if SMTP_PASSWORD else 'NOT SET'}")
    print(f"From: {SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>")
    print(f"Doctor Email: {DOCTOR_EMAIL}")
    
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("\n⚠️  SMTP credentials not configured!")
        print("Set the following in your .env file:")
        print("  SMTP_USERNAME=your_email@gmail.com")
        print("  SMTP_PASSWORD=your_app_password")
    else:
        print("\n✓ SMTP credentials are configured")
        
        # Test booking notification
        test_booking = {
            "name": "Juan Pérez",
            "email": "juan.perez@example.com",
            "phone": "+506 8888-8888",
            "service": "General Consultation",
            "preferred_date": "2026-07-25",
            "preferred_time": "10:00",
            "message": "This is a test booking"
        }
        
        print("\nSending test notification...")
        result = send_booking_notice(test_booking)
        print(f"Result: {'SUCCESS' if result else 'FAILED'}")
