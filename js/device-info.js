/* ══════════════════════════════════════════════
   DEVICE INFORMATION & IP TRACKING UTILITY
   Captures client device info and IP address
   ══════════════════════════════════════════════ */

(function () {
  'use strict';

  /**
   * DeviceInfo - Utility class for capturing device and network information
   */
  window.DeviceInfo = {

    /**
     * Get client IP address using multiple fallback services
     * @returns {Promise<Object>} IP information with address, country, city, etc.
     */
    async getIPInfo() {
      const services = [
        // Primary service - ipapi.co (free, no key required, detailed info)
        {
          url: 'https://ipapi.co/json/',
          parser: (data) => ({
            ip: data.ip,
            country: data.country_name,
            countryCode: data.country_code,
            region: data.region,
            city: data.city,
            postal: data.postal,
            latitude: data.latitude,
            longitude: data.longitude,
            timezone: data.timezone,
            isp: data.org,
            asn: data.asn,
          })
        },
        // Fallback 1 - ipify (simple, reliable)
        {
          url: 'https://api.ipify.org?format=json',
          parser: (data) => ({
            ip: data.ip,
            country: null,
            city: null,
          })
        },
        // Fallback 2 - ipapi.com (free tier, detailed)
        {
          url: 'https://ipapi.com/ip_api.php?ip=',
          parser: (data) => ({
            ip: data.query || data.ip,
            country: data.country,
            countryCode: data.countryCode,
            region: data.regionName,
            city: data.city,
            postal: data.zip,
            latitude: data.lat,
            longitude: data.lon,
            timezone: data.timezone,
            isp: data.isp,
          })
        }
      ];

      for (const service of services) {
        try {
          const response = await fetch(service.url, {
            method: 'GET',
            cache: 'no-cache',
            headers: {
              'Accept': 'application/json',
            },
          });

          if (!response.ok) continue;

          const data = await response.json();
          const parsed = service.parser(data);

          if (parsed.ip) {
            return {
              success: true,
              timestamp: new Date().toISOString(),
              ...parsed,
            };
          }
        } catch (error) {
          console.warn(`IP service failed: ${service.url}`, error);
          continue;
        }
      }

      // If all services fail, return minimal info
      return {
        success: false,
        ip: null,
        error: 'Unable to retrieve IP address',
        timestamp: new Date().toISOString(),
      };
    },

    /**
     * Get comprehensive device information
     * @returns {Object} Device details including browser, OS, screen, etc.
     */
    getDeviceInfo() {
      const ua = navigator.userAgent;
      const info = {
        // Basic browser info
        userAgent: ua,
        language: navigator.language || navigator.userLanguage,
        languages: navigator.languages || [navigator.language],
        
        // Platform detection
        platform: navigator.platform,
        vendor: navigator.vendor,
        
        // Screen information
        screen: {
          width: window.screen.width,
          height: window.screen.height,
          availWidth: window.screen.availWidth,
          availHeight: window.screen.availHeight,
          colorDepth: window.screen.colorDepth,
          pixelDepth: window.screen.pixelDepth,
          orientation: window.screen.orientation?.type || 'unknown',
        },
        
        // Viewport information
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight,
        },
        
        // Device capabilities
        capabilities: {
          cookieEnabled: navigator.cookieEnabled,
          doNotTrack: navigator.doNotTrack,
          onLine: navigator.onLine,
          touchPoints: navigator.maxTouchPoints || 0,
          hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
          deviceMemory: navigator.deviceMemory || 'unknown',
        },
        
        // Timezone
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        timezoneOffset: new Date().getTimezoneOffset(),
        
        // Connection info (if available)
        connection: this._getConnectionInfo(),
        
        // Parsed device details
        device: this._parseDevice(ua),
        browser: this._parseBrowser(ua),
        os: this._parseOS(ua),
        
        // Additional metadata
        timestamp: new Date().toISOString(),
        referrer: document.referrer || 'direct',
      };

      return info;
    },

    /**
     * Get network connection information
     * @private
     */
    _getConnectionInfo() {
      if (!navigator.connection && !navigator.mozConnection && !navigator.webkitConnection) {
        return null;
      }

      const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
      
      return {
        effectiveType: conn.effectiveType || 'unknown', // 4g, 3g, 2g, slow-2g
        downlink: conn.downlink || null, // Mbps
        rtt: conn.rtt || null, // ms
        saveData: conn.saveData || false,
        type: conn.type || 'unknown', // wifi, cellular, etc.
      };
    },

    /**
     * Parse device type from user agent
     * @private
     */
    _parseDevice(ua) {
      const mobile = /Mobile|Android|iP(hone|od|ad)|IEMobile|BlackBerry|Kindle|Silk-Accelerated|(hpw|web)OS|Opera M(obi|ini)/.test(ua);
      const tablet = /Tablet|iPad/.test(ua) || (mobile && !/Mobile/.test(ua));
      
      let type = 'desktop';
      let brand = 'Unknown';
      
      if (tablet) {
        type = 'tablet';
      } else if (mobile) {
        type = 'mobile';
      }
      
      // Detect brand
      if (/iPhone|iPad|iPod/.test(ua)) {
        brand = 'Apple';
      } else if (/Android/.test(ua)) {
        brand = 'Android';
        // Try to get manufacturer
        const brandMatch = ua.match(/Android.*?;\s*([^;)]+)/);
        if (brandMatch) {
          brand = brandMatch[1].trim();
        }
      } else if (/Windows Phone/.test(ua)) {
        brand = 'Windows Phone';
      } else if (/BlackBerry/.test(ua)) {
        brand = 'BlackBerry';
      }
      
      return {
        type,
        brand,
        model: this._extractModel(ua),
      };
    },

    /**
     * Extract device model from user agent
     * @private
     */
    _extractModel(ua) {
      // iPhone models
      if (/iPhone/.test(ua)) {
        const match = ua.match(/iPhone\s*OS\s*([\d_]+)/);
        return match ? `iPhone (iOS ${match[1].replace(/_/g, '.')})` : 'iPhone';
      }
      
      // iPad models
      if (/iPad/.test(ua)) {
        const match = ua.match(/CPU\s+OS\s+([\d_]+)/);
        return match ? `iPad (iOS ${match[1].replace(/_/g, '.')})` : 'iPad';
      }
      
      // Android models
      if (/Android/.test(ua)) {
        const match = ua.match(/Android\s+([\d.]+);\s*([^)]+)\)/);
        return match ? match[2].trim() : 'Android Device';
      }
      
      return 'Unknown';
    },

    /**
     * Parse browser from user agent
     * @private
     */
    _parseBrowser(ua) {
      let name = 'Unknown';
      let version = 'Unknown';
      
      if (/Edg\//.test(ua)) {
        name = 'Microsoft Edge';
        version = ua.match(/Edg\/([\d.]+)/)?.[1] || version;
      } else if (/Chrome/.test(ua) && !/Edg/.test(ua)) {
        name = 'Chrome';
        version = ua.match(/Chrome\/([\d.]+)/)?.[1] || version;
      } else if (/Safari/.test(ua) && !/Chrome/.test(ua)) {
        name = 'Safari';
        version = ua.match(/Version\/([\d.]+)/)?.[1] || version;
      } else if (/Firefox/.test(ua)) {
        name = 'Firefox';
        version = ua.match(/Firefox\/([\d.]+)/)?.[1] || version;
      } else if (/MSIE|Trident/.test(ua)) {
        name = 'Internet Explorer';
        version = ua.match(/(MSIE |rv:)([\d.]+)/)?.[2] || version;
      } else if (/Opera|OPR/.test(ua)) {
        name = 'Opera';
        version = ua.match(/(Opera|OPR)\/([\d.]+)/)?.[2] || version;
      }
      
      return { name, version };
    },

    /**
     * Parse operating system from user agent
     * @private
     */
    _parseOS(ua) {
      let name = 'Unknown';
      let version = 'Unknown';
      
      if (/Windows NT/.test(ua)) {
        name = 'Windows';
        const versionMap = {
          '10.0': '10/11',
          '6.3': '8.1',
          '6.2': '8',
          '6.1': '7',
          '6.0': 'Vista',
          '5.1': 'XP',
        };
        const ntVersion = ua.match(/Windows NT ([\d.]+)/)?.[1];
        version = versionMap[ntVersion] || ntVersion || version;
      } else if (/Mac OS X/.test(ua)) {
        name = 'macOS';
        version = ua.match(/Mac OS X ([\d_]+)/)?.[1]?.replace(/_/g, '.') || version;
      } else if (/Android/.test(ua)) {
        name = 'Android';
        version = ua.match(/Android ([\d.]+)/)?.[1] || version;
      } else if (/iPhone|iPad|iPod/.test(ua)) {
        name = 'iOS';
        version = ua.match(/OS ([\d_]+)/)?.[1]?.replace(/_/g, '.') || version;
      } else if (/Linux/.test(ua)) {
        name = 'Linux';
      } else if (/CrOS/.test(ua)) {
        name = 'Chrome OS';
      }
      
      return { name, version };
    },

    /**
     * Get complete tracking info (IP + Device)
     * @returns {Promise<Object>} Complete information bundle
     */
    async getCompleteInfo() {
      const [ipInfo, deviceInfo] = await Promise.all([
        this.getIPInfo(),
        Promise.resolve(this.getDeviceInfo()),
      ]);

      return {
        ip: ipInfo,
        device: deviceInfo,
        capturedAt: new Date().toISOString(),
      };
    },

    /**
     * Format device info for display (admin panel)
     * @param {Object} info - Device info object
     * @returns {string} Formatted string
     */
    formatForDisplay(info) {
      if (!info || !info.device) return 'No device info';
      
      const d = info.device;
      const parts = [];
      
      if (d.os?.name) {
        parts.push(`${d.os.name} ${d.os.version || ''}`);
      }
      
      if (d.browser?.name) {
        parts.push(`${d.browser.name} ${d.browser.version || ''}`);
      }
      
      if (d.device?.type) {
        parts.push(`(${d.device.type})`);
      }
      
      return parts.join(' · ');
    },

    /**
     * Format IP info for display
     * @param {Object} info - IP info object
     * @returns {string} Formatted string
     */
    formatIPForDisplay(info) {
      if (!info || !info.ip) return 'Unknown IP';
      
      const parts = [info.ip.ip || 'Unknown'];
      
      if (info.ip.city && info.ip.country) {
        parts.push(`${info.ip.city}, ${info.ip.country}`);
      } else if (info.ip.country) {
        parts.push(info.ip.country);
      }
      
      if (info.ip.isp) {
        parts.push(`(${info.ip.isp})`);
      }
      
      return parts.join(' · ');
    },

    /**
     * Create hidden form fields for device info
     * @param {HTMLFormElement} form - Form element
     * @param {Object} info - Complete device info
     */
    injectIntoForm(form, info) {
      // Create or update hidden input for device info JSON
      let input = form.querySelector('input[name="_device_info"]');
      if (!input) {
        input = document.createElement('input');
        input.type = 'hidden';
        input.name = '_device_info';
        form.appendChild(input);
      }
      input.value = JSON.stringify(info);

      // Also create individual fields for easy backend access
      const fields = {
        '_ip_address': info.ip?.ip || 'unknown',
        '_ip_country': info.ip?.country || 'unknown',
        '_ip_city': info.ip?.city || 'unknown',
        '_device_type': info.device?.device?.type || 'unknown',
        '_device_brand': info.device?.device?.brand || 'unknown',
        '_os': `${info.device?.os?.name || 'unknown'} ${info.device?.os?.version || ''}`.trim(),
        '_browser': `${info.device?.browser?.name || 'unknown'} ${info.device?.browser?.version || ''}`.trim(),
        '_screen_size': `${info.device?.screen?.width}x${info.device?.screen?.height}`,
        '_language': info.device?.language || 'unknown',
        '_timezone': info.device?.timezone || 'unknown',
      };

      Object.entries(fields).forEach(([name, value]) => {
        let field = form.querySelector(`input[name="${name}"]`);
        if (!field) {
          field = document.createElement('input');
          field.type = 'hidden';
          field.name = name;
          form.appendChild(field);
        }
        field.value = value;
      });
    },

  };

  // Auto-export to window
  if (typeof window !== 'undefined') {
    window.DeviceInfo = DeviceInfo;
  }

})();
