import os
from dotenv import load_dotenv
load_dotenv()
import re
import time
import json
from datetime import datetime, timedelta

import psycopg2
from flask import Flask, send_from_directory, request, jsonify, Response, render_template_string, make_response, redirect, url_for
from flask_cors import CORS
import notify

app = Flask(__name__)

# Only the real site may call this API. Adjust if you add a staging domain.
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "https://docdianasanchez.com,https://www.docdianasanchez.com",
).split(",")
CORS(app, origins=ALLOWED_ORIGINS, methods=["POST", "GET", "OPTIONS"])

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://diana_app@localhost/diana_bookings",
)

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")  # set via .env

# Very small in-memory rate limiter: IP -> list of timestamps (last 20 min)
_RATE = {}
_RATE_WINDOW = 20 * 60
_RATE_MAX = 15  # submissions per window per IP

VALID_TIME_SLOTS = {"08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"}
VALID_SERVICES = {
    "Vitamin C IV", "B-Complex IV", "IV Rehydration", "Symptomatic IV",
    "Facial Harmonization", "General Consultation",
    "Consulta General", "Medicina Preventiva", "Enfermedades Crónicas",
    "Atención Pediátrica", "Consulta Virtual", "Visita Domiciliaria",
}
NAME_RE = re.compile(r"^[\wÀ-ÿ'’\.\-\s]{2,120}$")


def _db():
    return psycopg2.connect(DATABASE_URL, connect_timeout=5)


def _rate_ok(ip: str) -> bool:
    now = time.time()
    hits = _RATE.get(ip, [])
    hits = [t for t in hits if now - t < _RATE_WINDOW]
    if len(hits) >= _RATE_MAX:
        _RATE[ip] = hits
        return False
    hits.append(now)
    _RATE[ip] = hits
    return True


@app.route("/api/health", methods=["GET"])
def health():
    try:
        conn = _db()
        conn.close()
        return jsonify({"status": "ok", "db": "up"})
    except Exception as e:  # pragma: no cover
        return jsonify({"status": "degraded", "db": "down", "error": str(e)}), 503


