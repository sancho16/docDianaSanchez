/* ══════════════════════════════════════════════
   VIDEO SCRUB — Scroll-driven video playback
   Plays forward on scroll down, backward on up
   ══════════════════════════════════════════════ */

(function () {
  'use strict';

  const video    = document.getElementById('scrub-video');
  const track    = document.getElementById('vid-track');
  const bar      = document.getElementById('vid-progress-bar');

  if (!video || !track) return;

  let duration   = 0;
  let rafPending = false;
  let targetTime = 0;
  let currentTime = 0;

  /* ── Once metadata loads, set track height proportional to duration ── */
  function onMeta() {
    duration = video.duration;
    /* Each second of video = 120px of scroll track */
    track.style.height = Math.ceil(duration * 120) + 'px';
    updateFrame();
  }

  video.addEventListener('loadedmetadata', onMeta);

  /* If already loaded (cached) */
  if (video.readyState >= 1) onMeta();

  /* ── Map scroll position → video time ── */
  function getTargetTime() {
    const rect      = track.closest('.vid-scrub').getBoundingClientRect();
    const sectionH  = track.closest('.vid-scrub').offsetHeight;
    const viewH     = window.innerHeight;

    /* Progress: 0 when section top hits viewport bottom → 1 when section bottom hits viewport top */
    const scrolled  = -rect.top;
    const total     = sectionH - viewH;
    const progress  = Math.min(1, Math.max(0, scrolled / total));

    return progress * duration;
  }

  /* ── Smooth lerp toward target ── */
  function updateFrame() {
    if (!duration) return;

    targetTime  = getTargetTime();
    /* Lerp: 12% per frame ≈ smooth but responsive */
    currentTime += (targetTime - currentTime) * 0.12;

    const clamped = Math.min(duration, Math.max(0, currentTime));
    video.currentTime = clamped;

    /* Progress bar */
    if (bar) bar.style.width = (clamped / duration * 100) + '%';

    rafPending = false;
  }

  window.addEventListener('scroll', function () {
    if (!rafPending) {
      rafPending = true;
      requestAnimationFrame(updateFrame);
    }
  }, { passive: true });

  window.addEventListener('resize', updateFrame);

})();
