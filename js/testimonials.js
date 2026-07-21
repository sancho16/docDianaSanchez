/* ══════════════════════════════════════════════
   TESTIMONIALS — Dynamic loader from reviews.json
   ══════════════════════════════════════════════ */

(function () {
  'use strict';

  const grid = document.getElementById('testimonials-grid');
  if (!grid) return;

  async function loadTestimonials() {
    let reviews = [];

    try {
      const res = await fetch('reviews/reviews.json?t=' + Date.now());
      if (res.ok) reviews = await res.json();
    } catch (e) {
      console.warn('Could not load reviews.json, using fallback.', e);
    }

    /* Filter only approved */
    const approved = reviews.filter(r => r.approved);

    /* Remove skeletons */
    grid.innerHTML = '';

    if (!approved.length) {
      grid.innerHTML = '<p style="text-align:center;color:var(--muted);grid-column:1/-1">Próximamente reseñas de pacientes.</p>';
      return;
    }

    approved.forEach((r, i) => {
      const card = document.createElement('blockquote');
      card.className = 'testimonial-card reveal';
      card.setAttribute('role', 'listitem');
      card.style.animationDelay = (i * 80) + 'ms';

      const stars = Array.from({ length: 5 }, (_, idx) =>
        `<span style="color:${idx < r.rating ? '#f39c12' : 'rgba(255,255,255,0.15)'}" aria-hidden="true">★</span>`
      ).join('');

      const since = r.since
        ? `<span>${escHtml(r.since)}</span>`
        : '';

      card.innerHTML = `
        <div class="testimonial-card__stars" aria-label="${r.rating} de 5 estrellas">${stars}</div>
        <p>"${escHtml(r.text)}"</p>
        <footer>
          <strong>${escHtml(r.name)}</strong>
          ${since}
        </footer>
      `;

      grid.appendChild(card);
    });

    /* Trigger reveal animations */
    requestAnimationFrame(() => {
      grid.querySelectorAll('.reveal').forEach(el => {
        el.classList.add('visible');
      });
    });
  }

  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  loadTestimonials();

})();