@app.route("/api/bookings", methods=["POST", "OPTIONS"])
def create_booking():
    if request.method == "OPTIONS":
        return ("", 204)

    # CORS preflight already handled, but block obvious abuse early
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip() or "unknown"
    if not _rate_ok(ip):
        return jsonify({"ok": False, "error": "Too many requests. Try again later."}), 429

    data = request.get_json(silent=True) or request.form.to_dict()

    # Honeypot — real users never fill this hidden field
    if data.get("_gotcha"):
        # Pretend success so bots don't retry
        return jsonify({"ok": True})

    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    email = (data.get("email") or "").strip() or None
    preferred_date = (data.get("preferred_date") or "").strip() or None
    preferred_time = (data.get("preferred_time") or "").strip() or None
    service = (data.get("service") or "").strip() or None
    message = (data.get("message") or "").strip()

    errors = []
    if not NAME_RE.match(name):
        errors.append("invalid name")
    if not re.match(r"^[\d\s\+\-\(\)]{7,20}$", phone):
        errors.append("invalid phone")
    if email and not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        errors.append("invalid email")
    if preferred_time and preferred_time not in VALID_TIME_SLOTS:
        errors.append("invalid time slot")
    if service and service not in VALID_SERVICES:
        errors.append("invalid service")
    if not message or len(message) < 3:
        errors.append("message too short")

    if preferred_date:
        try:
            pd = datetime.strptime(preferred_date, "%Y-%m-%d").date()
            if pd < datetime.now().date():
                errors.append("date in the past")
        except ValueError:
            errors.append("invalid date")

    if errors:
        return jsonify({"ok": False, "error": "; ".join(errors)}), 400

    try:
        conn = _db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO bookings
               (name, phone, email, preferred_date, preferred_time, service, message, status, is_dummy)
               VALUES (%s,%s,%s,%s,%s,%s,%s,'pending',FALSE)
               RETURNING id, created_at""",
            (name, phone, email, preferred_date, preferred_time, service, message),
        )
        row = cur.fetchone()
        bid = row[0]
        conn.commit()
        cur.close()
        conn.close()
        # Fire-and-forget email notification (does not block the response)
        try:
            notify.send_booking_notice({
                "name": name, "phone": phone, "email": email,
                "service": service, "preferred_date": preferred_date,
                "preferred_time": preferred_time, "message": message,
            })
        except Exception as e:
            print(f"[notify] exception: {e}")
        return jsonify({"ok": True, "id": bid}), 201
    except Exception as e:
        return jsonify({"ok": False, "error": "database error"}), 500




@app.route("/api/bookings", methods=["GET"])
def get_bookings():
    """Public endpoint to fetch bookings - for frontend admin panel"""
    try:
        status_filter = request.args.get('status', '').strip()
        limit = int(request.args.get('limit', '100'))
        
        conn = _db()
        cur = conn.cursor()
        
        # Fetch bookings with all device tracking fields
        query = """
            SELECT 
                id, name, patient_id, phone, email, channel, virtual_platform,
                address, address_city, address_province, gps_coordinates,
                service, preferred_date, preferred_time, message, status,
                ip_address, ip_country, ip_city, device_type, device_brand,
                device_model, device_os, device_browser, screen_size,
                user_language, user_timezone, connection_type,
                created_at, updated_at
            FROM bookings 
            WHERE 1=1
        """
        params = []
        
        if status_filter:
            query += " AND status = %s"
            params.append(status_filter)
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        cur.execute(query, params)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        
        bookings = []
        for row in rows:
            booking = dict(zip(cols, row))
            # Convert dates to ISO format strings
            for key in ['created_at', 'updated_at']:
                if booking.get(key):
                    booking[key] = booking[key].isoformat()
            for key in ['preferred_date', 'preferred_time']:
                if booking.get(key):
                    booking[key] = str(booking[key])
            bookings.append(booking)
        
        cur.close()
        conn.close()
        
        return jsonify({
            'ok': True,
            'bookings': bookings,
            'count': len(bookings)
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@app.route("/api/bookings/<int:booking_id>", methods=["GET", "PATCH", "DELETE"])
def handle_booking(booking_id):
    """Handle individual booking operations"""
    
    if request.method == "GET":
        try:
            conn = _db()
            cur = conn.cursor()
            
            query = """
                SELECT 
                    id, name, patient_id, phone, email, channel, virtual_platform,
                    address, address_city, address_province, gps_coordinates,
                    service, preferred_date, preferred_time, message, status,
                    ip_address, ip_country, ip_city, device_type, device_brand,
                    device_model, device_os, device_browser, screen_size,
                    user_language, user_timezone, connection_type,
                    created_at, updated_at
                FROM bookings 
                WHERE id = %s
            """
            
            cur.execute(query, (booking_id,))
            cols = [d[0] for d in cur.description]
            row = cur.fetchone()
            
            if not row:
                cur.close()
                conn.close()
                return jsonify({'ok': False, 'error': 'Booking not found'}), 404
            
            booking = dict(zip(cols, row))
            
            # Convert dates
            for key in ['created_at', 'updated_at']:
                if booking.get(key):
                    booking[key] = booking[key].isoformat()
            for key in ['preferred_date', 'preferred_time']:
                if booking.get(key):
                    booking[key] = str(booking[key])
            
            cur.close()
            conn.close()
            
            return jsonify({'ok': True, 'booking': booking})
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    elif request.method == "PATCH":
        try:
            data = request.get_json(silent=True) or {}
            status = data.get('status', '').strip()
            
            if not status:
                return jsonify({'ok': False, 'error': 'Status is required'}), 400
            
            if status not in ['pending', 'confirmed', 'cancelled', 'completed']:
                return jsonify({'ok': False, 'error': 'Invalid status'}), 400
            
            conn = _db()
            cur = conn.cursor()
            
            query = "UPDATE bookings SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
            cur.execute(query, (status, booking_id))
            conn.commit()
            
            if cur.rowcount == 0:
                cur.close()
                conn.close()
                return jsonify({'ok': False, 'error': 'Booking not found'}), 404
            
            cur.close()
            conn.close()
            
            return jsonify({'ok': True, 'message': 'Booking updated successfully'})
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    elif request.method == "DELETE":
        try:
            conn = _db()
            cur = conn.cursor()
            
            query = "DELETE FROM bookings WHERE id = %s"
            cur.execute(query, (booking_id,))
            conn.commit()
            
            if cur.rowcount == 0:
                cur.close()
                conn.close()
                return jsonify({'ok': False, 'error': 'Booking not found'}), 404
            
            cur.close()
            conn.close()
            
            return jsonify({'ok': True, 'message': 'Booking deleted successfully'})
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e)}), 500


@app.route("/api/bookings.csv", methods=["GET"])
def bookings_csv():
    token = request.args.get("token") or request.headers.get("X-Admin-Token", "")
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        return jsonify({"error": "unauthorized"}), 401
    only_dummy = request.args.get("dummy", "0") == "1"
    try:
        conn = _db()
        cur = conn.cursor()
        if only_dummy:
            cur.execute("SELECT * FROM bookings WHERE is_dummy = TRUE ORDER BY created_at DESC")
        else:
            cur.execute("SELECT * FROM bookings ORDER BY created_at DESC")
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        cur.close()
        conn.close()
        lines = [",".join(cols)]
        for r in rows:
            lines.append(",".join('"' + str(c).replace('"', '""') + '"' if c is not None else "" for c in r))
        return Response("\n".join(lines), mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=bookings.csv"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


ADMIN_COOKIE = "dds_admin"
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
ALLOWED_ADMINS = [e.strip().lower() for e in os.environ.get("ALLOWED_ADMINS", "").split(",") if e.strip()]
_GOOGLE_CERTS = {}


def _verify_google_token(token_str: str) -> dict:
    """Verify a Google ID token using google-auth library."""
    from google.oauth2 import id_token
    from google.auth.transport import requests
    try:
        info = id_token.verify_oauth2_token(
            id_token=token_str,
            request=requests.Request(),
            audience=GOOGLE_CLIENT_ID
        )
        if info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        return info
    except Exception as e:
        raise ValueError(f'Token verification failed: {e}')

def _admin_authed():
    """Cookie holds either a verified Google email (allow-listed) or the legacy ADMIN_TOKEN."""
    val = request.cookies.get(ADMIN_COOKIE) or request.headers.get("X-Admin-Token") or request.args.get("token", "")
    if not val:
        return False
    if ADMIN_TOKEN and val == ADMIN_TOKEN:
        return True
    return val.lower() in ALLOWED_ADMINS


@app.route("/api/admin/auth", methods=["POST"])
def admin_auth():
    """Accept a Google ID token, verify it, set session cookie if email is allowed."""
    if not GOOGLE_CLIENT_ID:
        return jsonify({"error": "Google Sign-In no configurado (falta GOOGLE_CLIENT_ID)."}), 503
    body = request.get_json(silent=True) or {}
    id_token = body.get("credential", "")
    try:
        payload = _verify_google_token(id_token)
    except Exception as e:
        return jsonify({"error": f"Token inválido: {e}"}), 401
    email = (payload.get("email") or "").lower()
    if not payload.get("email_verified") or email not in ALLOWED_ADMINS:
        return jsonify({"error": "Correo no autorizado para el panel."}), 403
    resp = make_response(jsonify({"ok": True, "email": email}))
    resp.set_cookie(ADMIN_COOKIE, email, httponly=True, secure=True, samesite="Strict", max_age=60*60*8)
    return resp


@app.route("/admin", methods=["GET"])
def admin_login_page():
    if _admin_authed():
        return redirect(url_for("admin_view"))
    return render_template_string(ADMIN_LOGIN_HTML, google_client_id=GOOGLE_CLIENT_ID)


@app.route("/admin/login", methods=["POST"])
def admin_login():
    # Legacy token fallback (still works if GOOGLE_CLIENT_ID not set)
    tok = (request.get_json(silent=True) or request.form.to_dict() or {}).get("token", "")
    if bool(ADMIN_TOKEN) and tok == ADMIN_TOKEN:
        resp = make_response(redirect(url_for("admin_view")))
        resp.set_cookie(ADMIN_COOKIE, tok, httponly=True, secure=True, samesite="Strict", max_age=60*60*8)
        return resp
    return render_template_string(ADMIN_LOGIN_HTML, error="Token inválido o Google Sign-In requerido.")


@app.route("/admin/logout", methods=["GET", "POST"])
def admin_logout():
    resp = make_response(redirect(url_for("admin_login_page")))
    resp.delete_cookie(ADMIN_COOKIE)
    return resp


@app.route("/admin/view", methods=["GET"])
def admin_view():
    if not _admin_authed():
        return redirect(url_for("admin_login_page"))
    return render_template_string(ADMIN_VIEW_HTML)


@app.route("/api/admin/bookings", methods=["GET"])
def admin_list():
    if not _admin_authed():
        return jsonify({"error": "unauthorized"}), 401
    only_dummy = request.args.get("dummy", "0") == "1"
    status = request.args.get("status", "").strip()
    read_filter = request.args.get("read", "").strip()
    try:
        conn = _db()
        cur = conn.cursor()
        q = "SELECT id,name,phone,email,preferred_date,preferred_time,service,message,status,is_dummy,created_at FROM bookings WHERE 1=1"
        params = []
        if only_dummy:
            q += " AND is_dummy = TRUE"
        if status:
            q += " AND status = %s"
            params.append(status)
        q += " ORDER BY created_at DESC LIMIT 500"
        cur.execute(q, params)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        
        processed_rows = []
        for r in rows:
            row_dict = dict(zip(cols, r))
            message = row_dict.get('message', '') or ''
            if message.startswith('[READ]'):
                row_dict['read_status'] = 'read'
                row_dict['message'] = message.replace('[READ] ', '').replace('[READ]', '')
            else:
                row_dict['read_status'] = 'unread'
            if read_filter and row_dict['read_status'] != read_filter:
                continue
            processed_rows.append(row_dict)
        
        cur.close()
        conn.close()
        return jsonify({"rows": processed_rows, "count": len(processed_rows)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/bookings/<int:bid>/mark-read", methods=["PATCH"])
def admin_mark_read(bid):
    if not _admin_authed():
        return jsonify({"error": "unauthorized"}), 401
    
    body = request.get_json(silent=True) or {}
    read_status = body.get('read_status', 'read')
    if read_status not in ['read', 'unread']:
        return jsonify({"error": "invalid read_status"}), 400
    
    try:
        conn = _db()
        cur = conn.cursor()
        cur.execute("SELECT message FROM bookings WHERE id=%s", (bid,))
        result = cur.fetchone()
        if not result:
            return jsonify({"error": "booking not found"}), 404
        
        current_message = result[0] or ""
        read_marker = "[READ]"
        
        if read_status == 'read' and not current_message.startswith(read_marker):
            new_message = read_marker + " " + current_message
        elif read_status == 'unread' and current_message.startswith(read_marker):
            new_message = current_message.replace(read_marker + " ", "").replace(read_marker, "")
        else:
            new_message = current_message
            
        cur.execute("UPDATE bookings SET message=%s, updated_at=now() WHERE id=%s", (new_message, bid))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"ok": True, "id": bid, "read_status": read_status})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    if not _admin_authed():
        return jsonify({"error": "unauthorized"}), 401
    try:
        conn = _db()
        cur = conn.cursor()
        # KPIs
        cur.execute("SELECT count(*) FROM bookings WHERE is_dummy=FALSE")
        total_real = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM bookings WHERE is_dummy=FALSE AND status='pending'")
        pending = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM bookings WHERE is_dummy=TRUE")
        total_dummy = cur.fetchone()[0]
        cur.execute("""SELECT count(*) FROM bookings WHERE is_dummy=FALSE
                        AND created_at >= now() - interval '7 days'""")
        week = cur.fetchone()[0]
        # by status (real only)
        cur.execute("""SELECT status, count(*) FROM bookings WHERE is_dummy=FALSE
                        GROUP BY status""")
        by_status = {r[0]: r[1] for r in cur.fetchall()}
        # by service (real only)
        cur.execute("""SELECT service, count(*) FROM bookings WHERE is_dummy=FALSE
                        GROUP BY service ORDER BY 2 DESC""")
        by_service = [{"service": r[0], "count": r[1]} for r in cur.fetchall()]
        # last 90 days (real only), bucketed by day
        cur.execute("""SELECT to_char(created_at,'YYYY-MM-DD') d, count(*)
                        FROM bookings WHERE is_dummy=FALSE
                        AND created_at >= now() - interval '90 days'
                        GROUP BY d ORDER BY d""")
        by_day = [{"date": r[0], "count": r[1]} for r in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({
            "kpi": {"total_real": total_real, "pending": pending, "week": week, "total_dummy": total_dummy},
            "by_status": by_status,
            "by_service": by_service,
            "by_day": by_day,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/bookings/<int:bid>", methods=["PATCH"])
def admin_update(bid):
    if not _admin_authed():
        return jsonify({"error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    new_status = body.get("status")
    if new_status not in ("pending", "confirmed", "completed", "cancelled"):
        return jsonify({"error": "invalid status"}), 400
    try:
        conn = _db()
        cur = conn.cursor()
        cur.execute("UPDATE bookings SET status=%s, updated_at=now() WHERE id=%s", (new_status, bid))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"ok": True, "id": bid, "status": new_status})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def index():
    return jsonify({"service": "diana-booking-backend", "endpoints": ["/api/health", "/api/bookings", "/admin"]})


# ── Admin HTML (kept inline; turquoise theme to match the site) ──
ADMIN_LOGIN_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin – Dr. Diana Sánchez</title>
<script src="https://accounts.google.com/gsi/client" async defer></script>
<style>
 *{box-sizing:border-box}
 :root{
   --bg-gradient-start:#001f25;
   --bg-gradient-mid:#003d47;
   --bg-gradient-end:#005f6b;
   --glass-bg:rgba(255,255,255,0.08);
   --glass-border:rgba(255,255,255,0.12);
   --text-primary:#ffffff;
   --text-secondary:rgba(255,255,255,0.75);
   --text-muted:rgba(255,255,255,0.5);
   --accent:#5fe3d6;
   --accent-hover:#00b8a3;
 }
 body{
   font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','Segoe UI',Roboto,sans-serif;
   background:linear-gradient(135deg,var(--bg-gradient-start) 0%,var(--bg-gradient-mid) 50%,var(--bg-gradient-end) 100%);
   color:var(--text-primary);
   display:flex;
   min-height:100vh;
   align-items:center;
   justify-content:center;
   margin:0;
   padding:1rem;
 }
 .glass-card{
   background:var(--glass-bg);
   backdrop-filter:blur(24px) saturate(180%);
   -webkit-backdrop-filter:blur(24px) saturate(180%);
   border-radius:24px;
   border:1px solid var(--glass-border);
   box-shadow:0 24px 64px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1);
   padding:3rem 2.5rem;
   width:420px;
   max-width:100%;
   text-align:center;
   animation:fadeIn 0.6s ease-out;
 }
 @keyframes fadeIn{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
 
 .lang-toggle{
   position:absolute;
   top:1rem;
   right:1rem;
   display:flex;
   gap:0.5rem;
 }
 .lang-toggle button{
   background:var(--glass-bg);
   border:1px solid var(--glass-border);
   color:var(--text-secondary);
   padding:0.4rem 0.8rem;
   border-radius:8px;
   cursor:pointer;
   font-size:0.85rem;
   transition:all 0.3s ease;
 }
 .lang-toggle button.active{
   background:var(--accent);
   color:#001f25;
   border-color:var(--accent);
   font-weight:700;
 }
 
 h1{font-size:1.8rem;font-weight:700;margin:0 0 .5rem;color:var(--accent);letter-spacing:-0.02em}
 p.subtitle{font-size:1rem;color:var(--text-secondary);margin:0 0 2.5rem;font-weight:400}
 .section{margin-bottom:2rem}
 .section-title{font-size:0.9rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:1rem;font-weight:600}
 .divider{display:flex;align-items:center;margin:2rem 0;color:rgba(255,255,255,0.4);font-size:0.85rem}
 .divider::before,.divider::after{content:'';flex:1;height:1px;background:rgba(255,255,255,0.15)}
 .divider::before{margin-right:1rem}.divider::after{margin-left:1rem}
 .token-form{display:flex;flex-direction:column;gap:1rem}
 input[type="password"]{
   width:100%;
   padding:1rem 1.2rem;
   border-radius:14px;
   border:1px solid rgba(255,255,255,0.15);
   background:rgba(255,255,255,0.06);
   color:var(--text-primary);
   font-size:1rem;
   transition:all 0.3s ease;
   font-family:inherit;
 }
 input[type="password"]:focus{
   outline:none;
   border-color:var(--accent);
   background:rgba(255,255,255,0.1);
   box-shadow:0 0 0 3px rgba(95,227,214,0.15);
 }
 input[type="password"]::placeholder{color:var(--text-muted)}
 button.primary{
   width:100%;
   padding:1rem 1.5rem;
   border:0;
   border-radius:14px;
   background:linear-gradient(135deg,var(--accent) 0%,var(--accent-hover) 100%);
   color:#001f25;
   font-weight:700;
   font-size:1rem;
   cursor:pointer;
   transition:all 0.3s ease;
   box-shadow:0 4px 16px rgba(95,227,214,0.3);
 }
 button.primary:hover{
   transform:translateY(-2px);
   box-shadow:0 8px 24px rgba(95,227,214,0.4);
 }
 button.primary:active{transform:translateY(0)}
 .google-container{display:flex;justify-content:center;min-height:44px}
 .safari-note{
   font-size:0.75rem;
   color:var(--text-muted);
   margin-top:0.8rem;
   padding:0.75rem 1rem;
   background:rgba(255,165,0,0.1);
   border:1px solid rgba(255,165,0,0.2);
   border-radius:10px;
   line-height:1.4;
 }
 .safari-note strong{color:#ffb347}
 .error{
   color:#ff6b6b;
   font-size:0.9rem;
   margin-top:1.5rem;
   padding:0.9rem 1.2rem;
   background:rgba(255,107,107,0.15);
   border:1px solid rgba(255,107,107,0.3);
   border-radius:12px;
 }

 .filter-bar{
   background:var(--glass-bg);
   backdrop-filter:blur(24px);
   border:1px solid var(--glass-border);
   border-radius:12px;
   padding:1rem;
   margin-bottom:1.5rem;
   display:flex;
   gap:1rem;
   align-items:center;
   flex-wrap:wrap;
 }
 .filter-group{
   display:flex;
   gap:0.5rem;
   align-items:center;
 }
 .filter-group label{
   font-size:0.85rem;
   color:var(--text-secondary);
   font-weight:500;
   margin-right:0.5rem;
 }
 .read-status{
   display:flex;
   gap:0.3rem;
   border:1px solid var(--glass-border);
   border-radius:8px;
   overflow:hidden;
   background:var(--glass-bg);
 }
 .read-status button{
   background:transparent;
   border:none;
   padding:0.5rem 1rem;
   color:var(--text-secondary);
   font-size:0.8rem;
   cursor:pointer;
   transition:all 0.2s;
   position:relative;
 }
 .read-status button.active{
   background:var(--accent);
   color:#000;
   font-weight:600;
 }
 .read-status button:hover:not(.active){
   background:rgba(255,255,255,0.1);
   color:var(--text-primary);
 }
 .unread-indicator{
   display:inline-block;
   width:8px;
   height:8px;
   background:#ff6b6b;
   border-radius:50%;
   margin-right:0.5rem;
   animation:pulse-unread 2s infinite;
 }
 .read-indicator{
   display:inline-block;
   width:8px;
   height:8px;
   background:#51cf66;
   border-radius:50%;
   margin-right:0.5rem;
 }
 @keyframes pulse-unread{
   0%, 100% { opacity:1; transform:scale(1); }
   50% { opacity:0.6; transform:scale(1.2); }
 }
 .read-actions{
   display:flex;
   gap:0.3rem;
 }
 .read-actions button{
   background:var(--glass-bg);
   border:1px solid var(--glass-border);
   color:var(--text-secondary);
   padding:0.3rem 0.6rem;
   border-radius:6px;
   font-size:0.75rem;
   cursor:pointer;
   transition:all 0.2s;
 }
 .read-actions button:hover{
   background:var(--accent);
   color:#000;
   border-color:var(--accent);
 }
 tr.unread{
   background:rgba(255,107,107,0.05);
   border-left:3px solid #ff6b6b;
 }
 tr.read{
   opacity:0.8;
 }

</style></head><body>

<div class="lang-toggle">
  <button onclick="setLang('en')" id="btnEN" class="active">EN</button>
  <button onclick="setLang('es')" id="btnES">ES</button>
</div>

<div class="glass-card">
 <h1 data-en="Admin Panel" data-es="Panel de Administración">Admin Panel</h1>
 <p class="subtitle" data-en="Dr. Diana Sánchez" data-es="Dra. Diana Sánchez">Dr. Diana Sánchez</p>
 
 <div class="section">
   <div class="section-title" data-en="Recommended method (Safari compatible)" data-es="Método recomendado (Safari compatible)">Recommended method (Safari compatible)</div>
   <form class="token-form" method="post" action="/admin/login">
     <input name="token" type="password" placeholder="Admin token" data-placeholder-en="Admin token" data-placeholder-es="Token de administrador" required autofocus>
     <button type="submit" class="primary" data-en="Sign in" data-es="Iniciar sesión">Sign in</button>
   </form>
 </div>

 <div class="divider" data-en="or continue with" data-es="o continuar con">or continue with</div>

 <div class="section">
   <div class="section-title" data-en="Google Sign-In (Chrome only)" data-es="Google Sign-In (Chrome solamente)">Google Sign-In (Chrome only)</div>
   <div class="google-container" id="g_id_signin"></div>
   <div class="safari-note" id="safari-warning" style="display:none">
     <strong>⚠️ Safari:</strong> <span data-en="Google Sign-In requires third-party cookies. Use the admin token above or switch to Chrome." data-es="Google Sign-In requiere cookies de terceros. Use el token de administrador arriba o cambie a Chrome.">Google Sign-In requires third-party cookies. Use the admin token above or switch to Chrome.</span>
   </div>
 </div>

 {% if error %}<div class="error">{{error}}</div>{% endif %}
</div>

<script>
let currentLang = 'en';

function setLang(lang) {
  currentLang = lang;
  localStorage.setItem('adminLang', lang);
  
  document.getElementById('btnEN').classList.toggle('active', lang === 'en');
  document.getElementById('btnES').classList.toggle('active', lang === 'es');
  
  document.querySelectorAll('[data-en]').forEach(el => {
    const text = el.getAttribute(`data-${lang}`);
    if (text) {
      if (el.tagName === 'INPUT') {
        el.placeholder = el.getAttribute(`data-placeholder-${lang}`) || text;
      } else {
        el.textContent = text;
      }
    }
  });
}

// Detect Safari
const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
if (isSafari) {
  document.getElementById('safari-warning').style.display = 'block';
}

const CLIENT_ID = "{{ google_client_id }}";
function handleCredential(resp){
  fetch('/api/admin/auth',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({credential:resp.credential})
  })
  .then(r=>r.json())
  .then(d=>{
    if(d.ok){ location.href='/admin/view'; }
    else { alert(d.error||'Error signing in with Google'); }
  })
  .catch(()=>alert('Network error'));
}

if (CLIENT_ID && CLIENT_ID.length > 10) {
  google.accounts.id.initialize({
    client_id: CLIENT_ID,
    callback: handleCredential
  });
  google.accounts.id.renderButton(
    document.getElementById('g_id_signin'),
    {theme:'filled_blue', size:'large', width:300}
  );
} else {
  document.getElementById('g_id_signin').innerHTML = 
    '<p style="color:rgba(255,255,255,0.5);font-size:0.85rem">Google Sign-In not configured</p>';
}

// Initialize language
const savedLang = localStorage.getItem('adminLang') || 'en';
setLang(savedLang);
</script>
</body></html>"""

