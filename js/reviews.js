/* ══════════════════════════════════════════════
   REVIEWS ENGINE — shared by review.html,
   admin/index.html, and index.html
   ══════════════════════════════════════════════ */

const ReviewsDB = (function () {
  'use strict';

  const PENDING_KEY = 'dds_pending_reviews';   // localStorage key for submitted reviews
  const APPROVED_URL = '../reviews/reviews.json'; // path from admin/ context
  const APPROVED_URL_ROOT = 'reviews/reviews.json'; // path from root context

  /* ── Helpers ── */
  function generateId() {
    return 'r' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  }

  function today() {
    return new Date().toISOString().slice(0, 10);
  }

  /* ── Pending reviews (localStorage) ── */
  function getPending() {
    try {
      return JSON.parse(localStorage.getItem(PENDING_KEY) || '[]');
    } catch {
      return [];
    }
  }

  function savePending(list) {
    localStorage.setItem(PENDING_KEY, JSON.stringify(list));
  }

  function submitReview(data) {
    const review = {
      id:       generateId(),
      name:     (data.name || 'Paciente anónimo/a').trim(),
      since:    (data.since || '').trim(),
      rating:   Number(data.rating) || 5,
      text:     (data.text || '').trim(),
      approved: false,
      date:     today()
    };
    const list = getPending();
    list.unshift(review);
    savePending(list);
    return review;
  }

  function deletePending(id) {
    savePending(getPending().filter(r => r.id !== id));
  }

  function clearAllPending() {
    localStorage.removeItem(PENDING_KEY);
  }

  /* ── Approved reviews (reviews.json, fetched) ── */
  async function fetchApproved(fromAdmin = false) {
    const url = fromAdmin ? APPROVED_URL : APPROVED_URL_ROOT;
    try {
      const res = await fetch(url + '?t=' + Date.now());
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  }

  /* ── Export helpers (used by admin) ── */
  function exportJSON(data) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = 'reviews.json';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  /* ── Star rendering helper ── */
  function starsHTML(rating, colored = true) {
    return Array.from({ length: 5 }, (_, i) => {
      const filled = i < rating;
      const color  = filled && colored ? '#f39c12' : 'rgba(255,255,255,0.15)';
      return `<span aria-hidden="true" style="color:${color}">★</span>`;
    }).join('');
  }

  /* ── Public API ── */
  return {
    getPending,
    savePending,
    submitReview,
    deletePending,
    clearAllPending,
    fetchApproved,
    exportJSON,
    starsHTML,
  };
})();
