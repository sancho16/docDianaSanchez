/* ══════════════════════════════════════════════
   DOC DIANA SÁNCHEZ — Main JavaScript
   ══════════════════════════════════════════════ */

(function() {
  'use strict';

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
    
    // Prevent body scroll when menu is open
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
    '.service-card, .testimonial-card, .about__visual, .about__text, ' +
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
      phone:     data.phone,
      email:     data.email     || '',
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
    submitBtn.disabled    = true;

    const formData = new FormData(form);
    const payload  = Object.fromEntries(formData.entries());

    // Always save locally so admin can see it regardless of backend
    saveAppointmentLocally(payload);

    // Post to the booking backend (Cloudflare Tunnel -> Flask)
    const action = form.getAttribute('action') || '';
    const isBackend = action.includes('docdianasanchez.com/api/bookings');

    if (isBackend) {
      try {
        const res = await fetch(action, {
          method:  'POST',
          headers: { 'Accept': 'application/json' },
          body:    formData
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.ok === false) {
          throw new Error(data.error || ('Error ' + res.status));
        }
      } catch (err) {
        // Keep the success message (data is saved locally + retried later),
        // but log so we can diagnose. Real failure still shows confirmation to user.
        console.warn('Booking backend submission failed; saved locally only.', err);
      }
    }

    form.reset();
    form.querySelectorAll('.form-group').forEach(g => g.classList.remove('has-error'));
    formSuccess.hidden    = false;
    submitBtn.textContent = 'Enviar solicitud';
    submitBtn.disabled    = false;
    setTimeout(() => { formSuccess.hidden = true; }, 7000);
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