ADMIN_VIEW_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin Panel – Dr. Diana Sánchez</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
 *{box-sizing:border-box;margin:0;padding:0}
 :root{
   --bg-gradient-start:#001f25;
   --bg-gradient-end:#003d47;
   --glass-bg:rgba(255,255,255,0.08);
   --glass-border:rgba(255,255,255,0.12);
   --text-primary:#ffffff;
   --text-secondary:rgba(255,255,255,0.7);
   --text-muted:rgba(255,255,255,0.5);
   --accent:#5fe3d6;
   --accent-hover:#00b8a3;
   --shadow:rgba(0,0,0,0.3);
 }
 body{
   font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','Segoe UI',Roboto,sans-serif;
   background:linear-gradient(135deg,var(--bg-gradient-start) 0%,var(--bg-gradient-end) 100%);
   color:var(--text-primary);
   min-height:100vh;
   overflow-x:hidden;
 }
 
 header{
   background:var(--glass-bg);
   backdrop-filter:blur(24px) saturate(180%);
   -webkit-backdrop-filter:blur(24px) saturate(180%);
   border-bottom:1px solid var(--glass-border);
   padding:1.2rem 2rem;
   display:flex;
   justify-content:space-between;
   align-items:center;
   position:sticky;
   top:0;
   z-index:100;
   box-shadow:0 4px 16px var(--shadow);
 }
 header h1{font-size:1.4rem;font-weight:700;color:var(--accent);letter-spacing:-0.02em}
 .lang-toggle{
   display:flex;
   gap:0.5rem;
   margin:0 1rem;
 }
 .lang-toggle button{
   background:var(--glass-bg);
   border:1px solid var(--glass-border);
   color:var(--text-secondary);
   padding:0.4rem 0.8rem;
   border-radius:8px;
   cursor:pointer;
   font-size:0.85rem;
   transition:all 0.3s ease;
 }
 .lang-toggle button.active{
   background:var(--accent);
   color:#001f25;
   border-color:var(--accent);
   font-weight:700;
 }
 a.logout{
   color:var(--text-secondary);
   font-size:0.95rem;
   text-decoration:none;
   padding:0.6rem 1.2rem;
   border-radius:12px;
   background:var(--glass-bg);
   border:1px solid var(--glass-border);
   transition:all 0.3s ease;
   white-space:nowrap;
 }
 a.logout:hover{background:rgba(255,255,255,0.12);transform:translateY(-1px)}
 
 .container{max-width:1600px;margin:0 auto;padding:2rem}
 
 .kpis{
   display:grid;
   grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
   gap:1.5rem;
   margin-bottom:2rem;
 }
 .kpi{
   background:var(--glass-bg);
   backdrop-filter:blur(16px) saturate(180%);
   -webkit-backdrop-filter:blur(16px) saturate(180%);
   border-radius:20px;
   border:1px solid var(--glass-border);
   padding:1.8rem 1.5rem;
   box-shadow:0 8px 32px var(--shadow);
   transition:all 0.3s ease;
 }
 .kpi:hover{transform:translateY(-4px);box-shadow:0 12px 48px rgba(0,0,0,0.5)}
 .kpi .num{font-size:2.4rem;font-weight:800;color:var(--accent);margin-bottom:0.4rem}
 .kpi .label{font-size:0.9rem;color:var(--text-muted);font-weight:500}
 
 .grid{display:grid;grid-template-columns:2fr 1fr;gap:1.5rem;margin-bottom:1.5rem}
 .panel{
   background:var(--glass-bg);
   backdrop-filter:blur(16px) saturate(180%);
   -webkit-backdrop-filter:blur(16px) saturate(180%);
   border-radius:20px;
   border:1px solid var(--glass-border);
   padding:1.8rem;
   box-shadow:0 8px 32px var(--shadow);
 }
 .panel h2{font-size:1.1rem;font-weight:600;margin:0 0 1.5rem;color:var(--text-secondary);letter-spacing:-0.01em}
 .panel canvas{display:block;width:100% !important;height:300px !important}
 
 .bar2{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:1.5rem}
 
 @media(max-width:1100px){
   .grid{grid-template-columns:1fr}
   .bar2{grid-template-columns:1fr}
   header{flex-wrap:wrap;gap:1rem}
 }
 
 .toolbar{
   background:var(--glass-bg);
   backdrop-filter:blur(16px) saturate(180%);
   -webkit-backdrop-filter:blur(16px) saturate(180%);
   border-radius:20px;
   border:1px solid var(--glass-border);
   padding:1.2rem 1.5rem;
   margin-bottom:1.5rem;
   display:flex;
   gap:1rem;
   flex-wrap:wrap;
   align-items:center;
 }
 .toolbar label{display:flex;align-items:center;gap:0.5rem;color:var(--text-secondary);font-size:0.9rem}
 select{
   padding:0.6rem 1rem;
   border-radius:10px;
   border:1px solid rgba(255,255,255,0.2);
   background:rgba(255,255,255,0.06);
   color:var(--text-primary);
   font-size:0.9rem;
   cursor:pointer;
   transition:all 0.3s ease;
 }
 select:focus{outline:none;border-color:var(--accent);background:rgba(255,255,255,0.1)}
 button.act{
   padding:0.7rem 1.4rem;
   border:0;
   border-radius:10px;
   background:linear-gradient(135deg,var(--accent) 0%,var(--accent-hover) 100%);
   color:#001f25;
   font-weight:700;
   font-size:0.9rem;
   cursor:pointer;
   transition:all 0.3s ease;
   box-shadow:0 4px 16px rgba(95,227,214,0.3);
 }
 button.act:hover{transform:translateY(-2px);box-shadow:0 6px 24px rgba(95,227,214,0.4)}
 .toolbar .cnt{margin-left:auto;color:var(--text-muted);font-size:0.9rem}
 a.exp{
   color:var(--accent);
   text-decoration:none;
   padding:0.6rem 1.2rem;
   border-radius:10px;
   border:1px solid rgba(95,227,214,0.3);
   background:rgba(95,227,214,0.06);
   transition:all 0.3s ease;
 }
 a.exp:hover{background:rgba(95,227,214,0.12);transform:translateY(-1px)}
 
 .table-container{
   background:var(--glass-bg);
   backdrop-filter:blur(16px) saturate(180%);
   -webkit-backdrop-filter:blur(16px) saturate(180%);
   border-radius:20px;
   border:1px solid var(--glass-border);
   padding:1.5rem;
   overflow-x:auto;
 }
 table{width:100%;border-collapse:collapse;font-size:0.9rem}
 th,td{padding:1rem 0.8rem;text-align:left;vertical-align:top;border-bottom:1px solid rgba(255,255,255,0.08)}
 th{color:var(--text-muted);font-weight:600;font-size:0.85rem;text-transform:uppercase;letter-spacing:0.05em}
 td{color:var(--text-secondary)}
 tr:last-child td{border-bottom:0}
 tbody tr:hover{background:rgba(255,255,255,0.03)}
 
 .pill{
   display:inline-block;
   padding:0.3rem 0.8rem;
   border-radius:999px;
   font-size:0.75rem;
   font-weight:600;
   text-transform:uppercase;
   letter-spacing:0.03em;
 }
 .pending{background:rgba(232,245,154,0.2);color:#e8f59a;border:1px solid rgba(232,245,154,0.3)}
 .confirmed{background:rgba(154,242,201,0.2);color:#9af2c9;border:1px solid rgba(154,242,201,0.3)}
 .completed{background:rgba(159,217,242,0.2);color:#9fd9f2;border:1px solid rgba(159,217,242,0.3)}
 .cancelled{background:rgba(245,154,154,0.2);color:#f59a9a;border:1px solid rgba(245,154,154,0.3)}
 
 .sel{opacity:0.5}
 .tag{
   font-size:0.7rem;
   color:var(--accent);
   background:rgba(95,227,214,0.15);
   padding:0.2rem 0.5rem;
   border-radius:6px;
   margin-left:0.4rem;
 }
</style></head><body>

<header>
  <h1 data-en="Appointment Panel – Dr. Diana Sánchez" data-es="Panel de citas – Dra. Diana Sánchez">Appointment Panel – Dr. Diana Sánchez</h1>
  <div style="display:flex;align-items:center;gap:1rem">
    <div class="lang-toggle">
      <button onclick="setLang('en')" id="btnEN" class="active">EN</button>
      <button onclick="setLang('es')" id="btnES">ES</button>
    </div>
    <a class="logout" href="/admin/logout" data-en="Logout" data-es="Cerrar sesión">Logout</a>
  </div>
</header>

<div class="container">
  <div class="kpis" id="kpis"></div>
  
  <div class="grid">
    <div class="panel">
      <h2 data-en="Appointments per day (last 90 days)" data-es="Citas por día (últimos 90 días)">Appointments per day (last 90 days)</h2>
      <canvas id="cDay"></canvas>
    </div>
    <div class="panel">
      <h2 data-en="By Status" data-es="Por estado">By Status</h2>
      <canvas id="cStatus"></canvas>
    </div>
  </div>
  
  <div class="bar2">
    <div class="panel">
      <h2 data-en="By Service" data-es="Por servicio">By Service</h2>
      <canvas id="cService"></canvas>
    </div>
    <div class="panel">
      <h2 data-en="Real vs. Dummy" data-es="Reales vs. Dummy">Real vs. Dummy</h2>
      <canvas id="cMix"></canvas>
    </div>
  </div>
  
  <div class="toolbar">
    <label><span data-en="Filter:" data-es="Filtrar:">Filter:</span>
      <select id="fDummy">
        <option value="0" data-en="All" data-es="Todas">All</option>
        <option value="1" data-en="Dummy only" data-es="Solo dummy">Dummy only</option>
      </select>
    </label>
    <label><span data-en="Status:" data-es="Estado:">Status:</span>
      <select id="fStatus">
        <option value="" data-en="All" data-es="Todos">All</option>
        <option value="pending" data-en="Pending" data-es="Pendiente">Pending</option>
        <option value="confirmed" data-en="Confirmed" data-es="Confirmado">Confirmed</option>
        <option value="completed" data-en="Completed" data-es="Completado">Completed</option>
        <option value="cancelled" data-en="Cancelled" data-es="Cancelado">Cancelled</option>
      </select>
    </label>
    <button class="act" onclick="load()" data-en="Refresh" data-es="Actualizar">Refresh</button>
    <a class="exp" id="csv" href="#" data-en="Export CSV" data-es="Exportar CSV">Export CSV</a>
    <span class="cnt" id="cnt"></span>
  </div>
  
  <div class="table-container">
    <table>
      <thead><tr>
        <th>#</th>
        <th data-en="Name" data-es="Nombre">Name</th>
        <th data-en="Phone" data-es="Teléfono">Phone</th>
        <th data-en="Email" data-es="Correo">Email</th>
        <th data-en="Date" data-es="Fecha">Date</th>
        <th data-en="Time" data-es="Hora">Time</th>
        <th data-en="Service" data-es="Servicio">Service</th>
        <th data-en="Message" data-es="Mensaje">Message</th>
        <th data-en="Status" data-es="Estado">Status</th>
        <th data-en="Action" data-es="Acción">Action</th>
      </tr></thead>
      <tbody id="rows"></tbody>
    </table>
  </div>
</div>

<script>
const TRANSLATIONS = {
  en: {
    appointments: 'appointments',
    realApptsTotal: 'Real appointments (total)',
    pending: 'Pending',
    last7Days: 'Last 7 days',
    dummyPractice: 'Dummy (practice)',
    real: 'Real',
    dummy: 'Dummy',
    confirm: 'Confirm',
    complete: 'Complete',
    cancel: 'Cancel'
  },
  es: {
    appointments: 'citas',
    realApptsTotal: 'Citas reales (total)',
    pending: 'Pendientes',
    last7Days: 'Últimos 7 días',
    dummyPractice: 'Dummy (práctica)',
    real: 'Reales',
    dummy: 'Dummy',
    confirm: 'Confirmar',
    complete: 'Completar',
    cancel: 'Cancelar'
  }
};

let currentLang = 'en';
let statsData = null;

function setLang(lang) {
  currentLang = lang;
  localStorage.setItem('adminLang', lang);
  
  // Update button states
  document.getElementById('btnEN').classList.toggle('active', lang === 'en');
  document.getElementById('btnES').classList.toggle('active', lang === 'es');
  
  // Update all translatable elements
  document.querySelectorAll('[data-en]').forEach(el => {
    const text = el.getAttribute(`data-${lang}`);
    if (text) {
      if (el.tagName === 'OPTION') {
        el.textContent = text;
      } else {
        el.childNodes[0].nodeValue = text;
      }
    }
  });
  
  // Redraw charts with new language
  if (statsData) charts(statsData);
  load();
}

const COL = {pending:'#e8f59a',confirmed:'#9af2c9',completed:'#9fd9f2',cancelled:'#f59a9a'};
const TOK = () => (document.cookie.match(/dds_admin=([^;]+)/)||[,location.search.match(/token=([^&]+)/)||['','']][1])[1];
const qp = () => `dummy=${fDummy.value}&status=${fStatus.value}`;
const t = (key) => TRANSLATIONS[currentLang][key];

function load() {
  fetch('/api/admin/bookings?'+qp(),{headers:{'X-Admin-Token':''}})
  .then(r=>r.json())
  .then(d=>{
    if(d.error){location.href='/admin';return;}
    rows.innerHTML=d.rows.map(r=>`
      <tr class="${r.is_dummy?'sel':''}">
        <td>${r.id}${r.is_dummy?` <span class="tag">${t('dummy')}</span>`:''}</td>
        <td>${esc(r.name)}</td>
        <td>${esc(r.phone||'')}</td>
        <td>${esc(r.email||'')}</td>
        <td>${r.preferred_date||'—'}</td>
        <td>${r.preferred_time||'—'}</td>
        <td>${esc(r.service||'—')}</td>
        <td>${esc((r.message||'').slice(0,80))}</td>
        <td><span class="pill ${r.status}">${r.status}</span></td>
        <td><select onchange="setStatus(${r.id},this.value)">
          <option value="">—</option>
          <option value="confirmed">${t('confirm')}</option>
          <option value="completed">${t('complete')}</option>
          <option value="cancelled">${t('cancel')}</option>
        </select></td>
      </tr>`).join('');
    cnt.textContent = `${d.count} ${t('appointments')}`;
    csv.href='/api/bookings.csv?dummy='+fDummy.value+'&token='+encodeURIComponent(TOK());
  })
  .catch(()=>location.href='/admin');
}

function setStatus(id,s){
  if(!s)return;
  fetch('/api/admin/bookings/'+id,{
    method:'PATCH',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({status:s})
  }).then(()=>load());
}

function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}

let chartInstances = {};

function charts(s) {
  statsData = s;
  const k = s.kpi;
  
  kpis.innerHTML=`
    <div class="kpi"><div class="num">${k.total_real}</div><div class="label">${t('realApptsTotal')}</div></div>
    <div class="kpi"><div class="num">${k.pending}</div><div class="label">${t('pending')}</div></div>
    <div class="kpi"><div class="num">${k.week}</div><div class="label">${t('last7Days')}</div></div>
    <div class="kpi"><div class="num">${k.total_dummy}</div><div class="label">${t('dummyPractice')}</div></div>`;
  
  // Destroy existing charts
  Object.values(chartInstances).forEach(c => c && c.destroy());
  chartInstances = {};
  
  const day = s.by_day || [];
  chartInstances.cDay = new Chart(document.getElementById('cDay'), {
    type:'line',
    data:{
      labels:day.map(x=>x.date),
      datasets:[{
        label:t('appointments'),
        data:day.map(x=>x.count),
        borderColor:'#5fe3d6',
        backgroundColor:'rgba(95,227,214,.2)',
        fill:true,
        tension:.4,
        borderWidth:3
      }]
    },
    options:{
      responsive:true,
      maintainAspectRatio:false,
      plugins:{legend:{display:false}},
      scales:{
        x:{ticks:{maxTicksLimit:12,color:'rgba(255,255,255,0.6)'},grid:{color:'rgba(255,255,255,0.06)'}},
        y:{ticks:{color:'rgba(255,255,255,0.6)',precision:0},grid:{color:'rgba(255,255,255,0.06)'}}
      }
    }
  });
  
  const st = s.by_status || {};
  const stk = Object.keys(st);
  chartInstances.cStatus = new Chart(document.getElementById('cStatus'), {
    type:'doughnut',
    data:{
      labels:stk,
      datasets:[{data:stk.map(k=>st[k]),backgroundColor:stk.map(k=>COL[k]||'#888')}]
    },
    options:{
      responsive:true,
      maintainAspectRatio:false,
      plugins:{legend:{position:'right',labels:{color:'#ffffff'}}}
    }
  });
  
  const sv = s.by_service || [];
  chartInstances.cService = new Chart(document.getElementById('cService'), {
    type:'bar',
    data:{
      labels:sv.map(x=>x.service),
      datasets:[{label:t('appointments'),data:sv.map(x=>x.count),backgroundColor:'#5fe3d6'}]
    },
    options:{
      responsive:true,
      maintainAspectRatio:false,
      plugins:{legend:{display:false}},
      scales:{
        x:{ticks:{color:'rgba(255,255,255,0.6)'},grid:{display:false}},
        y:{ticks:{color:'rgba(255,255,255,0.6)',precision:0},grid:{color:'rgba(255,255,255,0.06)'}}
      }
    }
  });
  
  const mix = [s.kpi.total_real, s.kpi.total_dummy];
  chartInstances.cMix = new Chart(document.getElementById('cMix'), {
    type:'pie',
    data:{
      labels:[t('real'), t('dummy')],
      datasets:[{data:mix,backgroundColor:['#5fe3d6','rgba(255,255,255,0.3)']}]
    },
    options:{
      responsive:true,
      maintainAspectRatio:false,
      plugins:{legend:{position:'right',labels:{color:'#ffffff'}}}
    }
  });
}

// Initialize
const savedLang = localStorage.getItem('adminLang') || 'en';
currentLang = savedLang;
setLang(savedLang);

fetch('/api/admin/stats')
  .then(r=>r.json())
  .then(charts)
  .catch(e=>console.warn('stats',e));

fDummy.onchange = load;
fStatus.onchange = load;
load();

// Read/Unread filter handling
let currentReadFilter = '';
document.getElementById('fAll').addEventListener('click', function() {
  setReadFilter('');
  setActiveReadButton(this);
});
document.getElementById('fUnread').addEventListener('click', function() {
  setReadFilter('unread');
  setActiveReadButton(this);
});
document.getElementById('fRead').addEventListener('click', function() {
  setReadFilter('read');
  setActiveReadButton(this);
});

function setReadFilter(filter) {
  currentReadFilter = filter;
  load();
}

function setActiveReadButton(activeBtn) {
  document.querySelectorAll('.read-status button').forEach(btn => {
    btn.classList.remove('active');
  });
  activeBtn.classList.add('active');
}

// Mark as read/unread functions
function markAsRead(id) {
  fetch('/api/admin/bookings/' + id + '/mark-read', {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({read_status: 'read'})
  }).then(() => load()).catch(console.error);
}

function markAsUnread(id) {
  fetch('/api/admin/bookings/' + id + '/mark-read', {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({read_status: 'unread'})
  }).then(() => load()).catch(console.error);
}

</script>
</body></html>"""



@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
# Medical Records API Endpoints for Dr. Diana Sánchez System

@app.route("/api/admin/visits", methods=["GET"])
def admin_list_visits():
    """Get all visits for admin panel"""
    if not _admin_authed():
        return jsonify({"error": "unauthorized"}), 401
    
    try:
        conn = _db()
        cur = conn.cursor()
        cur.execute("""
            SELECT v.id, v.booking_id, v.patient_name, v.patient_email, v.patient_phone,
                   v.visit_date, v.visit_time, v.chief_complaint, v.diagnosis, 
                   v.visit_status, v.created_at, b.service
            FROM visits v
            LEFT JOIN bookings b ON v.booking_id = b.id
            ORDER BY v.visit_date DESC, v.visit_time DESC
        """)
        cols = [d[0] for d in cur.description]
        visits = [dict(zip(cols, row)) for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        return jsonify({"visits": visits})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/visits/<int:visit_id>", methods=["GET"])
def admin_get_visit(visit_id):
    """Get detailed visit information"""
    if not _admin_authed():
        return jsonify({"error": "unauthorized"}), 401
    
    try:
        conn = _db()
        cur = conn.cursor()
        
        # Get visit details
        cur.execute("""
            SELECT v.*, b.service, b.message as booking_message
            FROM visits v
            LEFT JOIN bookings b ON v.booking_id = b.id
            WHERE v.id = %s
        """, (visit_id,))
        visit = cur.fetchone()
        
        if not visit:
            return jsonify({"error": "Visit not found"}), 404
        
        cols = [d[0] for d in cur.description]
        visit_data = dict(zip(cols, visit))
        
        # Get medications for this visit
        cur.execute("""
            SELECT * FROM medications WHERE visit_id = %s ORDER BY prescribed_date
        """, (visit_id,))
        medications = [dict(zip([d[0] for d in cur.description], row)) for row in cur.fetchall()]
        
        # Get symptoms for this visit
        cur.execute("""
            SELECT * FROM symptoms WHERE visit_id = %s ORDER BY recorded_at
        """, (visit_id,))
        symptoms = [dict(zip([d[0] for d in cur.description], row)) for row in cur.fetchall()]
        
        # Get patient history
        cur.execute("""
            SELECT * FROM patient_history WHERE patient_email = %s
        """, (visit_data["patient_email"],))
        history_row = cur.fetchone()
        patient_history = dict(zip([d[0] for d in cur.description], history_row)) if history_row else {}
        
        cur.close()
        conn.close()
        
        return jsonify({
            "visit": visit_data,
            "medications": medications,
            "symptoms": symptoms,
            "patient_history": patient_history
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/visits", methods=["POST"])
def admin_create_visit():
    """Create a new visit from booking"""
    if not _admin_authed():
        return jsonify({"error": "unauthorized"}), 401
    
    data = request.get_json(silent=True) or {}
    booking_id = data.get("booking_id")
    
    if not booking_id:
        return jsonify({"error": "booking_id required"}), 400
    
    try:
        conn = _db()
        cur = conn.cursor()
        
        # Get booking information
        cur.execute("SELECT * FROM bookings WHERE id = %s", (booking_id,))
        booking = cur.fetchone()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        
        booking_cols = [d[0] for d in cur.description]
        booking_data = dict(zip(booking_cols, booking))
        
        # Create visit
        cur.execute("""
            INSERT INTO visits (booking_id, patient_name, patient_email, patient_phone,
                              visit_date, visit_time, chief_complaint, ai_history)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            booking_id,
            booking_data["name"],
            booking_data["email"],
            booking_data["phone"],
            booking_data["preferred_date"],
            booking_data["preferred_time"],
            booking_data["message"],
            f"AI Analysis for {booking_data['name']} - Service: {booking_data['service']} - Initial assessment pending."
        ))
        
        visit_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"visit_id": visit_id, "success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/visits/<int:visit_id>", methods=["PUT"])
