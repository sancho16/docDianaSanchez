#!/usr/bin/env python3
"""
Dr. Diana Sánchez - Booking Backend API
Flask API for handling appointment bookings and reviews
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DATABASE_HOST', 'localhost'),
    'user': os.getenv('DATABASE_USER', 'beckham23'),
    'password': os.getenv('DATABASE_PASSWORD', ''),
    'database': os.getenv('DATABASE_NAME', 'diana_bookings'),
    'port': int(os.getenv('DATABASE_PORT', 3306))
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_database():
    """Initialize database tables if they don't exist"""
    connection = get_db_connection()
    if not connection:
        print("Failed to initialize database - no connection")
        return False
    
    try:
        cursor = connection.cursor()
        
        # Create bookings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                patient_id VARCHAR(50),
                phone VARCHAR(50) NOT NULL,
                email VARCHAR(255),
                channel VARCHAR(50),
                virtual_platform VARCHAR(50),
                address TEXT,
                address_city VARCHAR(100),
                address_province VARCHAR(100),
                gps_coordinates VARCHAR(100),
                service VARCHAR(255),
                preferred_date DATE,
                preferred_time TIME,
                message TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                
                -- Device tracking fields
                ip_address VARCHAR(45),
                ip_country VARCHAR(100),
                ip_city VARCHAR(100),
                device_type VARCHAR(50),
                device_brand VARCHAR(100),
                device_model VARCHAR(255),
                device_os VARCHAR(100),
                device_browser VARCHAR(100),
                screen_size VARCHAR(20),
                user_language VARCHAR(10),
                user_timezone VARCHAR(50),
                connection_type VARCHAR(20),
                device_info_json TEXT,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                INDEX idx_status (status),
                INDEX idx_created_at (created_at),
                INDEX idx_date (preferred_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Create reviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                rating INT NOT NULL,
                text TEXT NOT NULL,
                since VARCHAR(100),
                approved BOOLEAN DEFAULT FALSE,
                ip_address VARCHAR(45),
                device_info TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_approved (approved),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        connection.commit()
        print("Database tables initialized successfully")
        return True
        
    except Error as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

# Initialize database on startup
init_database()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    connection = get_db_connection()
    db_status = 'connected' if connection else 'disconnected'
    if connection:
        connection.close()
    
    return jsonify({
        'status': 'ok',
        'service': 'Dr. Diana Sánchez Booking API',
        'database': db_status,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    """Create a new booking appointment"""
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
            'connection_type': data.get('_connection_type', ''),
            'device_info_json': device_info_json
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
                user_language, user_timezone, connection_type, device_info_json
            ) VALUES (
                %(name)s, %(patient_id)s, %(phone)s, %(email)s, %(channel)s, %(virtual_platform)s,
                %(address)s, %(address_city)s, %(address_province)s, %(gps_coordinates)s,
                %(service)s, %(preferred_date)s, %(preferred_time)s, %(message)s, %(status)s,
                %(ip_address)s, %(ip_country)s, %(ip_city)s, %(device_type)s, %(device_brand)s,
                %(device_model)s, %(device_os)s, %(device_browser)s, %(screen_size)s,
                %(user_language)s, %(user_timezone)s, %(connection_type)s, %(device_info_json)s
            )
        """
        
        cursor.execute(query, booking_data)
        connection.commit()
        booking_id = cursor.lastrowid
        
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

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    """Get all bookings"""
    try:
        status_filter = request.args.get('status')
        
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'ok': False,
                'error': 'Database connection failed'
            }), 500
        
        cursor = connection.cursor(dictionary=True)
        
        if status_filter:
            query = "SELECT * FROM bookings WHERE status = %s ORDER BY created_at DESC"
            cursor.execute(query, (status_filter,))
        else:
            query = "SELECT * FROM bookings ORDER BY created_at DESC"
            cursor.execute(query)
        
        bookings = cursor.fetchall()
        
        # Convert datetime objects to strings
        for booking in bookings:
            for key, value in booking.items():
                if isinstance(value, (datetime)):
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

@app.route('/api/bookings/<int:booking_id>', methods=['PATCH'])
def update_booking(booking_id):
    """Update booking status"""
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
        
        query = "UPDATE bookings SET status = %s WHERE id = %s"
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

@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    """Delete a booking"""
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

@app.route('/api/reviews', methods=['POST'])
def create_review():
    """Create a new review"""
    try:
        data = request.get_json()
        
        review_data = {
            'name': data.get('name'),
            'rating': data.get('rating'),
            'text': data.get('text'),
            'since': data.get('since', ''),
            'approved': False,
            'ip_address': request.headers.get('X-Real-IP', request.remote_addr),
            'device_info': json.dumps(data.get('device_info', {}))
        }
        
        # Validate
        if not all([review_data['name'], review_data['rating'], review_data['text']]):
            return jsonify({
                'ok': False,
                'error': 'Name, rating, and text are required'
            }), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'ok': False,
                'error': 'Database connection failed'
            }), 500
        
        cursor = connection.cursor()
        
        query = """
            INSERT INTO reviews (name, rating, text, since, approved, ip_address, device_info)
            VALUES (%(name)s, %(rating)s, %(text)s, %(since)s, %(approved)s, %(ip_address)s, %(device_info)s)
        """
        
        cursor.execute(query, review_data)
        connection.commit()
        review_id = cursor.lastrowid
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'ok': True,
            'message': 'Review submitted for approval',
            'review_id': review_id
        }), 201
        
    except Exception as e:
        print(f"Error creating review: {e}")
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    """Get reviews (approved only by default)"""
    try:
        approved_only = request.args.get('approved', 'true').lower() == 'true'
        
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'ok': False,
                'error': 'Database connection failed'
            }), 500
        
        cursor = connection.cursor(dictionary=True)
        
        if approved_only:
            query = "SELECT * FROM reviews WHERE approved = TRUE ORDER BY created_at DESC"
        else:
            query = "SELECT * FROM reviews ORDER BY created_at DESC"
        
        cursor.execute(query)
        reviews = cursor.fetchall()
        
        # Convert datetime to string
        for review in reviews:
            if review.get('created_at'):
                review['created_at'] = review['created_at'].isoformat()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'ok': True,
            'reviews': reviews,
            'count': len(reviews)
        })
        
    except Exception as e:
        print(f"Error fetching reviews: {e}")
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500

@app.route('/api/reviews/<int:review_id>/approve', methods=['PATCH'])
def approve_review(review_id):
    """Approve a review"""
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'ok': False,
                'error': 'Database connection failed'
            }), 500
        
        cursor = connection.cursor()
        
        query = "UPDATE reviews SET approved = TRUE WHERE id = %s"
        cursor.execute(query, (review_id,))
        connection.commit()
        
        if cursor.rowcount == 0:
            cursor.close()
            connection.close()
            return jsonify({
                'ok': False,
                'error': 'Review not found'
            }), 404
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'ok': True,
            'message': 'Review approved successfully'
        })
        
    except Exception as e:
        print(f"Error approving review: {e}")
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500

@app.route('/api/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    """Delete a review"""
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'ok': False,
                'error': 'Database connection failed'
            }), 500
        
        cursor = connection.cursor()
        
        query = "DELETE FROM reviews WHERE id = %s"
        cursor.execute(query, (review_id,))
        connection.commit()
        
        if cursor.rowcount == 0:
            cursor.close()
            connection.close()
            return jsonify({
                'ok': False,
                'error': 'Review not found'
            }), 404
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'ok': True,
            'message': 'Review deleted successfully'
        })
        
    except Exception as e:
        print(f"Error deleting review: {e}")
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('ENVIRONMENT', 'production') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
