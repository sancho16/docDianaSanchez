#!/usr/bin/env python3
"""
Script to add the /admin/medical-records route to app.py
This route will serve the medical records page dynamically with appointment data
"""

import sys

# The medical records HTML template (will be embedded in app.py)
MEDICAL_RECORDS_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medical Records - Dr. Diana Sánchez</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        :root {
            --bg-gradient-start: #001f25;
            --bg-gradient-end: #003d47;
            --glass-bg: rgba(255,255,255,0.08);
            --glass-border: rgba(255,255,255,0.12);
            --text-primary: #ffffff;
            --text-secondary: rgba(255,255,255,0.75);
            --text-muted: rgba(255,255,255,0.5);
            --accent: #5fe3d6;
            --accent-hover: #00b8a3;
            --shadow: rgba(0,0,0,0.3);
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 100%);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
            padding: 2rem;
        }

        .medical-container {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }

        .medical-panel {
            background: var(--glass-bg);
            backdrop-filter: blur(24px) saturate(180%);
            -webkit-backdrop-filter: blur(24px) saturate(180%);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 8px 32px var(--shadow);
        }

        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            border-bottom: 2px solid var(--accent);
            padding-bottom: 1rem;
        }

        .panel-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent);
        }

        .close-btn {
            background: var(--error);
            color: white;
            border: none;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            aspect-ratio: 1 / 1;
        }

        .patient-info {
            background: rgba(95, 227, 214, 0.1);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border-left: 4px solid var(--accent);
        }

        .patient-info h3 {
            color: var(--accent);
            margin-bottom: 1rem;
            font-size: 1.2rem;
        }

        .patient-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }

        .detail-item {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .detail-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .detail-value {
            color: var(--text-primary);
            font-weight: 600;
        }

        .form-section {
            margin-bottom: 2rem;
        }

        .section-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--accent);
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--glass-border);
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-label {
            display: block;
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
            font-weight: 500;
        }

        .form-input, .form-textarea, .form-select {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid var(--glass-border);
            border-radius: 8px;
            background: var(--glass-bg);
            color: var(--text-primary);
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }

        .form-input:focus, .form-textarea:focus, .form-select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(95, 227, 214, 0.2);
        }

        .form-textarea {
            min-height: 80px;
            resize: vertical;
        }

        .action-buttons {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 1px solid var(--glass-border);
        }

        .btn-primary, .btn-secondary {
            padding: 0.75rem 2rem;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }

        .btn-primary {
            background: var(--accent);
            color: #000;
        }

        .btn-primary:hover {
            background: var(--accent-hover);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(95, 227, 214, 0.3);
        }

        .btn-secondary {
            background: transparent;
            color: var(--text-secondary);
            border: 2px solid var(--glass-border);
        }

        .btn-secondary:hover {
            border-color: var(--accent);
            color: var(--accent);
        }

        @media (max-width: 1024px) {
            .medical-container {
                grid-template-columns: 1fr;
                gap: 1rem;
                padding: 1rem;
            }
            
            body {
                padding: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="medical-container">
        <!-- Left Panel - Current Visit -->
        <div class="medical-panel">
            <div class="panel-header">
                <h2 class="panel-title">Medical Record</h2>
                <button class="close-btn" onclick="window.close()" title="Close">&times;</button>
            </div>

            <div class="patient-info">
                <h3>Patient Information</h3>
                <div class="patient-details">
                    <div class="detail-item">
                        <span class="detail-label">Name</span>
                        <span class="detail-value">{{ booking.name }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Email</span>
                        <span class="detail-value">{{ booking.email or 'N/A' }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Phone</span>
                        <span class="detail-value">{{ booking.phone }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Service</span>
                        <span class="detail-value">{{ booking.service or 'General Consultation' }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Date & Time</span>
                        <span class="detail-value">{{ booking.preferred_date or 'Not specified' }} {{ booking.preferred_time or '' }}</span>
                    </div>
                    {% if booking.message %}
                    <div class="detail-item" style="grid-column: 1 / -1;">
                        <span class="detail-label">Patient Message</span>
                        <span class="detail-value">"{{ booking.message }}"</span>
                    </div>
                    {% endif %}
                </div>
            </div>

            <form id="medical-form" action="/api/admin/visits" method="POST">
                <input type="hidden" name="booking_id" value="{{ booking.id }}">
                
                <div class="form-section">
                    <h3 class="section-title">Chief Complaint & Examination</h3>
                    <div class="form-group">
                        <label class="form-label">Chief Complaint</label>
                        <textarea class="form-textarea" name="chief_complaint" placeholder="Patient's main concern or reason for visit..."></textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Physical Examination</label>
                        <textarea class="form-textarea" name="physical_examination" placeholder="Physical examination findings..."></textarea>
                    </div>
                </div>

                <div class="form-section">
                    <h3 class="section-title">Diagnosis & Treatment</h3>
                    <div class="form-group">
                        <label class="form-label">Diagnosis</label>
                        <textarea class="form-textarea" name="diagnosis" placeholder="Primary and secondary diagnoses..." required></textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Treatment Plan</label>
                        <textarea class="form-textarea" name="treatment_plan" placeholder="Treatment recommendations and plan..." required></textarea>
                    </div>
                </div>

                <div class="form-section">
                    <h3 class="section-title">Follow-up</h3>
                    <div class="form-group">
                        <label class="form-label">Follow-up Instructions</label>
                        <textarea class="form-textarea" name="follow_up_instructions" placeholder="Follow-up care instructions..."></textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Next Appointment (Optional)</label>
                        <input type="date" class="form-input" name="next_appointment">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Doctor's Notes</label>
                        <textarea class="form-textarea" name="doctor_notes" placeholder="Additional notes and observations..."></textarea>
                    </div>
                </div>

                <div class="action-buttons">
                    <button type="submit" class="btn-primary">Save Medical Record</button>
                    <button type="button" class="btn-secondary" onclick="window.close()">Cancel</button>
                </div>
            </form>
        </div>

        <!-- Right Panel - Device & Tracking Info -->
        <div class="medical-panel">
            <div class="panel-header">
                <h2 class="panel-title">Booking Details</h2>
            </div>

            <div class="form-section">
                <h3 class="section-title">Appointment Status</h3>
                <div class="patient-details">
                    <div class="detail-item">
                        <span class="detail-label">Status</span>
                        <span class="detail-value" style="text-transform: capitalize;">{{ booking.status }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Booking ID</span>
                        <span class="detail-value">#{{ booking.id }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Created</span>
                        <span class="detail-value">{{ booking.created_at }}</span>
                    </div>
                </div>
            </div>

            {% if booking.ip_address %}
            <div class="form-section">
                <h3 class="section-title">Device & Location Tracking</h3>
                <div class="patient-details">
                    <div class="detail-item">
                        <span class="detail-label">🌐 IP Address</span>
                        <span class="detail-value">{{ booking.ip_address }}</span>
                    </div>
                    {% if booking.ip_city %}
                    <div class="detail-item">
                        <span class="detail-label">📍 Location</span>
                        <span class="detail-value">{{ booking.ip_city }}, {{ booking.ip_country }}</span>
                    </div>
                    {% endif %}
                    {% if booking.device_type %}
                    <div class="detail-item">
                        <span class="detail-label">📱 Device Type</span>
                        <span class="detail-value">{{ booking.device_type }}</span>
                    </div>
                    {% endif %}
                    {% if booking.device_os %}
                    <div class="detail-item">
                        <span class="detail-label">💻 Operating System</span>
                        <span class="detail-value">{{ booking.device_os }}</span>
                    </div>
                    {% endif %}
                    {% if booking.device_browser %}
                    <div class="detail-item">
                        <span class="detail-label">🌍 Browser</span>
                        <span class="detail-value">{{ booking.device_browser }}</span>
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endif %}

            {% if booking.address %}
            <div class="form-section">
                <h3 class="section-title">Visit Location</h3>
                <div class="patient-details">
                    <div class="detail-item" style="grid-column: 1 / -1;">
                        <span class="detail-label">Address</span>
                        <span class="detail-value">{{ booking.address }}</span>
                    </div>
                    {% if booking.address_city %}
                    <div class="detail-item">
                        <span class="detail-label">City</span>
                        <span class="detail-value">{{ booking.address_city }}</span>
                    </div>
                    {% endif %}
                    {% if booking.address_province %}
                    <div class="detail-item">
                        <span class="detail-label">Province</span>
                        <span class="detail-value">{{ booking.address_province }}</span>
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>

    <script>
        document.getElementById('medical-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            try {
                const response = await fetch('/api/admin/visits', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success || result.ok) {
                    alert('Medical record saved successfully!');
                    window.close();
                } else {
                    alert('Error saving medical record: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                alert('Error saving medical record: ' + error.message);
            }
        });
    </script>
</body>
</html>
'''

def add_medical_records_route(content):
    """Add the medical records route and template to app.py"""
    
    # First, add the template variable after ADMIN_VIEW_HTML
    admin_view_end = 'load();'
    
    # Find where to insert (after the ADMIN_VIEW_HTML closing)
    if 'ADMIN_VIEW_HTML = """' in content and admin_view_end in content:
        # Find the end of ADMIN_VIEW_HTML
        parts = content.split('</script></body></html>"""')
        
        if len(parts) >= 2:
            # Add the new template
            medical_records_template = '\n\n# ── Medical Records HTML Template ──\nMEDICAL_RECORDS_HTML = """' + MEDICAL_RECORDS_HTML + '"""'
            
            # Reconstruct
            content = parts[0] + '</script></body></html>"""' + medical_records_template + parts[1]
    
    # Now add the route before the final if __name__ == '__main__':
    route_code = '''
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
        
        # Fetch booking details
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
            return "Booking not found", 404
        
        booking = dict(zip(cols, row))
        
        # Convert dates to strings
        for key in ['created_at', 'updated_at']:
            if booking.get(key):
                booking[key] = booking[key].strftime('%Y-%m-%d %H:%M')
        for key in ['preferred_date', 'preferred_time']:
            if booking.get(key):
                booking[key] = str(booking[key])
        
        cur.close()
        conn.close()
        
        # Render template with booking data
        from jinja2 import Template
        template = Template(MEDICAL_RECORDS_HTML)
        return template.render(booking=booking)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

'''
    
    # Insert before if __name__
    if_main_marker = 'if __name__ == \'__main__\':'
    if if_main_marker in content:
        content = content.replace(if_main_marker, route_code + if_main_marker)
    
    return content

if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'app.py'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    updated_content = add_medical_records_route(content)
    
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"✓ Added /admin/medical-records route to {input_file}")
    print("✓ Added MEDICAL_RECORDS_HTML template")
    print("✓ Route will fetch booking data from database and render dynamically")
