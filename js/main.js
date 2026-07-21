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

  // ── CONTACT FORM VALIDATION & SUBMIT ──
  const form = document.getElementById('contact-form');
  const formSuccess = document.getElementById('form-success');

  function validateField(field) {
    const group = field.closest('.form-group');
    const errorEl = group.querySelector('.field-error');
    let errorMsg = '';

    if (field.required && !field.value.trim()) {
      errorMsg = 'Este campo es obligatorio.';
    } else if (field.type === 'email' && field.value.trim()) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(field.value.trim())) {
        errorMsg = 'Ingrese un correo electrónico válido.';
      }
    } else if (field.type === 'tel' && field.value.trim()) {
      const telRegex = /^[\d\s\+\-\(\)]{7,}$/;
      if (!telRegex.test(field.value.trim())) {
        errorMsg = 'Ingrese un número de teléfono válido.';
      }
    }

    if (errorMsg) {
      group.classList.add('has-error');
      errorEl.textContent = errorMsg;
      return false;
    } else {
      group.classList.remove('has-error');
      errorEl.textContent = '';
      return true;
    }
  }

  // Live validation on blur
  form.querySelectorAll('input, textarea').forEach(field => {
    field.addEventListener('blur', () => validateField(field));
    field.addEventListener('input', () => {
      if (field.closest('.form-group').classList.contains('has-error')) {
        validateField(field);
      }
    });
  });

  form.addEventListener('submit', function(e) {
    e.preventDefault();

    const fields = form.querySelectorAll('input[required], textarea[required]');
    let allValid = true;

    fields.forEach(field => {
      if (!validateField(field)) allValid = false;
    });

    if (!allValid) {
      const firstError = form.querySelector('.has-error input, .has-error textarea');
      if (firstError) firstError.focus();
      return;
    }

    // Simulate form submission (replace with real endpoint as needed)
    const submitBtn = form.querySelector('[type="submit"]');
    submitBtn.textContent = 'Enviando…';
    submitBtn.disabled = true;

    setTimeout(() => {
      form.reset();
      form.querySelectorAll('.form-group').forEach(g => g.classList.remove('has-error'));
      formSuccess.hidden = false;
      submitBtn.textContent = 'Enviar solicitud';
      submitBtn.disabled = false;

      setTimeout(() => { formSuccess.hidden = true; }, 6000);
    }, 1200);
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
