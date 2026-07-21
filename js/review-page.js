/* ══════════════════════════════════════════════
   REVIEW PAGE — Interaction logic
   ══════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ── State ── */
  let currentStep = 1;
  let selectedRating = 0;

  const starLabels = ['', 'Mala experiencia', 'Regular', 'Buena', 'Muy buena', '¡Excelente!'];

  /* ── DOM refs ── */
  const stars      = document.querySelectorAll('.rv-star');
  const starsLabel = document.getElementById('stars-label');
  const step1Next  = document.getElementById('step1-next');
  const step2Next  = document.getElementById('step2-next');
  const step3Next  = document.getElementById('step3-next');
  const rvText     = document.getElementById('rv-text');
  const charCount  = document.getElementById('rv-text-count');
  const rvName     = document.getElementById('rv-name');
  const progress   = document.getElementById('rv-progress');

  /* ══ PARTICLES CANVAS ══ */
  (function initParticles() {
    const canvas = document.getElementById('particles');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W, H, particles;

    function resize() {
      W = canvas.width  = window.innerWidth;
      H = canvas.height = window.innerHeight;
    }

    function makeParticle() {
      return {
        x:     Math.random() * W,
        y:     Math.random() * H,
        r:     Math.random() * 1.5 + 0.4,
        dx:    (Math.random() - 0.5) * 0.3,
        dy:   -(Math.random() * 0.4 + 0.1),
        alpha: Math.random() * 0.5 + 0.1,
      };
    }

    function init() {
      resize();
      particles = Array.from({ length: 80 }, makeParticle);
    }

    function draw() {
      ctx.clearRect(0, 0, W, H);
      particles.forEach(p => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(192,57,43,${p.alpha})`;
        ctx.fill();
        p.x += p.dx;
        p.y += p.dy;
        if (p.y < -4 || p.x < -4 || p.x > W + 4) Object.assign(p, makeParticle(), { y: H + 4 });
      });
      requestAnimationFrame(draw);
    }

    window.addEventListener('resize', resize);
    init();
    draw();
  })();

  /* ══ STEP NAVIGATION ══ */
  function goToStep(next, direction = 'forward') {
    const currentEl = document.getElementById('step-' + currentStep);
    const nextEl    = document.getElementById('step-' + next);
    if (!nextEl) return;

    const exitClass  = 'rv-step--exit';
    const enterClass = direction === 'forward' ? 'rv-step--enter' : 'rv-step--enter-back';

    currentEl.classList.add(exitClass);
    currentEl.addEventListener('animationend', () => {
      currentEl.classList.remove(exitClass);
      currentEl.classList.add('rv-step--hidden');
      currentEl.setAttribute('aria-hidden', 'true');

      nextEl.classList.remove('rv-step--hidden');
      nextEl.classList.add(enterClass);
      nextEl.removeAttribute('aria-hidden');
      nextEl.addEventListener('animationend', () => {
        nextEl.classList.remove(enterClass);
      }, { once: true });
    }, { once: true });

    currentStep = next;
    updateProgress(next);

    // Sync star displays
    if (next === 2 || next === 3) {
      const display2 = document.getElementById('stars-display');
      const display3 = document.getElementById('stars-display-3');
      const html = ReviewsDB.starsHTML(selectedRating);
      if (display2) display2.innerHTML = html;
      if (display3) display3.innerHTML = html;
    }
  }

  function updateProgress(step) {
    const dots = progress.querySelectorAll('.rv-dot');
    dots.forEach((dot, i) => {
      dot.classList.toggle('rv-dot--active', i + 1 === step);
    });
    progress.setAttribute('aria-valuenow', step);
    // Hide dots on success step
    progress.style.display = step === 4 ? 'none' : 'flex';
  }

  /* ══ STAR RATING ══ */
  stars.forEach(star => {
    const val = parseInt(star.dataset.value);

    star.addEventListener('mouseenter', () => highlightStars(val));
    star.addEventListener('mouseleave', () => highlightStars(selectedRating));
    star.addEventListener('focus',      () => highlightStars(val));
    star.addEventListener('blur',       () => highlightStars(selectedRating));

    star.addEventListener('click', () => {
      selectedRating = val;
      highlightStars(val);
      markSelected(val);
      starsLabel.textContent = starLabels[val];
      starsLabel.style.color = '#f39c12';
      step1Next.disabled = false;

      // Tiny bounce on selected star
      star.style.transform = 'scale(1.35)';
      setTimeout(() => { star.style.transform = ''; }, 220);
    });

    // Keyboard: space/enter to select
    star.addEventListener('keydown', e => {
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        star.click();
      }
    });
  });

  function highlightStars(upTo) {
    stars.forEach(s => {
      const v = parseInt(s.dataset.value);
      s.classList.toggle('hovered', v <= upTo);
    });
  }

  function markSelected(upTo) {
    stars.forEach(s => {
      const v = parseInt(s.dataset.value);
      s.classList.toggle('selected', v <= upTo);
    });
  }

  /* ══ STEP 1 → 2 ══ */
  step1Next.addEventListener('click', () => {
    if (selectedRating < 1) return;
    goToStep(2);
    setTimeout(() => rvText.focus(), 400);
  });

  /* ══ TEXTAREA CHAR COUNT ══ */
  rvText.addEventListener('input', () => {
    const len = rvText.value.length;
    charCount.textContent = len + ' / 500';
    charCount.classList.toggle('warn', len > 420);
    clearError(rvText);
  });

  /* ══ STEP 2 → 3 ══ */
  step2Next.addEventListener('click', () => {
    if (!rvText.value.trim()) {
      showError(rvText, 'rv-text-error', 'Por favor escriba su reseña.');
      rvText.focus();
      return;
    }
    if (rvText.value.trim().length < 15) {
      showError(rvText, 'rv-text-error', 'Su reseña debe tener al menos 15 caracteres.');
      rvText.focus();
      return;
    }
    goToStep(3);
    setTimeout(() => rvName.focus(), 400);
  });

  /* ══ STEP 3 → SUBMIT ══ */
  step3Next.addEventListener('click', () => {
    const name = rvName.value.trim();
    if (!name) {
      showError(rvName, 'rv-name-error', 'Por favor ingrese su nombre o alias.');
      rvName.focus();
      return;
    }

    ReviewsDB.submitReview({
      rating: selectedRating,
      text:   rvText.value.trim(),
      name:   name,
      since:  document.getElementById('rv-since').value.trim(),
    });

    goToStep(4);
  });

  /* ══ PREV BUTTONS ══ */
  document.querySelectorAll('.rv-prev-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = parseInt(btn.dataset.target);
      goToStep(target, 'back');
    });
  });

  /* ══ ERROR HELPERS ══ */
  function showError(field, errorId, msg) {
    field.closest('.rv-form-group').classList.add('has-error');
    const el = document.getElementById(errorId);
    if (el) el.textContent = msg;
  }

  function clearError(field) {
    const group = field.closest('.rv-form-group');
    if (group) group.classList.remove('has-error');
  }

  rvText.addEventListener('focus', () => clearError(rvText));
  rvName.addEventListener('focus', () => clearError(rvName));

})();
