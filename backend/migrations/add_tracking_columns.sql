-- Migration: Add IP/Device Tracking Columns to Bookings Table
-- Date: 2026-07-24
-- Description: Adds columns to track IP address, geolocation, device type, OS, and browser for bookings

-- Add IP address and geolocation columns
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS ip_city VARCHAR(100);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS ip_country VARCHAR(100);

-- Add device information columns
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS device_type VARCHAR(50);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS device_os VARCHAR(100);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS device_browser VARCHAR(100);

-- Create index on IP address for faster lookups
CREATE INDEX IF NOT EXISTS idx_bookings_ip_address ON bookings(ip_address);

-- Create index on status for faster filtering
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);

-- Add comment to document the tracking columns
COMMENT ON COLUMN bookings.ip_address IS 'IP address of the user who created the booking (supports IPv4 and IPv6)';
COMMENT ON COLUMN bookings.ip_city IS 'City derived from IP geolocation';
COMMENT ON COLUMN bookings.ip_country IS 'Country derived from IP geolocation';
COMMENT ON COLUMN bookings.device_type IS 'Type of device used (mobile, tablet, desktop)';
COMMENT ON COLUMN bookings.device_os IS 'Operating system of the device';
COMMENT ON COLUMN bookings.device_browser IS 'Web browser used to create the booking';
