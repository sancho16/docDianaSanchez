from pathlib import Path
import subprocess

REMOTE_HOST = "beckham23@192.168.0.131"
REMOTE_APP = "/home/beckham23/diana-booking-backend/app.py"
LOCAL_BACKUP = Path("/Users/juliansanchez/docDianaSanchez/scripts/remote-app.py.backup")

# --- Patched styles to inject into the ADMIN_VIEW_HTML <style> block ---
STYLE_BLOCK = """
/* ── Admin appointment cards ── */
.appointments-grid{display:flex;flex-direction:column;gap:1.2rem}
.appointment-card{cursor:pointer}
.card-inner{position:relative;width:100%;transition:transform .35s ease;transform-style:preserve-3d}
.card-inner.flipped{transform:rotateY(180deg)}
.card-front,.card-back{backface-visibility:hidden;-webkit-backface-visibility:hidden;border-radius:18px;border:1px solid var(--glass-border);background:var(--glass-bg);backdrop-filter:blur(16px) saturate(180%);-webkit-backdrop-filter:blur(16px) saturate(180%);box-shadow:0 8px 32px var(--shadow);padding:1.2rem;color:var(--text-primary)}
.card-front{position:relative;z-index:2}
.card-back{position:absolute;inset:0;z-index:3;transform:rotateY(180deg);display:flex;flex-direction:column;gap:16px;padding:1.2rem;overflow:auto}
.appointment-header{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.patient-name{font-size:1rem;font-weight:600;color:var(--white)}
.status-badge{padding:3px 10px;border-radius:999px;font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.03em}
.status-pending{background:rgba(232,245,154,.2);color:#e8f59a;border:1px solid rgba(232,245,154,.3)}
.status-confirmed{background:rgba(154,242,201,.2);color:#9af2c9;border:1px solid rgba(154,242,201,.3)}
.status-completed{background:rgba(159,217,242,.2);color:#9fd9f2;border:1px solid rgba(159,217,242,.3)}
.status-cancelled{background:rgba(245,154,154,.2);color:#f59a9a;border:1px solid rgba(245,154,154,.3)}
.appointment-summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.5rem .75rem}
.summary-item{font-size:.9rem;color:var(--text-secondary);display:flex;align-items:center;gap:.4rem}
.tap-hint{font-size:.78rem;color:var(--text-muted);margin-top:.8rem}
.appointment-details{display:flex;flex-direction:column;gap:.6rem}
.detail-row{display:flex;justify-content:space-between;gap:1rem;font-size:.9rem}
.detail-label{color:var(--text-muted)}
.detail-value{color:var(--text-primary);font-weight:500;word-break:break-word}
.card-actions{display:flex;flex-wrap:wrap;gap:.5rem}
.card-actions-row{display:flex;gap:.5rem;flex-wrap:wrap}
.btn-secondary,.btn-primary,.btn-danger{padding:.45rem .9rem;border-radius:10px;font-size:.82rem;font-weight:700;cursor:pointer;border:0;transition:all .3s ease}
.btn-secondary{background:rgba(255,255,255,.08);color:var(--text-secondary);border:1px solid rgba(255,255,255,.15)}
.btn-primary{background:linear-gradient(135deg,#5fe3d0,#00b8a3);color:#001f25}
.btn-danger{background:#ef4444;color:#fff}
"""

# --- Patched HTML body markup near admin grid/table block ---
HTML_BLOCK = """
  <div id=\"appointmentsGrid\" class=\"appointments-grid\"></div>
"""

OLD_HTML_BLOCK = """
  <div id=\"appointmentsGrid\" class=\"appointments-grid\"></div>
  <div class=\"table-container\" style=\"display:none\">
    <table> ...
"""

# Best-effort injection.
if "</style>" in text and STYLE_BLOCK.strip() not in text:
    text = text.replace("</style>", STYLE_BLOCK + "\n</style>", 1)
if OLD_HTML_BLOCK.strip() in text:
    text = text.replace(OLD_HTML_BLOCK.strip(), HTML_BLOCK.strip(), 1)
app_py.write_text(text)
print('patched', app_py)
