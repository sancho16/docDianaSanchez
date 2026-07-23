#!/usr/bin/env python3
"""
Dr. Diana Sánchez - Booking Backend API (PostgreSQL Version)
Flask API for handling appointment bookings with PostgreSQL
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import json
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure CORS
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'https://docdianasanchez.com').split(',')
CORS(app, origins=allowed_origins)

# Parse DATABASE_URL
database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise ValueError("DATABASE_URL environment variable is required")

url = urlparse(database_url)

DB_CONFIG = {
    'dbname': url.path[1:],
    'user': url.username,
    'password': url.password,
    'host': url.hostname,
    'port': url.port or 5432
}

def get_db_connection():
    """Create and return a PostgreSQL database connection"""
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    connection = get_db_connection()
    db_status = 'up' if connection else 'down'
    if connection:
        connection.close()
    
    return jsonify({
        'status': 'ok',
        'db': db_status
    })

@app.route('/api/bookings', methods=['GET', 'POST'])
def handle_bookings():
    """Get all bookings or create a new booking"""
    
    if request.method == 'GET':
        try:
            status_filter = request.args.get('status')
            
            connection = get_db_connection()
            if not connection:
                return jsonify({
                    'ok': False,
                    'error': 'Database connection failed'
                }), 500
            
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            if status_filter:
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
                    WHERE status = %s 
                    ORDER BY created_at DESC
                """
                cursor.execute(query, (status_filter,))
            else:
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
                    ORDER BY created_at DESC
                """
                cursor.execute(query)
            
            bookings = cursor.fetchall()
            
            # Convert datetime and date objects to strings
            for booking in bookings:
                for key, value in booking.items():
                    if isinstance(value, (datetime)):
                        booking[key] = value.isoformat()
                    elif hasattr(value, 'isoformat'):  # date objects
                        booking[key] = value.isoformat()
                    elif value is None:
                        booking[key] = ''
            
            cursor.close()
            connection.close()
            
            return jsonify({
                'ok': True,
                'bookings': bookings,
                'count': len(bookings)
            })
            
        except Exception as e:
            print(f"Error fetching bookings: {e}")
            return jsonify({
                'ok': False,
                'error': str(e)
            }), 500
    
    # POST - Create new booking
    elif request.method == 'POST':
        try:
            # Get form data
            data = request.form.to_dict()
            
            # Extract device tracking info
            device_info_json = data.get('_device_info', '{}')
            
            # Prepare insert data
            booking_data = {
                'name': data.get('name'),
                'patient_id': data.get('patient_id', ''),
                'phone': data.get('phone'),
                'email': data.get('email', ''),
                'channel': data.get('channel', ''),
                'virtual_platform': data.get('virtual_platform', ''),
                'address': data.get('address', ''),
                'address_city': data.get('address_city', ''),
                'address_province': data.get('address_province', ''),
                'gps_coordinates': data.get('gps_coordinates', ''),
                'service': data.get('service', ''),
                'preferred_date': data.get('preferred_date') or None,
                'preferred_time': data.get('preferred_time') or None,
                'message': data.get('message', ''),
                'status': 'pending',
                
                # Device tracking
                'ip_address': data.get('_ip_address', ''),
                'ip_country': data.get('_ip_country', ''),
                'ip_city': data.get('_ip_city', ''),
                'device_type': data.get('_device_type', ''),
                'device_brand': data.get('_device_brand', ''),
                'device_model': data.get('_device_type', ''),
                'device_os': data.get('_os', ''),
                'device_browser': data.get('_browser', ''),
                'screen_size': data.get('_screen_size', ''),
                'user_language': data.get('_language', ''),
                'user_timezone': data.get('_timezone', ''),
                'connection_type': data.get('_connection_type', '')
            }
            
            # Validate required fields
            if not booking_data['name'] or not booking_data['phone']:
                return jsonify({
                    'ok': False,
                    'error': 'Name and phone are required'
                }), 400
            
            # Insert into database
            connection = get_db_connection()
            if not connection:
                return jsonify({
                    'ok': False,
                    'error': 'Database connection failed'
                }), 500
            
            cursor = connection.cursor()
            
            query = """
                INSERT INTO bookings (
                    name, patient_id, phone, email, channel, virtual_platform,
                    address, address_city, address_province, gps_coordinates,
                    service, preferred_date, preferred_time, message, status,
                    ip_address, ip_country, ip_city, device_type, device_brand,
                    device_model, device_os, device_browser, screen_size,
                    user_language, user_timezone, connection_type
                ) VALUES (
                    %(name)s, %(patient_id)s, %(phone)s, %(email)s, %(channel)s, %(virtual_platform)s,
                    %(address)s, %(address_city)s, %(address_province)s, %(gps_coordinates)s,
                    %(service)s, %(preferred_date)s, %(preferred_time)s, %(message)s, %(status)s,
                    %(ip_address)s, %(ip_country)s, %(ip_city)s, %(device_type)s, %(device_brand)s,
                    %(device_model)s, %(device_os)s, %(device_browser)s, %(screen_size)s,
                    %(user_language)s, %(user_timezone)s, %(connection_type)s
                )
                RETURNING id
            """
            
            cursor.execute(query, booking_data)
            booking_id = cursor.fetchone()[0]
            connection.commit()
            
            cursor.close()
            connection.close()
            
            return jsonify({
                'ok': True,
                'message': 'Booking created successfully',
                'booking_id': booking_id
            }), 201
            
        except Exception as e:
            print(f"Error creating booking: {e}")
            return jsonify({
                'ok': False,
                'error': str(e)
            }), 500

@app.route('/api/bookings/<int:booking_id>', methods=['GET', 'PATCH', 'DELETE'])
def handle_booking(booking_id):
    """Get, update, or delete a specific booking"""
    
    if request.method == 'GET':
        try:
            connection = get_db_connection()
            if not connection:
                return jsonify({
                    'ok': False,
                    'error': 'Database connection failed'
                }), 500
            
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
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
            cursor.execute(query, (booking_id,))
            booking = cursor.fetchone()
            
            if not booking:
                cursor.close()
                connection.close()
                return jsonify({
                    'ok': False,
                    'error': 'Booking not found'
                }), 404
            
            # Convert datetime to string
            for key, value in booking.items():
                if isinstance(value, (datetime)):
                    booking[key] = value.isoformat()
                elif hasattr(value, 'isoformat'):
                    booking[key] = value.isoformat()
            
            cursor.close()
            connection.close()
            
            return jsonify({
                'ok': True,
                'booking': booking
            })
            
        except Exception as e:
            print(f"Error fetching booking: {e}")
            return jsonify({
                'ok': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'PATCH':
        try:
            data = request.get_json()
            status = data.get('status')
            
            if not status:
                return jsonify({
                    'ok': False,
                    'error': 'Status is required'
                }), 400
            
            if status not in ['pending', 'confirmed', 'cancelled', 'completed']:
                return jsonify({
                    'ok': False,
                    'error': 'Invalid status'
                }), 400
            
            connection = get_db_connection()
            if not connection:
                return jsonify({
                    'ok': False,
                    'error': 'Database connection failed'
                }), 500
            
            cursor = connection.cursor()
            
            query = "UPDATE bookings SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
            cursor.execute(query, (status, booking_id))
            connection.commit()
            
            if cursor.rowcount == 0:
                cursor.close()
                connection.close()
                return jsonify({
                    'ok': False,
                    'error': 'Booking not found'
                }), 404
            
            cursor.close()
            connection.close()
            
            return jsonify({
                'ok': True,
                'message': 'Booking updated successfully'
            })
            
        except Exception as e:
            print(f"Error updating booking: {e}")
            return jsonify({
                'ok': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'DELETE':
        try:
            connection = get_db_connection()
            if not connection:
                return jsonify({
                    'ok': False,
                    'error': 'Database connection failed'
                }), 500
            
            cursor = connection.cursor()
            
            query = "DELETE FROM bookings WHERE id = %s"
            cursor.execute(query, (booking_id,))
            connection.commit()
            
            if cursor.rowcount == 0:
                cursor.close()
                connection.close()
                return jsonify({
                    'ok': False,
                    'error': 'Booking not found'
                }), 404
            
            cursor.close()
            connection.close()
            
            return jsonify({
                'ok': True,
                'message': 'Booking deleted successfully'
            })
            
        except Exception as e:
            print(f"Error deleting booking: {e}")
            return jsonify({
                'ok': False,
                'error': str(e)
            }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('ENVIRONMENT', 'production') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
