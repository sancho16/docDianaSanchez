/* ══════════════════════════════════════════════
   DOC DIANA SÁNCHEZ — Main JavaScript
   ══════════════════════════════════════════════ */

(function() {
  'use strict';

  // ── LANGUAGE TOGGLE ──
  const langToggle = document.getElementById('lang-toggle');
  if (langToggle) {
    langToggle.addEventListener('click', function () {
      I18N.toggle();
    });
  }
  // Apply saved/default language on load
  I18N.applyLanguage();

  // ── NAVBAR SCROLL EFFECT ──
  const navbar = document.getElementById('navbar');
  
  function handleNavbarScroll() {
    if (window.scrollY > 60) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  }
  
  window.addEventListener('scroll', handleNavbarScroll);
  handleNavbarScroll(); // Initial check

  // ── MOBILE MENU TOGGLE ──
  const hamburger = document.getElementById('hamburger');
  const mainNav = document.getElementById('main-nav');

  hamburger.addEventListener('click', function() {
    const isOpen = hamburger.classList.toggle('open');
    mainNav.classList.toggle('open');
    hamburger.setAttribute('aria-expanded', isOpen);
    document.body.style.overflow = isOpen ? 'hidden' : '';
  });

  // Close mobile menu when clicking a link
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', function() {
      hamburger.classList.remove('open');
      mainNav.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    });
  });

  // ── SMOOTH SCROLL FOR ANCHOR LINKS ──
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        e.preventDefault();
        const navbarHeight = navbar.offsetHeight;
        const targetPosition = targetElement.offsetTop - navbarHeight;
        
        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });
      }
    });
  });

  // ── BACK TO TOP BUTTON ──
  const backTopBtn = document.getElementById('back-top');
  
  function handleBackTopVisibility() {
    if (window.scrollY > 400) {
      backTopBtn.hidden = false;
      backTopBtn.classList.add('visible');
    } else {
      backTopBtn.classList.remove('visible');
      setTimeout(() => {
        if (!backTopBtn.classList.contains('visible')) {
          backTopBtn.hidden = true;
        }
      }, 300);
    }
  }
  
  window.addEventListener('scroll', handleBackTopVisibility);
  handleBackTopVisibility();
  
  backTopBtn.addEventListener('click', function() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // ── SCROLL REVEAL ANIMATION ──
  const revealElements = document.querySelectorAll(
    '.testimonial-card, .about__visual, .about__text, ' +
    '.schedule__text, .schedule__table-wrap, .contact__info, .contact__form, ' +
    '.section__header, .stat'
  );

  // Add reveal class to elements
  revealElements.forEach(el => el.classList.add('reveal'));

  const revealObserver = new IntersectionObserver(
    function(entries) {
      entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
          // Stagger children inside grids
          const delay = entry.target.closest('.services__grid, .testimonials__grid')
            ? Array.from(entry.target.parentElement.children).indexOf(entry.target) * 80
            : 0;
          
          setTimeout(() => {
            entry.target.classList.add('visible');
          }, delay);
          
          revealObserver.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.12,
      rootMargin: '0px 0px -40px 0px'
    }
  );

  revealElements.forEach(el => revealObserver.observe(el));

  // ── ACTIVE NAV LINK HIGHLIGHTING ──
  const sections = document.querySelectorAll('section[id]');
  
  const navObserver = new IntersectionObserver(
    function(entries) {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute('id');
          
          document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            link.removeAttribute('aria-current');
          });
          
          const activeLink = document.querySelector(`.nav-link[href="#${id}"]`);
          if (activeLink) {
            activeLink.classList.add('active');
            activeLink.setAttribute('aria-current', 'page');
          }
        }
      });
    },
    {
      threshold: 0.3,
      rootMargin: '-80px 0px -60% 0px'
    }
  );

  sections.forEach(section => navObserver.observe(section));

  // ── SERVICE CARD FLIP ──
  document.querySelectorAll('.service-card').forEach(card => {
    function toggleFlip(e) {
      // Don't flip if clicking the "Book now" link on the back
      if (e.target.closest('.service-card__cta')) return;
      const isFlipped = card.classList.toggle('is-flipped');
      card.setAttribute('aria-expanded', isFlipped);
    }
    card.addEventListener('click', toggleFlip);
    card.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleFlip(e); }
    });
  });

  // ── BOOKING FORM — Channel, Platform Cards, GPS ──
  (function initBookingForm() {
    const channelVirtual  = document.getElementById('channel-virtual');
    const channelExpress  = document.getElementById('channel-express');
    const sectionPlatform = document.getElementById('field-virtual-platform');
    const sectionAddress  = document.getElementById('field-express-address');
    const platformInput   = document.getElementById('virtual-platform');
    const platformCards   = document.querySelectorAll('.form-platform-card');
    const addressInput    = document.getElementById('address');
    const emailInput      = document.getElementById('email');
    const emailBadge      = document.getElementById('email-required-badge');
    const channelError    = document.getElementById('channel-error');
    const platformError   = document.getElementById('platform-error');
    const addressError    = document.getElementById('address-error');

    if (!channelVirtual) return; // not on booking page

    function showSection(el) {
      if (!el) return;
      el.hidden = false;
      el.classList.remove('active');
      void el.offsetWidth;
      el.classList.add('active');
    }
    function hideSection(el) {
      if (!el) return;
      el.hidden = true;
      el.classList.remove('active');
    }

    function onChannelChange() {
      const val = document.querySelector('input[name="channel"]:checked')?.value;
      if (channelError) channelError.textContent = '';

      if (val === 'virtual') {
        showSection(sectionPlatform);
        hideSection(sectionAddress);
        // Email becomes required for virtual
        if (emailInput) { emailInput.required = true; }
        if (emailBadge) { emailBadge.hidden = false; }
        if (addressInput) { addressInput.required = false; }
      } else if (val === 'express') {
        hideSection(sectionPlatform);
        showSection(sectionAddress);
        // Email optional, address required
        if (emailInput) { emailInput.required = false; }
        if (emailBadge) { emailBadge.hidden = true; }
        if (addressInput) { addressInput.required = true; }
        // Clear platform
        platformCards.forEach(c => c.setAttribute('aria-pressed', 'false'));
        if (platformInput) platformInput.value = '';
      } else {
        hideSection(sectionPlatform);
        hideSection(sectionAddress);
        if (emailInput) { emailInput.required = false; }
        if (emailBadge) { emailBadge.hidden = true; }
      }
    }

    channelVirtual.addEventListener('change', onChannelChange);
    channelExpress.addEventListener('change', onChannelChange);

    // Also handle direct label click for iOS (radio change may not fire reliably)
    document.querySelectorAll('.form-channel-card').forEach(label => {
      label.addEventListener('click', function () {
        // Update is-selected class on all channel cards
        document.querySelectorAll('.form-channel-card').forEach(l => l.classList.remove('is-selected'));
        this.classList.add('is-selected');
        // Trigger onChannelChange after a tick so radio.checked is updated
        setTimeout(onChannelChange, 0);
      });
    });

    // Platform card click
    platformCards.forEach(card => {
      card.addEventListener('click', function () {
        platformCards.forEach(c => c.setAttribute('aria-pressed', 'false'));
        this.setAttribute('aria-pressed', 'true');
        if (platformInput) platformInput.value = this.dataset.platform;
        if (platformError) platformError.textContent = '';
      });
      card.addEventListener('keydown', e => {
        if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); card.click(); }
      });
    });

    // GPS
    const gpsBtn        = document.getElementById('gps-btn');
    const gpsBtnText    = document.getElementById('gps-btn-text');
    const gpsResult     = document.getElementById('gps-result');
    const gpsResultText = document.getElementById('gps-result-text');
    const gpsMapLink    = document.getElementById('gps-map-link');
    const gpsCoordsInput = document.getElementById('gps-coords');
    const gpsSubText    = document.getElementById('gps-sub-text');

    if (gpsBtn) {
      gpsBtn.addEventListener('click', function () {
        if (!navigator.geolocation) {
          if (gpsSubText) gpsSubText.textContent = 'GPS not available on this device.';
          return;
        }

        gpsBtn.disabled = true;
        gpsBtn.classList.add('detecting');
        if (gpsBtnText) gpsBtnText.textContent = 'Detecting…';

        navigator.geolocation.getCurrentPosition(
          function (pos) {
            const lat = pos.coords.latitude.toFixed(6);
            const lng = pos.coords.longitude.toFixed(6);
            const acc = Math.round(pos.coords.accuracy);
            const coords = `${lat}, ${lng}`;

            if (gpsCoordsInput) gpsCoordsInput.value = coords;
            if (gpsResultText) gpsResultText.textContent = `${coords}  ±${acc}m`;
            if (gpsMapLink) {
              gpsMapLink.href = `https://maps.google.com/?q=${lat},${lng}`;
            }
            if (gpsResult) { gpsResult.hidden = false; }
            if (gpsSubText) gpsSubText.textContent = `Location captured · ±${acc}m accuracy`;

            gpsBtn.disabled = false;
            gpsBtn.classList.remove('detecting');
            if (gpsBtnText) gpsBtnText.textContent = '✔ Done';
          },
          function (err) {
            gpsBtn.disabled = false;
            gpsBtn.classList.remove('detecting');
            if (gpsBtnText) gpsBtnText.textContent = 'Retry';
            const msgs = { 1: 'Permission denied.', 2: 'Position unavailable.', 3: 'Timed out.' };
            if (gpsSubText) gpsSubText.textContent = msgs[err.code] || 'Location error.';
          },
          { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
        );
      });
    }
  })();

  // ── CONTACT FORM — Formspree AJAX + localStorage backup ──
  const form        = document.getElementById('contact-form');
  const formSuccess = document.getElementById('form-success');
  const submitBtn   = document.getElementById('form-submit-btn');

  // Set min date on date picker to today
  const dateInput = document.getElementById('preferred-date');
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);
  }

  function validateField(field) {
    const group   = field.closest('.form-group');
    const errorEl = group ? group.querySelector('.field-error') : null;
    let errorMsg  = '';

    if (field.required && !field.value.trim()) {
      errorMsg = 'Este campo es obligatorio.';
    } else if (field.type === 'email' && field.value.trim()) {
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(field.value.trim())) {
        errorMsg = 'Ingrese un correo electrónico válido.';
      }
    } else if (field.type === 'tel' && field.value.trim()) {
      if (!/^[\d\s\+\-\(\)]{7,}$/.test(field.value.trim())) {
        errorMsg = 'Ingrese un número de teléfono válido.';
      }
    }

    if (group) group.classList.toggle('has-error', !!errorMsg);
    if (errorEl) errorEl.textContent = errorMsg;
    return !errorMsg;
  }

  form.querySelectorAll('input[required], textarea[required]').forEach(field => {
    field.addEventListener('blur',  () => validateField(field));
    field.addEventListener('input', () => {
      if (field.closest('.form-group').classList.contains('has-error')) validateField(field);
    });
  });

  function saveAppointmentLocally(data) {
    const APPT_KEY = 'dds_appointments';
    let list = [];
    try { list = JSON.parse(localStorage.getItem(APPT_KEY) || '[]'); } catch {}
    list.unshift({
      id:        'a' + Date.now().toString(36),
      name:      data.name,
      patient_id: data.patient_id || '',
      phone:     data.phone,
      email:     data.email     || '',
      channel:   data.channel   || '',
      platform:  data.virtual_platform || '',
      address:   data.address   || '',
      service:   data.service   || '',
      date:      data.preferred_date || '',
      time:      data.preferred_time || '',
      message:   data.message,
      status:    'pending',
      submitted: new Date().toISOString()
    });
    localStorage.setItem(APPT_KEY, JSON.stringify(list));
  }

  form.addEventListener('submit', async function(e) {
    e.preventDefault();

    // Validate required fields (skip hidden _gotcha)
    const fields = form.querySelectorAll('input[required], textarea[required]');
    let allValid = true;
    fields.forEach(f => { if (!validateField(f)) allValid = false; });

    if (!allValid) {
      const firstErr = form.querySelector('.has-error input, .has-error textarea');
      if (firstErr) firstErr.focus();
      return;
    }

    submitBtn.textContent = 'Enviando…';
    submitBtn.disabled = true;

    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    // Always save locally so admin can see it regardless of backend
    saveAppointmentLocally(payload);

    // Post to the booking backend (Cloudflare Tunnel -> Flask)
    const action = form.getAttribute('action') || '';
    const isBackend = action.includes('docdianasanchez.com/api/bookings');

    if (isBackend) {
      try {
        const res = await fetch(action, {
          method: 'POST',
          headers: { 'Accept': 'application/json' },
          body: formData
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.ok === false) {
          throw new Error(data.error || ('Error ' + res.status));
        }
      } catch (err) {
        console.warn('Booking backend submission failed; saved locally only.', err);
      }
    }

    // Redirect to success page
    window.location.href = 'success.html';
  });

  // ── FOOTER YEAR ──
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // ── ACTIVE NAV LINK STYLE ──
  const style = document.createElement('style');
  style.textContent = `
    .nav-link.active {
      color: var(--white) !important;
      background: rgba(255,255,255,0.05);
    }
    .nav-link--cta.active {
      background: var(--red-light) !important;
    }
  `;
  document.head.appendChild(style);

})();

  // ── MODERN DATE/TIME PICKER WITH HAPTIC FEEDBACK ──
  function initModernDateTimePicker() {
    const dateInput = document.getElementById('preferred-date');
    const timeSlots = document.querySelectorAll('.time-slot');
    const hiddenTimeInput = document.getElementById('preferred-time');
    const selectedTimeValue = document.querySelector('.selected-time-value');
    const selectedTimeDisplay = document.querySelector('.selected-time-display');

    // Haptic feedback function
    function triggerHapticFeedback(element, intensity = 'light') {
      // Add haptic animation class
      element.classList.add('haptic-feedback');
      setTimeout(() => {
        element.classList.remove('haptic-feedback');
      }, 200);

      // Try to trigger device haptic feedback
      if ('vibrate' in navigator) {
        const patterns = {
          light: [10],
          medium: [20],
          strong: [30, 10, 30]
        };
        navigator.vibrate(patterns[intensity] || patterns.light);
      }

      // iOS haptic feedback (requires user gesture)
      if (window.DeviceMotionEvent && typeof DeviceMotionEvent.requestPermission === 'function') {
        // This would require permission, keeping as fallback
        console.log('iOS haptic feedback triggered');
      }
    }

    // Set minimum date to today
    if (dateInput) {
      const today = new Date();
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);
      
      const minDate = tomorrow.toISOString().split('T')[0];
      dateInput.setAttribute('min', minDate);

      // Add haptic feedback to date input
      dateInput.addEventListener('change', function() {
        triggerHapticFeedback(this, 'light');
        
        // Add selection animation
        this.style.transform = 'scale(1.02)';
        setTimeout(() => {
          this.style.transform = '';
        }, 150);
      });

      dateInput.addEventListener('focus', function() {
        triggerHapticFeedback(this, 'light');
      });
    }

    // Handle time slot selection
    timeSlots.forEach(slot => {
      slot.addEventListener('click', function() {
        // Remove previous selection
        timeSlots.forEach(s => s.classList.remove('selected'));
        
        // Add selection to clicked slot
        this.classList.add('selected');
        
        // Update hidden input and display
        const timeValue = this.dataset.time;
        const displayValue = this.dataset.display;
        
        if (hiddenTimeInput) hiddenTimeInput.value = timeValue;
        if (selectedTimeValue) selectedTimeValue.textContent = displayValue;
        if (selectedTimeDisplay) selectedTimeDisplay.classList.add('has-selection');

        // Trigger haptic feedback
        triggerHapticFeedback(this, 'medium');
        
        // Add ripple effect
        createRippleEffect(this);
      });

      // Add hover haptic feedback
      slot.addEventListener('mouseenter', function() {
        if (window.matchMedia('(hover: hover)').matches) {
          triggerHapticFeedback(this, 'light');
        }
      });
    });

    // Create ripple effect
    function createRippleEffect(element) {
      const ripple = document.createElement('span');
      ripple.classList.add('ripple');
      
      const rect = element.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = rect.width / 2;
      const y = rect.height / 2;
      
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = (x - size / 2) + 'px';
      ripple.style.top = (y - size / 2) + 'px';
      
      element.appendChild(ripple);
      
      setTimeout(() => {
        if (ripple.parentNode) {
          ripple.parentNode.removeChild(ripple);
        }
      }, 600);
    }

    // Add ripple CSS if not already present
    if (!document.querySelector('style[data-ripple]')) {
      const rippleStyle = document.createElement('style');
      rippleStyle.setAttribute('data-ripple', 'true');
      rippleStyle.textContent = `
        .time-slot {
          position: relative;
          overflow: hidden;
        }
        .ripple {
          position: absolute;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.6);
          transform: scale(0);
          animation: ripple 0.6s linear;
          pointer-events: none;
        }
        @keyframes ripple {
          to {
            transform: scale(4);
            opacity: 0;
          }
        }
      `;
      document.head.appendChild(rippleStyle);
    }

    // Progressive enhancement for touch devices
    if ('ontouchstart' in window) {
      timeSlots.forEach(slot => {
        slot.addEventListener('touchstart', function() {
          triggerHapticFeedback(this, 'light');
        });
      });
    }

    // Keyboard navigation support
    timeSlots.forEach((slot, index) => {
      slot.addEventListener('keydown', function(e) {
        let nextIndex;
        
        switch(e.key) {
          case 'ArrowRight':
          case 'ArrowDown':
            e.preventDefault();
            nextIndex = (index + 1) % timeSlots.length;
            timeSlots[nextIndex].focus();
            triggerHapticFeedback(timeSlots[nextIndex], 'light');
            break;
          case 'ArrowLeft':
          case 'ArrowUp':
            e.preventDefault();
            nextIndex = (index - 1 + timeSlots.length) % timeSlots.length;
            timeSlots[nextIndex].focus();
            triggerHapticFeedback(timeSlots[nextIndex], 'light');
            break;
          case 'Enter':
          case ' ':
            e.preventDefault();
            this.click();
            break;
        }
      });
    });
  }

  // Initialize when DOM is loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initModernDateTimePicker);
  } else {
    initModernDateTimePicker();
  }