def admin_update_visit(visit_id):
    """Update visit information"""
    if not _admin_authed():
        return jsonify({"error": "unauthorized"}), 401
    
    data = request.get_json(silent=True) or {}
    
    try:
        conn = _db()
        cur = conn.cursor()
        
        # Update visit
        update_fields = []
        params = []
        
        for field in ["symptoms", "vital_signs", "physical_examination", "diagnosis", 
                     "treatment_plan", "follow_up_instructions", "next_appointment", 
                     "visit_status", "doctor_notes", "medications_prescribed"]:
            if field in data:
                update_fields.append(f"{field} = %s")
                params.append(data[field])
        
        if update_fields:
            update_fields.append("updated_at = NOW()")
            params.append(visit_id)
            
            query = f"UPDATE visits SET {', '.join(update_fields)} WHERE id = %s"
            cur.execute(query, params)
            conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/visits/<int:visit_id>/medications", methods=["POST"])
def admin_add_medication(visit_id):
    """Add medication to visit"""
    if not _admin_authed():
        return jsonify({"error": "unauthorized"}), 401
    
    data = request.get_json(silent=True) or {}
    
    try:
        conn = _db()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO medications (visit_id, medication_name, dosage, frequency, duration, instructions)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            visit_id,
            data.get("medication_name"),
            data.get("dosage"),
            data.get("frequency"),
            data.get("duration"),
            data.get("instructions")
        ))
        
        med_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"medication_id": med_id, "success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/visits/<int:visit_id>/symptoms", methods=["POST"])
