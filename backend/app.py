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

# Directory for storing temporary visit drafts when DB permissions prevent creating real visits
DRAFTS_DIR = os.path.join(os.path.dirname(__file__), 'data', 'visit_drafts')


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
    
    # Capture device/tracking information
    ip_address = ip  # Already extracted above for rate limiting
    user_agent = request.headers.get("User-Agent", "")
    
    # Extract device info from request data (sent from frontend with underscore prefix)
    device_type = (data.get("_device_type") or "").strip() or None
    device_os = (data.get("_os") or "").strip() or None
    device_browser = (data.get("_browser") or "").strip() or None
    ip_city = (data.get("_ip_city") or "").strip() or None
    ip_country = (data.get("_ip_country") or "").strip() or None

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
               (name, phone, email, preferred_date, preferred_time, service, message, status, is_dummy,
                ip_address, device_type, device_os, device_browser, ip_city, ip_country)
               VALUES (%s,%s,%s,%s,%s,%s,%s,'pending',FALSE,%s,%s,%s,%s,%s,%s)
               RETURNING id, created_at""",
            (name, phone, email, preferred_date, preferred_time, service, message,
             ip_address, device_type, device_os, device_browser, ip_city, ip_country),
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
        
        # Fetch bookings using the live table columns
        query = """
            SELECT 
                id, name, phone, email, preferred_date, preferred_time,
                service, message, status, is_dummy, created_at, updated_at,
                ip_address, device_type, device_os, device_browser, ip_city, ip_country
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
                    id, name, phone, email,
                    
                    service, preferred_date, preferred_time, message, status,
                    
                    
                    
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
 .panel canvas{display:block;width:100% !important;aspect-ratio:1/1;max-height:min(300px,60vw)}
 
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
 .appointments-grid{
   display:grid;
   grid-template-columns:repeat(auto-fit,minmax(320px,1fr));
   gap:1.2rem;
   align-items:start;
 }
 .appointment-card{
   cursor:default;
   min-height:340px;
 }
 .card-inner{
   position:relative;
   width:100%;
   min-height:340px;
   display:flex;
   flex-direction:column;
   justify-content:space-between;
   border-radius:18px;
   border:1px solid var(--glass-border);
   background:var(--glass-bg);
   backdrop-filter:blur(16px) saturate(180%);
   -webkit-backdrop-filter:blur(16px) saturate(180%);
   box-shadow:0 8px 32px var(--shadow);
   padding:1.3rem;
   color:var(--text-primary);
   transition:box-shadow .25s ease;
 }
 .card-inner:hover{
   box-shadow:0 18px 40px rgba(0,0,0,.22);
 }
 .card-front,
 .card-back{
   position:static;
   transform:none;
   backface-visibility:visible;
   -webkit-backface-visibility:visible;
 }
 .appointment-header{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;margin-bottom:14px}
 .patient-name{font-size:1rem;font-weight:700;color:var(--white);line-height:1.2}
 .status-badge{padding:3px 10px;border-radius:999px;font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.03em}
 .status-pending{background:rgba(232,245,154,.2);color:#e8f59a;border:1px solid rgba(232,245,154,.3)}
 .status-confirmed{background:rgba(154,242,201,.2);color:#9af2c9;border:1px solid rgba(154,242,201,.3)}
 .status-completed{background:rgba(159,217,242,.2);color:#9fd9f2;border:1px solid rgba(159,217,242,.3)}
 .status-cancelled{background:rgba(245,154,154,.2);color:#f59a9a;border:1px solid rgba(245,154,154,.3)}
 .field-labels{display:flex;flex-wrap:wrap;gap:.65rem;margin-bottom:1rem;font-size:.72rem;color:var(--text-muted);}
 .field-label{white-space:nowrap;}
 .appointment-summary{display:grid;grid-template-columns:1fr;gap:.65rem;}
 .summary-item{font-size:.92rem;color:var(--text-secondary);display:flex;align-items:center;gap:.5rem}
 .tap-hint{font-size:.78rem;color:var(--text-muted);margin-top:.75rem}
 .appointment-tabs{display:flex;gap:.5rem;margin-top:1rem;flex-wrap:wrap}
 .tab-button{flex:1 1 120px;min-width:120px;background:rgba(255,255,255,.08);color:var(--text-secondary);border:1px solid rgba(255,255,255,.12);border-radius:999px;padding:.7rem 1rem;font-size:.84rem;font-weight:700;cursor:pointer;transition:all .25s ease}
 .tab-button.active{background:rgba(255,255,255,.18);color:#fff;border-color:rgba(255,255,255,.22)}
 .tab-panel{display:none;margin-top:1rem}
 .tab-panel.active{display:block}
 .appointment-details{display:grid;gap:.75rem}
 .detail-row{display:grid;grid-template-columns:auto 1fr;gap:.75rem;font-size:.92rem;align-items:start}
 .detail-label{color:var(--text-muted)}
 .detail-value{color:var(--text-primary);font-weight:500;word-break:break-word}
 .card-actions{display:flex;flex-wrap:wrap;gap:.65rem;margin-top:1rem}
 .btn-secondary,.btn-primary,.btn-danger{padding:.55rem 1rem;border-radius:10px;font-size:.82rem;font-weight:700;cursor:pointer;border:0;transition:all .3s ease}
 .btn-secondary{background:rgba(255,255,255,.08);color:var(--text-secondary);border:1px solid rgba(255,255,255,.15)}
 .btn-primary{background:linear-gradient(135deg,#5fe3d0,#00b8a3);color:#001f25}
 .btn-danger{background:#ef4444;color:#fff}
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
    <label style="flex-grow:1;max-width:300px"><span data-en="Search:" data-es="Buscar:">Search:</span>
      <input type="text" id="fSearch" placeholder="Name, phone, email..." style="width:100%;padding:0.6rem 1rem;border-radius:10px;border:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.06);color:var(--text-primary);font-size:0.9rem" />
    </label>
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
  
  <div class="container">
    <div id="appointmentsGrid" class="appointments-grid"></div>
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

function adminStatus(msg, isError=false){
  let el = document.getElementById('adminStatus');
  if(!el){
    el = document.createElement('div');
    el.id = 'adminStatus';
    el.style.cssText = 'position:fixed;left:12px;right:12px;bottom:12px;padding:.8rem 1rem;border-radius:12px;font:.85rem/1.3 system-ui,sans-serif;z-index:9999';
    document.body.appendChild(el);
  }
  el.style.background = isError ? 'rgba(255,107,107,0.22)' : 'rgba(95,227,214,0.18)';
  el.style.color = isError ? '#ffb3b3' : '#c7fff6';
  el.style.border = isError ? '1px solid rgba(255,107,107,0.35)' : '1px solid rgba(95,227,214,0.3)';
  el.textContent = '[admin] ' + msg;
}

function debugApi(path){
  const box = document.getElementById('adminDebug');
  const line = document.createElement('div');
  line.style.cssText='font-size:.75rem;padding:.25rem 0;border-bottom:1px solid rgba(255,255,255,0.08)';
  box.appendChild(line);
  try{
    fetch(path,{headers:{'X-Admin-Token': TOK()}}).then(async r=>{
      const body = await r.text().catch(()=>'<text-failed>');
      line.textContent = path + ' -> ' + r.status + ' ' + r.statusText + ' ; token=' + TOK() + ' ; body=' + String(body).slice(0,400);
    }).catch(e=> line.textContent = path + ' -> FETCH_ERR ' + e.message + ' ; token=' + TOK());
  }catch(e){ line.textContent = path + ' -> SCRIPT_ERR ' + e.message; }
}

function load() {
  fetch('/api/admin/bookings?'+qp(),{headers:{'X-Admin-Token': TOK()}})
  .then(r=>r.json().then(d => ({r,d})).catch(e=>({r:{status:0},d:{error:'Network error: '+String(e)}})))
  .then(o=>{
    if(o.r.status === 401 || o.r.status === 403){
      adminStatus('Unauthorized: ' + ((o.d && o.d.error) || o.r.status), true);
      location.href='/admin'; 
      return;
    }
    if(o.d && o.d.error){
      adminStatus('Backend error: ' + o.d.error, true);
      console.warn(o.d);
    } else {
      adminStatus('Loaded ' + ((o.d && o.d.count)||0) + ' appointments');
    }
    allData = (o.d && o.d.rows) || [];
    applyClientSideFilters();
    csv.href='/api/bookings.csv?dummy='+fDummy.value+'&token='+encodeURIComponent(TOK());
  });
}
let allData = [];
let filteredData = [];

// Apply client-side filters (search)
function applyClientSideFilters() {
  const searchTerm = (_fSearch ? _fSearch.value : '').toLowerCase().trim();
  
  if (!searchTerm) {
    // No search, show all data
    filteredData = allData;
  } else {
    // Filter by search term (name, phone, email, service, message)
    filteredData = allData.filter(booking => {
      const searchableText = [
        booking.name || '',
        booking.phone || '',
        booking.email || '',
        booking.service || '',
        booking.message || '',
        booking.preferred_date || '',
        booking.ip_address || '',
        booking.ip_city || '',
        booking.ip_country || ''
      ].join(' ').toLowerCase();
      
      return searchableText.includes(searchTerm);
    });
  }
  
  renderAppointmentsGrid();
  cnt.textContent = `${filteredData.length} ${t('appointments')}`;
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

fetch('/api/admin/stats',{headers:{'X-Admin-Token': TOK()}})
  .then(r=>r.json())
  .then(charts)
  .catch(e=>console.warn('stats',e));

// Safely wire filters if elements are present (avoid null addEventListener errors)
const _fDummy = document.getElementById('fDummy');
const _fStatus = document.getElementById('fStatus');
const _fSearch = document.getElementById('fSearch');
if (_fDummy) _fDummy.onchange = load;
if (_fStatus) _fStatus.onchange = load;
if (_fSearch) {
  // Debounced search - wait 300ms after user stops typing
  let searchTimeout;
  _fSearch.oninput = function() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      applyClientSideFilters();
    }, 300);
  };
}
load();

// Read/Unread filter handling
let currentReadFilter = '';
// Wire read-filter buttons only if they exist in the DOM
const _fAll = document.getElementById('fAll');
const _fUnread = document.getElementById('fUnread');
const _fRead = document.getElementById('fRead');
if (_fAll) _fAll.addEventListener('click', function() { setReadFilter(''); setActiveReadButton(this); });
if (_fUnread) _fUnread.addEventListener('click', function() { setReadFilter('unread'); setActiveReadButton(this); });
if (_fRead) _fRead.addEventListener('click', function() { setReadFilter('read'); setActiveReadButton(this); });

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
  fetch('/api/admin/bookings/' + id + '/mark-read', {headers:{'X-Admin-Token': TOK()},
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({read_status: 'read'})
  }).then(() => load()).catch(console.error);
}

function markAsUnread(id) {
  fetch('/api/admin/bookings/' + id + '/mark-read', {headers:{'X-Admin-Token': TOK()},
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({read_status: 'unread'})
  }).then(() => load()).catch(console.error);
}


// Use a window-scoped flag to avoid temporal-dead-zone issues when scripts execute
window.appointmentInteractionsInitialized = window.appointmentInteractionsInitialized || false;

function renderAppointmentsGrid() {
  const grid = document.getElementById('appointmentsGrid') || createAppointmentsGrid();
  
  if (filteredData.length === 0) {
    grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:3rem;color:var(--text-muted)">No appointments found</div>';
    initAppointmentInteractions();
    return;
  }
  
  grid.innerHTML = filteredData.map(booking => createAppointmentCard(booking)).join('');
  initAppointmentInteractions();
}

function createAppointmentsGrid() {
  const grid = document.createElement('div');
  grid.id = 'appointmentsGrid';
  grid.className = 'appointments-grid';
  document.querySelector('.container').appendChild(grid);
  return grid;
}

function createAppointmentCard(booking) {
  const statusClass = `status-${booking.status || 'pending'}`;
  const statusLabel = getStatusLabel(booking.status || 'pending');
  const date = formatDate(booking.preferred_date);
  const time = booking.preferred_time || 'Not specified';

  return `
    <div class="appointment-card" data-id="${booking.id}" data-status="${booking.status || 'pending'}">
      <div class="card-inner">
        <div class="field-labels">
          <span class="field-label">Name</span>
          <span class="field-label">Phone</span>
          <span class="field-label">Email</span>
          <span class="field-label">Date</span>
          <span class="field-label">Time</span>
          <span class="field-label">Service</span>
        </div>
        <div class="appointment-header">
          <div class="patient-name">${escapeHtml(booking.name)}</div>
          <div class="status-badge ${statusClass}">${statusLabel}</div>
        </div>
        <div class="appointment-summary tab-panel active" data-panel="summary">
          <div class="summary-item">📅 ${date}</div>
          <div class="summary-item">⏰ ${time}</div>
          ${booking.service ? `<div class="summary-item">🩺 ${escapeHtml(booking.service)}</div>` : ''}
          <div class="tap-hint">Select “Details” for full patient information.</div>
        </div>
        <div class="appointment-details tab-panel" data-panel="details">
          <div class="detail-row">
            <span class="detail-label">Patient:</span>
            <span class="detail-value">${escapeHtml(booking.name)}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Email:</span>
            <span class="detail-value">${escapeHtml(booking.email || 'Not provided')}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Phone:</span>
            <span class="detail-value">${escapeHtml(booking.phone || 'Not provided')}</span>
          </div>
          ${booking.service ? `<div class="detail-row"><span class="detail-label">Service:</span><span class="detail-value">${escapeHtml(booking.service)}</span></div>` : ''}
          <div class="detail-row"><span class="detail-label">Status:</span><span class="detail-value">${statusLabel}</span></div>
        </div>
        <div class="appointment-tabs">
          <button type="button" class="tab-button active" data-tab="summary">Summary</button>
          <button type="button" class="tab-button" data-tab="details">Details</button>
        </div>
        <div class="card-actions">
          <button class="btn btn-primary" data-act="view">Open full</button>
          <button class="btn btn-primary" data-act="confirm">Confirm</button>
          <button class="btn btn-danger" data-act="cancel">Cancel</button>
        </div>
      </div>
    </div>
  `;
}

function getStatusLabel(status) {
  const labels = {'pending': 'Pending', 'confirmed': 'Confirmed', 'cancelled': 'Cancelled', 'completed':'Completed'};
  return labels[status] || 'Pending';
}

function formatDate(dateStr) {
  if (!dateStr) return 'Not specified';
  try {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', { weekday:'short', month:'short', day:'numeric' });
  } catch (e) {
    return dateStr || 'Not specified';
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text || '';
  return div.innerHTML;
}

function initAppointmentInteractions() {
  if (window.appointmentInteractionsInitialized) return;
  window.appointmentInteractionsInitialized = true;

  console.log && console.log('[admin-debug] initAppointmentInteractions()');

  document.addEventListener('click', (e) => {
    const tabButton = e.target.closest('[data-tab]');
    if (tabButton) {
      const card = tabButton.closest('.appointment-card');
      if (!card) return;
      const panelName = tabButton.getAttribute('data-tab');
      console.log && console.log('[admin-debug] tab click', panelName, card && card.getAttribute('data-id'));
      card.querySelectorAll('.tab-button').forEach(btn => btn.classList.toggle('active', btn === tabButton));
      card.querySelectorAll('.tab-panel').forEach(panel => panel.classList.toggle('active', panel.getAttribute('data-panel') === panelName));
      return;
    }

    const action = e.target.closest('[data-act]');
    if (action) {
      const card = action.closest('.appointment-card');
      const act = action.getAttribute('data-act');
      const id = card ? card.getAttribute('data-id') : null;
      console.log && console.log('[admin-debug] action', act, id);
      if (!id) return;
      if (act === 'view') {
        // Open the medical records form for the booking so doctor can work
        window.open('/admin/medical-records?booking_id=' + id, '_blank');
        return;
      }
      if (act === 'confirm') {
        // Confirm booking, then open medical records for the visit so the doctor can start notes
        patchStatus(id, 'confirmed').then(() => {
          try { window.open('/admin/medical-records?booking_id=' + id, '_blank'); } catch (e) { console.error(e); }
        }).catch(err => { console.error('Confirm failed', err); });
        return;
      }
      if (act === 'cancel') { patchStatus(id, 'cancelled'); return; }
      return;
    }
  });

  document.addEventListener('dblclick', (e) => {
    const card = e.target.closest('.appointment-card');
    if (!card) return;
    const id = card.getAttribute('data-id');
    if (id) window.open('/admin/appointment/' + id, '_blank');
  });
}

function confirmAppointment(id) { patchStatus(id, 'confirmed'); }
function cancelAppointment(id) { patchStatus(id, 'cancelled'); }

async function patchStatus(id, status) {
  const card = document.querySelector('.appointment-card[data-id="' + id + '"]');
  const button = card ? card.querySelector('[data-act="' + status + '"]') : null;
  if (button) { button.disabled = true; button.textContent = status === 'confirmed' ? 'Confirming…' : 'Cancelling…'; }
  try {
    const res = await fetch('/api/admin/bookings/' + id, { method:'PATCH', headers:{'Content-Type':'application/json','X-Admin-Token': TOK()}, body: JSON.stringify({ status }) });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || ('HTTP ' + res.status));
    if (card) {
      const badge = card.querySelector('.status-badge');
      if (badge) { badge.className = 'status-badge status-' + status; badge.textContent = getStatusLabel(status); }
      const hint = card.querySelector('.tap-hint');
      if (hint) hint.textContent = status === 'confirmed' ? 'Confirmed' : 'Cancelled';
    }
    showToast(status === 'confirmed' ? 'Appointment confirmed' : 'Appointment cancelled');
  } catch (err) {
    showToast(err.message || 'Action failed', 'error');
    if (button) { button.disabled = false; button.textContent = status === 'confirmed' ? 'Confirm' : 'Cancel'; }
  }
}

function showToast(message, type = 'success') {
  const el = document.createElement('div');
  el.style.cssText = 'position:fixed;top:18px;right:18px;z-index:12000;padding:12px 16px;border-radius:14px;color:#fff;font-weight:600;font-size:14px;background:' + (type === 'success' ? '#10b981' : '#ef4444') + ';box-shadow:0 10px 30px rgba(0,0,0,.25);opacity:0;transform:translateY(-10px);transition:all .35s ease';
  el.textContent = message;
  document.body.appendChild(el);
  requestAnimationFrame(() => { el.style.opacity = '1'; el.style.transform = 'translateY(0)'; });
  setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateY(-10px)'; setTimeout(() => el.remove(), 400); }, 2400);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAppointmentInteractions);
} else {
  initAppointmentInteractions();
}</script>
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
        # If database permissions prevent creating a real visit, create a local draft fallback
        err = str(e)
        try:
            if 'permission denied' in err.lower() or 'insufficient privilege' in err.lower():
                os.makedirs(DRAFTS_DIR, exist_ok=True)
                draft_id = f"draft-{int(time.time() * 1000)}"
                path = os.path.join(DRAFTS_DIR, draft_id + ".json")
                payload = {"draft_id": draft_id, "booking_id": booking_id, "error": err, "created_at": datetime.utcnow().isoformat()}
                with open(path, "w") as f:
                    json.dump(payload, f)
                return jsonify({"visit_id": draft_id, "success": True, "draft": True})
        except Exception as e2:
            # fall through to send original error
            err = f"{err}; fallback failed: {e2}"
        return jsonify({"error": err}), 500


@app.route("/api/admin/visits/draft", methods=["POST"])
def admin_create_visit_draft():
  """Create a local draft visit when DB write permissions are unavailable."""
  if not _admin_authed():
    return jsonify({"error": "unauthorized"}), 401
  data = request.get_json(silent=True) or {}
  try:
    os.makedirs(DRAFTS_DIR, exist_ok=True)
    draft_id = f"draft-{int(time.time() * 1000)}"
    path = os.path.join(DRAFTS_DIR, draft_id + ".json")
    payload = {"draft_id": draft_id, "booking_id": data.get("booking_id"), "data": data, "created_at": datetime.utcnow().isoformat()}
    with open(path, "w") as f:
      json.dump(payload, f)
    return jsonify({"visit_id": draft_id, "success": True})
  except Exception as e:
    return jsonify({"error": str(e)}), 500


@app.route("/api/admin/visits/draft/<draft_id>", methods=["PUT"])
def admin_update_visit_draft(draft_id):
  if not _admin_authed():
    return jsonify({"error": "unauthorized"}), 401
  data = request.get_json(silent=True) or {}
  try:
    os.makedirs(DRAFTS_DIR, exist_ok=True)
    path = os.path.join(DRAFTS_DIR, draft_id + ".json")
    existing = {}
    if os.path.exists(path):
      with open(path, "r") as f:
        existing = json.load(f)
    existing["data"] = data
    existing["updated_at"] = datetime.utcnow().isoformat()
    with open(path, "w") as f:
      json.dump(existing, f)
    return jsonify({"success": True})
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
        
        for field in ["chief_complaint", "symptoms", "vital_signs", "physical_examination", "diagnosis", 
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
        
        # Get booking_id from visit
        booking_id = visit_data.get('booking_id')
        
        # Update visit status to completed
        cur.execute("UPDATE visits SET visit_status = 'completed', updated_at = NOW() WHERE id = %s", (visit_id,))
        
        # Update related booking status to completed
        if booking_id:
            cur.execute("UPDATE bookings SET status = 'completed', updated_at = NOW() WHERE id = %s", (booking_id,))
        
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


MEDICAL_RECORDS_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medical Records - {{ booking.name }}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        :root {
            --bg-gradient-start: #001f25; --bg-gradient-end: #003d47;
            --glass-bg: rgba(255,255,255,0.08); --glass-border: rgba(255,255,255,0.12);
            --text-primary: #ffffff; --text-secondary: rgba(255,255,255,0.75);
            --text-muted: rgba(255,255,255,0.5); --accent: #5fe3d6;
            --accent-hover: #00b8a3; --shadow: rgba(0,0,0,0.3);
            --success: #10b981; --error: #ef4444;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 100%);
            color: var(--text-primary); min-height: 100vh; overflow-x: hidden; padding: 1rem;
        }
        .medical-container { max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
        .medical-panel {
            background: var(--glass-bg); backdrop-filter: blur(24px) saturate(180%);
            -webkit-backdrop-filter: blur(24px) saturate(180%); border: 1px solid var(--glass-border);
            border-radius: 16px; padding: 1.5rem; box-shadow: 0 8px 32px var(--shadow);
        }
        .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; border-bottom: 2px solid var(--accent); padding-bottom: 1rem; }
        .panel-title { font-size: 1.3rem; font-weight: 700; color: var(--accent); }
        .close-btn {
            background: var(--error); color: white; border: none; width: 32px; height: 32px;
            border-radius: 50%; cursor: pointer; display: flex; align-items: center;
            justify-content: center; font-weight: bold; aspect-ratio: 1 / 1; transition: all 0.3s ease;
        }
        .close-btn:hover { transform: scale(1.1); box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4); }
        .patient-info { background: rgba(95, 227, 214, 0.1); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem; border-left: 4px solid var(--accent); }
        .patient-info h3 { color: var(--accent); margin-bottom: 1rem; font-size: 1.1rem; }
        .patient-details { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }
        .detail-item { display: flex; flex-direction: column; gap: 0.4rem; }
        .detail-label { font-size: 0.8rem; color: var(--text-secondary); font-weight: 500; }
        .detail-value { color: var(--text-primary); font-weight: 600; font-size: 0.95rem; }
        .form-section { margin-bottom: 1.5rem; }
        .section-title { font-size: 1rem; font-weight: 600; color: var(--accent); margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--glass-border); }
        .form-group { margin-bottom: 1rem; }
        .form-label { display: block; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.5rem; font-weight: 500; }
        .form-input, .form-textarea, .form-select {
            width: 100%; padding: 0.7rem; border: 2px solid var(--glass-border);
            border-radius: 8px; background: var(--glass-bg); color: var(--text-primary);
            font-size: 0.9rem; transition: all 0.3s ease;
        }
        .form-input:focus, .form-textarea:focus, .form-select:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px rgba(95, 227, 214, 0.2); }
        .form-textarea { min-height: 70px; resize: vertical; font-family: inherit; }
        .action-buttons { display: flex; gap: 1rem; margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid var(--glass-border); }
        .btn-primary, .btn-secondary { padding: 0.75rem 1.5rem; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.3s ease; font-size: 0.9rem; }
        .btn-primary { background: var(--accent); color: #000; flex: 1; }
        .btn-primary:hover { background: var(--accent-hover); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(95, 227, 214, 0.3); }
        .btn-secondary { background: transparent; color: var(--text-secondary); border: 2px solid var(--glass-border); }
        .btn-secondary:hover { border-color: var(--accent); color: var(--accent); }
        @media (max-width: 1024px) { .medical-container { grid-template-columns: 1fr; gap: 1rem; } }
    </style>
</head>
<body>
    <div class="medical-container">
        <div class="medical-panel">
            <div class="panel-header">
                <h2 class="panel-title">Medical Record</h2>
                <button class="close-btn" onclick="window.close()" title="Close">&times;</button>
            </div>
            <div class="patient-info">
                <h3>Patient Information</h3>
                <div class="patient-details">
                    <div class="detail-item"><span class="detail-label">Name</span><span class="detail-value">{{ booking.name }}</span></div>
                    <div class="detail-item"><span class="detail-label">Email</span><span class="detail-value">{{ booking.email or 'N/A' }}</span></div>
                    <div class="detail-item"><span class="detail-label">Phone</span><span class="detail-value">{{ booking.phone }}</span></div>
                    <div class="detail-item"><span class="detail-label">Service</span><span class="detail-value">{{ booking.service or 'General Consultation' }}</span></div>
                    <div class="detail-item"><span class="detail-label">Date & Time</span><span class="detail-value">{{ booking.preferred_date or 'Not specified' }} {{ booking.preferred_time or '' }}</span></div>
                    {% if booking.message %}
                    <div class="detail-item" style="grid-column: 1 / -1;"><span class="detail-label">Patient Message</span><span class="detail-value">"{{ booking.message }}"</span></div>
                    {% endif %}
                </div>
            </div>
            <form id="medical-form" onsubmit="return saveMedicalRecord(event)">
                <input type="hidden" name="booking_id" value="{{ booking.id }}">
                <div class="form-section">
                    <h3 class="section-title">Chief Complaint & Examination</h3>
                    <div class="form-group"><label class="form-label">Chief Complaint</label><textarea class="form-textarea" name="chief_complaint" placeholder="Patient's main concern..."></textarea></div>
                    <div class="form-group"><label class="form-label">Physical Examination</label><textarea class="form-textarea" name="physical_examination" placeholder="Physical examination findings..."></textarea></div>
                </div>
                <div class="form-section">
                    <h3 class="section-title">Diagnosis & Treatment</h3>
                    <div class="form-group"><label class="form-label">Diagnosis</label><textarea class="form-textarea" name="diagnosis" placeholder="Primary and secondary diagnoses..." required></textarea></div>
                    <div class="form-group"><label class="form-label">Treatment Plan</label><textarea class="form-textarea" name="treatment_plan" placeholder="Treatment recommendations..." required></textarea></div>
                </div>
                <div class="form-section">
                    <h3 class="section-title">Follow-up</h3>
                    <div class="form-group"><label class="form-label">Follow-up Instructions</label><textarea class="form-textarea" name="follow_up_instructions" placeholder="Follow-up care..."></textarea></div>
                    <div class="form-group"><label class="form-label">Next Appointment</label><input type="date" class="form-input" name="next_appointment"></div>
                    <div class="form-group"><label class="form-label">Doctor's Notes</label><textarea class="form-textarea" name="doctor_notes" placeholder="Additional notes..."></textarea></div>
                </div>
                <div class="action-buttons">
                    <button type="submit" class="btn-primary">Save Medical Record</button>
                    <button type="button" class="btn-secondary" onclick="window.close()">Cancel</button>
                </div>
            </form>
        </div>
        <div class="medical-panel">
            <div class="panel-header"><h2 class="panel-title">Booking Details</h2></div>
            <div class="form-section">
                <h3 class="section-title">Appointment Status</h3>
                <div class="patient-details">
                    <div class="detail-item"><span class="detail-label">Status</span><span class="detail-value" style="text-transform: capitalize;">{{ booking.status }}</span></div>
                    <div class="detail-item"><span class="detail-label">Booking ID</span><span class="detail-value">#{{ booking.id }}</span></div>
                    <div class="detail-item"><span class="detail-label">Created</span><span class="detail-value">{{ booking.created_at }}</span></div>
                </div>
            </div>
            {% if booking.ip_address %}
            <div class="form-section">
                <h3 class="section-title">Device & Location</h3>
                <div class="patient-details">
                    <div class="detail-item"><span class="detail-label">IP Address</span><span class="detail-value">{{ booking.ip_address }}</span></div>
                    {% if booking.ip_city %}<div class="detail-item"><span class="detail-label">Location</span><span class="detail-value">{{ booking.ip_city }}, {{ booking.ip_country }}</span></div>{% endif %}
                    {% if booking.device_type %}<div class="detail-item"><span class="detail-label">Device</span><span class="detail-value">{{ booking.device_type }}</span></div>{% endif %}
                    {% if booking.device_os %}<div class="detail-item"><span class="detail-label">OS</span><span class="detail-value">{{ booking.device_os }}</span></div>{% endif %}
                    {% if booking.device_browser %}<div class="detail-item"><span class="detail-label">Browser</span><span class="detail-value">{{ booking.device_browser }}</span></div>{% endif %}
                </div>
            </div>
            {% endif %}
            {% if booking.address %}
            <div class="form-section">
                <h3 class="section-title">Visit Location</h3>
                <div class="patient-details">
                    <div class="detail-item" style="grid-column: 1 / -1;"><span class="detail-label">Address</span><span class="detail-value">{{ booking.address }}</span></div>
                    {% if booking.address_city %}<div class="detail-item"><span class="detail-label">City</span><span class="detail-value">{{ booking.address_city }}</span></div>{% endif %}
                    {% if booking.address_province %}<div class="detail-item"><span class="detail-label">Province</span><span class="detail-value">{{ booking.address_province }}</span></div>{% endif %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>
    <script>
        async function saveMedicalRecord(event) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            data.patient_name = "{{ booking.name }}";
            data.patient_email = "{{ booking.email or '' }}";
            data.patient_phone = "{{ booking.phone }}";
            data.visit_date = "{{ booking.preferred_date or '' }}";
            data.visit_time = "{{ booking.preferred_time or '' }}";
            try {
                const response = await fetch('/api/admin/visits', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                if (result.success || result.ok || result.visit_id) {
                    alert('Medical record saved successfully!');
                    window.close();
                } else {
                    alert('Error: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
            return false;
        }
    </script>
</body>
</html>
'''

@app.route("/admin/medical-records", methods=["GET"])
def admin_medical_records():
    """Serve medical records page for a specific booking"""
    if not _admin_authed():
        return redirect(url_for("admin_login_page"))
    
    booking_id = request.args.get("booking_id")
    if not booking_id:
        return jsonify({"error": "booking_id required"}), 400
    
    try:
        conn = _db()
        cur = conn.cursor()
        
        query = """
            SELECT 
                id, name, phone, email,
                
                service, preferred_date, preferred_time, message, status,
                
                
                
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
            return "Booking not found", 404
        
        booking = dict(zip(cols, row))
        
        for key in ['created_at', 'updated_at']:
            if booking.get(key):
                booking[key] = booking[key].strftime('%Y-%m-%d %H:%M')
        for key in ['preferred_date', 'preferred_time']:
            if booking.get(key):
                booking[key] = str(booking[key])
        
        if booking.get('message'):
            booking['message'] = booking['message'].replace('[READ] ', '').replace('[READ]', '')
        
        cur.close()
        conn.close()
        
        return render_template_string(MEDICAL_RECORDS_TEMPLATE, booking=booking)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