def admin_add_symptom(visit_id):
    """Add symptom to visit"""
    if not _admin_authed():
        return jsonify({"error": "unauthorized"}), 401
    
    data = request.get_json(silent=True) or {}
    
    try:
        conn = _db()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO symptoms (visit_id, symptom_name, severity, duration, description)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            visit_id,
            data.get("symptom_name"),
            data.get("severity"),
            data.get("duration"),
            data.get("description")
        ))
        
        symptom_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"symptom_id": symptom_id, "success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/visits/<int:visit_id>/complete", methods=["POST"])
def admin_complete_visit(visit_id):
    """Complete visit and send summary email"""
    if not _admin_authed():
        return jsonify({"error": "unauthorized"}), 401
    
    try:
        conn = _db()
        cur = conn.cursor()
        
        # Get visit details with medications and symptoms
        cur.execute("""
            SELECT v.*, 
                   COALESCE(
                       array_agg(DISTINCT m.medication_name || ' - ' || m.dosage || ' - ' || m.frequency) 
                       FILTER (WHERE m.id IS NOT NULL), 
                       '{}'
                   ) as medications,
                   COALESCE(
                       array_agg(DISTINCT s.symptom_name || ' (Severity: ' || s.severity || '/10)') 
                       FILTER (WHERE s.id IS NOT NULL), 
                       '{}'
                   ) as symptoms
            FROM visits v
            LEFT JOIN medications m ON v.id = m.visit_id
            LEFT JOIN symptoms s ON v.id = s.visit_id
            WHERE v.id = %s
            GROUP BY v.id
        """, (visit_id,))
        
        visit = cur.fetchone()
        if not visit:
            cur.close()
            conn.close()
            return jsonify({"error": "Visit not found"}), 404
        
        cols = [d[0] for d in cur.description]
        visit_data = dict(zip(cols, visit))
        
        # Update visit status
        cur.execute("UPDATE visits SET visit_status = 'completed', updated_at = NOW() WHERE id = %s", (visit_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        # Send completion email
        try:
            from notify import send_visit_completion_notice
            doctor_email = "drasanchezd94@gmail.com"
            
            # Clean up medications and symptoms arrays
            medications = [med for med in (visit_data.get('medications') or []) if med and med.strip()]
            symptoms = [symptom for symptom in (visit_data.get('symptoms') or []) if symptom and symptom.strip()]
            
            # Prepare email data
            email_data = {
                "patient_name": visit_data.get('patient_name'),
                "visit_date": str(visit_data.get('visit_date', '')),
                "visit_time": str(visit_data.get('visit_time', '')),
                "diagnosis": visit_data.get('diagnosis', ''),
                "treatment_plan": visit_data.get('treatment_plan', ''),
                "follow_up_instructions": visit_data.get('follow_up_instructions', ''),
                "medications": medications,
                "symptoms": symptoms
            }
            
            email_sent = send_visit_completion_notice(
                email_data, 
                visit_data.get('patient_email'), 
                doctor_email
            )
            
            return jsonify({
                "success": True, 
                "visit_data": visit_data,
                "email_sent": email_sent
            })
            
        except Exception as email_error:
            print(f"Email sending failed: {email_error}")
            return jsonify({
                "success": True, 
                "visit_data": visit_data,
                "email_sent": False,
                "email_error": str(email_error)
            })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def admin_complete_visit(visit_id):
    """Complete visit and send summary email"""
    if not _admin_authed():
        return jsonify({"error": "unauthorized"}), 401
    
    try:
        conn = _db()
        cur = conn.cursor()
        
        # Get visit details
        cur.execute("""
            SELECT v.*, 
                   array_agg(DISTINCT m.medication_name || ' - ' || m.dosage || ' - ' || m.frequency) as medications,
                   array_agg(DISTINCT s.symptom_name || ' (Severity: ' || s.severity || ')') as symptoms
            FROM visits v
            LEFT JOIN medications m ON v.id = m.visit_id
            LEFT JOIN symptoms s ON v.id = s.visit_id
            WHERE v.id = %s
            GROUP BY v.id
        """, (visit_id,))
        
        visit = cur.fetchone()
        if not visit:
            return jsonify({"error": "Visit not found"}), 404
        
        cols = [d[0] for d in cur.description]
        visit_data = dict(zip(cols, visit))
        
        # Update visit status
        cur.execute("UPDATE visits SET visit_status = 'completed', updated_at = NOW() WHERE id = %s", (visit_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        # Send completion email (integrate with existing notify system)
        # This will be implemented next
        
        return jsonify({"success": True, "visit_data": visit_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
