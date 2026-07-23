/* ══════════════════════════════════════════════
   ADMIN PANEL — Full Logic
   Password: diana2024  (change ADMIN_PASS below)
   ══════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ── Config ── */
  const ADMIN_PASS  = 'diana2024';
  const SESSION_KEY = 'dds_admin_session';
  const APPT_KEY    = 'dds_appointments';

  /* ── State ── */
  let approvedReviews = [];
  let pendingReviews  = [];
  let sessionApproved = [];
  let appointments    = [];
  let apptFilter      = 'all';
  let activeTab       = 'pending';

  /* ── DOM ── */
  const loginScreen = document.getElementById('adm-login');
  const appScreen   = document.getElementById('adm-app');
  const loginForm   = document.getElementById('login-form');
  const passInput   = document.getElementById('adm-pass');
  const passError   = document.getElementById('adm-pass-error');
  const togglePass  = document.getElementById('toggle-pass');
  const logoutBtn   = document.getElementById('logout-btn');
  const refreshBtn  = document.getElementById('refresh-btn');
  const menuToggle  = document.getElementById('adm-menu-toggle');
  const sidebar     = document.getElementById('adm-sidebar');
  const downloadBtn = document.getElementById('download-btn');
  const toast       = document.getElementById('adm-toast');

  /* ══════════════════════════════════════════════
     AUTH
  ══════════════════════════════════════════════ */
  function isLoggedIn() { return sessionStorage.getItem(SESSION_KEY) === '1'; }

  function showApp() {
    loginScreen.hidden = true;
    appScreen.hidden   = false;
    loadAll();
  }

  function showLogin() {
    loginScreen.hidden = false;
    appScreen.hidden   = true;
    sessionStorage.removeItem(SESSION_KEY);
  }

  loginForm.addEventListener('submit', function (e) {
    e.preventDefault();
    if (passInput.value === ADMIN_PASS) {
      passError.textContent = '';
      passInput.classList.remove('has-error');
      sessionStorage.setItem(SESSION_KEY, '1');
      showApp();
    } else {
      passError.textContent = 'Contraseña incorrecta.';
      passInput.classList.add('has-error');
      passInput.focus();
      passInput.select();
      passInput.animate([
        { transform: 'translateX(-6px)' }, { transform: 'translateX(6px)' },
        { transform: 'translateX(-4px)' }, { transform: 'translateX(4px)' },
        { transform: 'translateX(0)' }
      ], { duration: 320, easing: 'ease' });
    }
  });

  logoutBtn.addEventListener('click', showLogin);

  togglePass.addEventListener('click', function () {
    const isText = passInput.type === 'text';
    passInput.type = isText ? 'password' : 'text';
    togglePass.setAttribute('aria-label', isText ? 'Mostrar contraseña' : 'Ocultar contraseña');
  });

  /* ══════════════════════════════════════════════
     LOAD ALL DATA
  ══════════════════════════════════════════════ */
  async function loadAll() {
    pendingReviews  = ReviewsDB.getPending();
    approvedReviews = await ReviewsDB.fetchApproved(true);
    appointments    = loadAppointments();
    renderAll();
  }

  function renderAll() {
    renderPending();
    renderApproved();
    renderAppointments();
    updateBadges();
    if (activeTab === 'export') renderExportPreview();
  }

  /* ══════════════════════════════════════════════
     APPOINTMENTS — localStorage CRUD
  ══════════════════════════════════════════════ */
  function loadAppointments() {
    try { return JSON.parse(localStorage.getItem(APPT_KEY) || '[]'); }
    catch { return []; }
  }

  function saveAppointments(list) {
    localStorage.setItem(APPT_KEY, JSON.stringify(list));
  }

  function updateAppointmentStatus(id, status) {
    appointments = appointments.map(a => a.id === id ? { ...a, status } : a);
    saveAppointments(appointments);
  }

  function deleteAppointment(id) {
    appointments = appointments.filter(a => a.id !== id);
    saveAppointments(appointments);
  }

  /* ══════════════════════════════════════════════
     RENDER APPOINTMENTS
  ══════════════════════════════════════════════ */
  function renderAppointments() {
    const list  = document.getElementById('appointments-list');
    const empty = document.getElementById('appointments-empty');
    if (!list) return;
    list.innerHTML = '';

    const filtered = apptFilter === 'all'
      ? appointments
      : appointments.filter(a => (a.status || 'pending') === apptFilter);

    if (!filtered.length) {
      empty.hidden = false;
      return;
    }
    empty.hidden = true;

    filtered.forEach((appt, idx) => {
      const card = buildAppointmentCard(appt);
      card.style.animationDelay = (idx * 50) + 'ms';
      list.appendChild(card);
    });

    document.getElementById('appointments-badge').textContent =
      appointments.filter(a => (a.status || 'pending') === 'pending').length;
  }

  function buildAppointmentCard(appt) {
    const card = document.createElement('article');
    const status = appt.status || 'pending';
    card.className = 'adm-review-card adm-appt-card adm-appt-card--' + status;
    card.setAttribute('role', 'listitem');
    card.dataset.id = appt.id;

    const statusLabels = { pending: 'Pendiente', confirmed: 'Confirmada', cancelled: 'Cancelada' };
    const statusColors = { pending: '#f39c12', confirmed: '#2ecc71', cancelled: '#e74c3c' };

    const dateDisplay = appt.date
      ? new Date(appt.date + 'T12:00:00').toLocaleDateString('es-CR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
      : 'Fecha no especificada';

    const timeDisplay = appt.time
      ? formatTime(appt.time)
      : 'Hora no especificada';

    const submittedDisplay = appt.submitted
      ? new Date(appt.submitted).toLocaleString('es-CR', { dateStyle: 'short', timeStyle: 'short' })
      : '';

    card.innerHTML = `
      <div class="adm-review-card__body" style="flex:1">
        <div class="adm-appt-front">
          <div class="adm-appt-header">
            <div class="adm-appt-who">
              <span class="adm-appt-name">${esc(appt.name)}</span>
              <span class="adm-appt-status-badge" style="background:${statusColors[status]}22;color:${statusColors[status]};border:1px solid ${statusColors[status]}44">
                ${statusLabels[status]}
              </span>
            </div>
            <span class="adm-appt-submitted">${submittedDisplay ? 'Enviado: ' + submittedDisplay : ''}</span>
          </div>

          <div class="adm-appt-details">
            <div class="adm-appt-detail">
              <span class="adm-appt-detail-icon">📅</span>
              <span>${dateDisplay}</span>
            </div>
            <div class="adm-appt-detail">
              <span class="adm-appt-detail-icon">🕐</span>
              <span>${timeDisplay}</span>
            </div>
            ${appt.phone ? `<div class="adm-appt-detail"><span class="adm-appt-detail-icon">📞</span><span>${esc(appt.phone)}</span></div>` : ''}
            ${appt.email ? `<div class="adm-appt-detail"><span class="adm-appt-detail-icon">✉️</span><span>${esc(appt.email)}</span></div>` : ''}
            ${appt.service ? `<div class="adm-appt-detail"><span class="adm-appt-detail-icon">🩺</span><span>${esc(appt.service)}</span></div>` : ''}
          </div>
          ${appt.message ? `<p class=\"adm-appt-message\">\"${esc(appt.message)}\"</p>` : ''}
        </div>
        <div class="adm-appt-back" aria-hidden="true">
          <div class="adm-appt-back-title">Detalle rápido</div>
          <div class="adm-appt-back-row"><span class="adm-appt-back-icon">👤</span><span>${esc(appt.name)}</span></div>
          ${appt.phone ? `<div class=\"adm-appt-back-row\"><span class=\"adm-appt-back-icon\">📞</span><a href=\"tel:${esc(appt.phone)}\">${esc(appt.phone)}</a></div>` : ''}
          ${appt.email ? `<div class=\"adm-appt-back-row\"><span class=\"adm-appt-back-icon\">✉️</span><a href=\"mailto:${esc(appt.email)}\">${esc(appt.email)}</a></div>` : ''}
          ${appt.service ? `<div class=\"adm-appt-back-row\"><span class=\"adm-appt-back-icon\">🩺</span><span>${esc(appt.service)}</span></div>` : ''}
          ${appt.message ? `<div class=\"adm-appt-detail-note\">Nota: ${esc(appt.message)}</div>` : ''}
        </div>
      </div>

      <div class="adm-review-card__actions adm-appt-actions">
        ${status === 'pending' ? `
          <button class="adm-btn adm-btn--green adm-btn--sm" data-action="confirm" data-id="${esc(appt.id)}">✔ Confirmar</button>
          <button class="adm-btn adm-btn--danger adm-btn--sm" data-action="cancel-appt" data-id="${esc(appt.id)}">✕ Cancelar</button>
        ` : ''}
        ${status === 'confirmed' ? `
          <button class="adm-btn adm-btn--danger adm-btn--sm" data-action="cancel-appt" data-id="${esc(appt.id)}">✕ Cancelar</button>
        ` : ''}
        <button class="adm-btn adm-btn--ghost adm-btn--sm adm-calendar-btn" data-action="calendar" data-id="${esc(appt.id)}"
          title="Agregar a Apple Calendar" aria-label="Descargar evento de calendario">
          <svg viewBox="0 0 20 20" fill="none" width="14" height="14" aria-hidden="true">
            <rect x="2" y="4" width="16" height="13" rx="2" stroke="currentColor" stroke-width="1.5"/>
            <path d="M6 2v4M14 2v4M2 9h16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M6 13h2v2H6z" fill="currentColor"/>
          </svg>
          .ics
        </button>
        <button class="adm-btn adm-btn--danger adm-btn--sm" data-action="delete-appt" data-id="${esc(appt.id)}">🗑</button>
      </div>
    `;

    card.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', handleApptAction);
    });

    card.addEventListener('click', function (e) {
      if (e.target.closest('a') || e.target.closest('button') || e.target.closest('[data-action]')) return;

      const card = e.currentTarget;

      if (card._singleTimer) {
        clearTimeout(card._singleTimer);
        card._singleTimer = null;
        handleCardFlip(e);
        return;
      }

      card._singleTimer = setTimeout(() => {
        card._singleTimer = null;
        const appt = appointments.find(a => a.id === card.dataset.id);
        if (appt) openDetailModal(appt);
      }, 260);
    });

    return card;
  }

  function formatTime(t) {
    if (!t) return '';
    const [h, m] = t.split(':').map(Number);
    const ampm = h >= 12 ? 'pm' : 'am';
    const h12  = h % 12 || 12;
    return `${h12}:${String(m).padStart(2,'0')} ${ampm}`;
  }

  /* ══════════════════════════════════════════════
     CARD FLIP + DETAIL OPEN
  ══════════════════════════════════════════════ */
  function handleCardOpen(e) {
    /* Only trigger when the click target is the card itself or a non-interactive child,
       not when the user clicked an <a>, <button>, or [data-action] element */
    const target = e.target;
    if (target.closest('a') || target.closest('button') || target.closest('[data-action]')) return;

    const card = e.currentTarget;
    const appt = appointments.find(a => a.id === card.dataset.id);
    if (!appt) return;
    openDetailModal(appt);
  }

  function showDetailModal(appt) {
    openDetailModal(appt);
  }

  function openDetailModal(appt) {
    closeDetailModal();
    const overlay = document.createElement('div');
    overlay.className = 'adm-appt-detail-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', 'Detalle de cita');

    const statusLabels = { pending: 'Pendiente', confirmed: 'Confirmada', cancelled: 'Cancelada' };
    const statusColors = { pending: '#f39c12', confirmed: '#2ecc71', cancelled: '#e74c3c' };
    const status = appt.status || 'pending';

    const dateDisplay = appt.date
      ? new Date(appt.date + 'T12:00:00').toLocaleDateString('es-CR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
      : 'Fecha no especificada';
    const timeDisplay = appt.time ? formatTime(appt.time) : 'Hora no especificada';

    overlay.innerHTML = `
      <div class="adm-appt-detail-card">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:16px">
          <strong style="font-family:var(--serif);font-size:1.15rem;color:var(--white)">${esc(appt.name)}</strong>
          <span style="padding:3px 10px;border-radius:100px;font-size:.72rem;font-weight:600;background:${statusColors[status]}22;color:${statusColors[status]};border:1px solid ${statusColors[status]}44">
            ${statusLabels[status]}
          </span>
        </div>
        <div class="adm-appt-detail-row"><span style="font-size:1rem">📅</span><span>${dateDisplay}</span></div>
        <div class="adm-appt-detail-row"><span style="font-size:1rem">🕐</span><span>${timeDisplay}</span></div>
        ${appt.phone ? `<div class="adm-appt-detail-row"><span style="font-size:1rem">📞</span><a href="tel:${esc(appt.phone)}">${esc(appt.phone)}</a></div>` : ''}
        ${appt.email ? `<div class="adm-appt-detail-row"><span style="font-size:1rem">✉️</span><a href="mailto:${esc(appt.email)}">${esc(appt.email)}</a></div>` : ''}
        ${appt.service ? `<div class="adm-appt-detail-row"><span style="font-size:1rem">🩺</span><span>${esc(appt.service)}</span></div>` : ''}
        ${appt.message ? `<div class="adm-appt-detail-note">"${esc(appt.message)}"</div>` : ''}
        <div class="adm-appt-detail-actions adm-appt-actions" style="margin-top:18px"></div>
        <button class="adm-btn adm-btn--ghost adm-btn--sm adm-appt-detail-close" style="margin-top:14px">Cerrar</button>
      </div>
    `;

    const detailActions = overlay.querySelector('.adm-appt-detail-actions');
    ['confirm','cancel-appt','calendar','delete-appt'].forEach(action => {
      const btn = buildApptDetailButton(action, appt);
      if (btn) detailActions.appendChild(btn);
    });

    const closeBtn = overlay.querySelector('.adm-appt-detail-close');
    closeBtn.addEventListener('click', closeDetailModal);
    detailActions.addEventListener('click', function (ev) {
      const actionBtn = ev.target.closest('[data-action]');
      if (!actionBtn) return;
      handleApptAction({ currentTarget: actionBtn });
      setTimeout(() => { if (!document.querySelector('.adm-appt-detail-overlay')) renderAppointments(); }, 280);
    });

    overlay.addEventListener('click', function (ev) {
      if (ev.target === overlay) closeDetailModal();
    });
    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';
  }

  function buildApptDetailButton(action, appt) {
    if (action === 'confirm' && appt.status === 'pending') {
      const btn = document.createElement('button');
      btn.className = 'adm-btn adm-btn--green adm-btn--sm';
      btn.setAttribute('data-action', 'confirm');
      btn.setAttribute('data-id', appt.id);
      btn.textContent = '✔ Confirmar';
      return btn;
    }
    if (action === 'cancel-appt' && (appt.status === 'pending' || appt.status === 'confirmed')) {
      const btn = document.createElement('button');
      btn.className = 'adm-btn adm-btn--danger adm-btn--sm';
      btn.setAttribute('data-action', 'cancel-appt');
      btn.setAttribute('data-id', appt.id);
      btn.textContent = '✕ Cancelar';
      return btn;
    }
    if (action === 'calendar') {
      const btn = document.createElement('button');
      btn.className = 'adm-btn adm-btn--ghost adm-btn--sm';
      btn.setAttribute('data-action', 'calendar');
      btn.setAttribute('data-id', appt.id);
      btn.innerHTML = `📅 .ics`;
      return btn;
    }
    if (action === 'delete-appt') {
      const btn = document.createElement('button');
      btn.className = 'adm-btn adm-btn--danger adm-btn--sm';
      btn.setAttribute('data-action', 'delete-appt');
      btn.setAttribute('data-id', appt.id);
      btn.textContent = '🗑';
      return btn;
    }
    return null;
  }

  function closeDetailModal() {
    const overlay = document.querySelector('.adm-appt-detail-overlay');
    if (!overlay) return;
    overlay.remove();
    document.body.style.overflow = '';
  }

  function handleCardFlip(e) {
    const card = e.currentTarget;
    const isFlipped = card.classList.contains('adm-appt-card--flipped');
    /* Close any modal before flipping */
    closeDetailModal();
    card.classList.toggle('adm-appt-card--flipped', !isFlipped);
  }

  /* ══════════════════════════════════════════════
     APPOINTMENT ACTIONS
  ══════════════════════════════════════════════ */
  function handleApptAction(e) {
    const btn    = e.currentTarget;
    const action = btn.dataset.action;
    const id     = btn.dataset.id;
    const appt   = appointments.find(a => a.id === id);

    if (action === 'confirm') {
      updateAppointmentStatus(id, 'confirmed');
      renderAppointments();
      showToast('✔ Cita confirmada.', 'green');
    }

    if (action === 'cancel-appt') {
      updateAppointmentStatus(id, 'cancelled');
      renderAppointments();
      showToast('Cita marcada como cancelada.', 'red');
    }

    if (action === 'delete-appt') {
      animateRemove(btn.closest('.adm-appt-card'), () => {
        deleteAppointment(id);
        renderAppointments();
        updateBadges();
        showToast('Solicitud eliminada.');
      });
    }

    if (action === 'calendar' && appt) {
      downloadICS(appt);
    }
  }

  /* ══════════════════════════════════════════════
     ICS / APPLE CALENDAR GENERATOR
  ══════════════════════════════════════════════ */
  function downloadICS(appt) {
    const now     = icsNow();
    const uid     = appt.id + '@docdianasanchez.com';
    const summary = `Cita – ${appt.name}${appt.service ? ' (' + appt.service + ')' : ''}`;

    /* Build start/end datetimes */
    let dtStart, dtEnd;
    if (appt.date) {
      const [yr, mo, dy] = appt.date.split('-').map(Number);
      let startH = 9, startM = 0;
      if (appt.time) {
        [startH, startM] = appt.time.split(':').map(Number);
      }
      /* 45-minute appointment by default */
      const startDate = new Date(yr, mo - 1, dy, startH, startM);
      const endDate   = new Date(startDate.getTime() + 45 * 60000);
      dtStart = icsDate(startDate);
      dtEnd   = icsDate(endDate);
    } else {
      /* No date — use floating 1-hour event tomorrow 9am */
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(9, 0, 0, 0);
      const end = new Date(tomorrow.getTime() + 60 * 60000);
      dtStart = icsDate(tomorrow);
      dtEnd   = icsDate(end);
    }

    const description = [
      appt.phone   ? `Teléfono: ${appt.phone}`   : '',
      appt.email   ? `Correo: ${appt.email}`     : '',
      appt.service ? `Servicio: ${appt.service}` : '',
      appt.message ? `Notas: ${appt.message}`    : '',
    ].filter(Boolean).join('\\n');

    const ics = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//Dra. Diana Sánchez//Citas//ES',
      'CALSCALE:GREGORIAN',
      'METHOD:PUBLISH',
      'BEGIN:VEVENT',
      `UID:${uid}`,
      `DTSTAMP:${now}`,
      `DTSTART:${dtStart}`,
      `DTEND:${dtEnd}`,
      `SUMMARY:${icsText(summary)}`,
      `DESCRIPTION:${icsText(description)}`,
      'LOCATION:San José\\, Costa Rica',
      'STATUS:CONFIRMED',
      'BEGIN:VALARM',
      'TRIGGER:-PT30M',
      'ACTION:DISPLAY',
      'DESCRIPTION:Recordatorio de cita',
      'END:VALARM',
      'END:VEVENT',
      'END:VCALENDAR'
    ].join('\r\n');

    const blob = new Blob([ics], { type: 'text/calendar;charset=utf-8' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `cita-${appt.name.replace(/\s+/g,'-').toLowerCase()}.ics`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);

    showToast('📅 Archivo .ics descargado — ábralo para agregar a Calendar.', 'green');
  }

  function icsDate(d) {
    const pad = n => String(n).padStart(2,'0');
    return `${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}T${pad(d.getHours())}${pad(d.getMinutes())}00`;
  }

  function icsNow() {
    return icsDate(new Date()) + 'Z';
  }

  function icsText(str) {
    return String(str).replace(/[,;\\]/g, c => '\\' + c);
  }

  /* ══════════════════════════════════════════════
     APPOINTMENT FILTERS
  ══════════════════════════════════════════════ */
  document.querySelectorAll('.adm-filter-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      apptFilter = this.dataset.filter;
      document.querySelectorAll('.adm-filter-btn').forEach(b => b.classList.remove('adm-filter-btn--active'));
      this.classList.add('adm-filter-btn--active');
      renderAppointments();
    });
  });

  const clearApptBtn = document.getElementById('clear-appointments-btn');
  if (clearApptBtn) {
    clearApptBtn.addEventListener('click', function () {
      if (!confirm('¿Eliminar TODAS las solicitudes de cita? Esta acción no se puede deshacer.')) return;
      localStorage.removeItem(APPT_KEY);
      appointments = [];
      renderAppointments();
      updateBadges();
      showToast('Todas las solicitudes eliminadas.');
    });
  }

  /* ══════════════════════════════════════════════
     REVIEWS — PENDING
  ══════════════════════════════════════════════ */
  function renderPending() {
    const list  = document.getElementById('pending-list');
    const empty = document.getElementById('pending-empty');
    list.innerHTML = '';

    if (!pendingReviews.length) { empty.hidden = false; return; }
    empty.hidden = true;

    pendingReviews.forEach((review, idx) => {
      const card = buildReviewCard(review, 'pending');
      card.style.animationDelay = (idx * 60) + 'ms';
      list.appendChild(card);
    });
  }

  /* ══════════════════════════════════════════════
     REVIEWS — APPROVED
  ══════════════════════════════════════════════ */
  function renderApproved() {
    const list  = document.getElementById('approved-list');
    const empty = document.getElementById('approved-empty');
    list.innerHTML = '';

    const merged = mergeApproved();
    if (!merged.length) { empty.hidden = false; return; }
    empty.hidden = true;

    merged.forEach((review, idx) => {
      const card = buildReviewCard(review, 'approved');
      card.style.animationDelay = (idx * 60) + 'ms';
      list.appendChild(card);
    });
  }

  function mergeApproved() {
    const ids   = new Set(approvedReviews.map(r => r.id));
    const extra = sessionApproved.filter(r => !ids.has(r.id));
    return [...approvedReviews, ...extra];
  }

  function buildReviewCard(review, type) {
    const card = document.createElement('article');
    card.className = 'adm-review-card adm-review-card--' + type;
    card.setAttribute('role', 'listitem');
    card.dataset.id = review.id;

    const since   = review.since ? `<span class="adm-review-card__since">${esc(review.since)}</span>` : '';
    const dateStr = review.date  ? `<span class="adm-review-card__date">${review.date}</span>` : '';

    let actions = type === 'pending'
      ? `<div class="adm-review-card__actions">
           <button class="adm-btn adm-btn--green adm-btn--sm" data-action="approve" data-id="${esc(review.id)}">✔ Aprobar</button>
           <button class="adm-btn adm-btn--danger adm-btn--sm" data-action="reject" data-id="${esc(review.id)}">✕ Rechazar</button>
         </div>`
      : `<div class="adm-review-card__actions">
           <button class="adm-btn adm-btn--danger adm-btn--sm" data-action="delete-approved" data-id="${esc(review.id)}">✕ Eliminar</button>
         </div>`;

    card.innerHTML = `
      <div class="adm-review-card__body">
        <div class="adm-review-card__meta">
          <span class="adm-review-card__stars">${ReviewsDB.starsHTML(review.rating)}</span>
          <span class="adm-review-card__name">${esc(review.name)}</span>
          ${since}${dateStr}
        </div>
        <p class="adm-review-card__text">${esc(review.text)}</p>
      </div>
      ${actions}
    `;

    card.querySelectorAll('[data-action]').forEach(btn => btn.addEventListener('click', handleReviewAction));
    return card;
  }

  function handleReviewAction(e) {
    const btn    = e.currentTarget;
    const action = btn.dataset.action;
    const id     = btn.dataset.id;

    if (action === 'approve') {
      const review = pendingReviews.find(r => r.id === id);
      if (!review) return;
      sessionApproved.push({ ...review, approved: true });
      ReviewsDB.deletePending(id);
      pendingReviews = ReviewsDB.getPending();
      animateRemove(btn.closest('.adm-review-card'), () => { renderAll(); showToast('✔ Reseña aprobada. Recuerde exportar.', 'green'); });
    }
    if (action === 'reject') {
      animateRemove(btn.closest('.adm-review-card'), () => {
        ReviewsDB.deletePending(id);
        pendingReviews = ReviewsDB.getPending();
        renderAll();
        showToast('Reseña rechazada.');
      });
    }
    if (action === 'delete-approved') {
      approvedReviews = approvedReviews.filter(r => r.id !== id);
      sessionApproved = sessionApproved.filter(r => r.id !== id);
      animateRemove(btn.closest('.adm-review-card'), () => { renderAll(); showToast('Reseña eliminada. Descargue reviews.json.', 'red'); });
    }
  }

  /* ══════════════════════════════════════════════
     BADGES
  ══════════════════════════════════════════════ */
  function updateBadges() {
    document.getElementById('pending-badge').textContent      = pendingReviews.length;
    document.getElementById('approved-badge').textContent     = mergeApproved().length;
    const pendingAppts = appointments.filter(a => (a.status || 'pending') === 'pending').length;
    const apptBadge    = document.getElementById('appointments-badge');
    if (apptBadge) apptBadge.textContent = pendingAppts;
  }

  /* ══════════════════════════════════════════════
     EXPORT TAB
  ══════════════════════════════════════════════ */
  function renderExportPreview() {
    const merged  = mergeApproved();
    const preview = document.getElementById('export-preview');
    const count   = document.getElementById('export-count');
    if (!preview || !count) return;
    count.textContent   = merged.length + ' reseña' + (merged.length !== 1 ? 's' : '');
    preview.textContent = JSON.stringify(merged, null, 2);
  }

  downloadBtn.addEventListener('click', function () {
    ReviewsDB.exportJSON(mergeApproved());
    showToast('✔ reviews.json descargado. Haga commit y push.', 'green');
  });

  /* ══════════════════════════════════════════════
     TAB SWITCHING
  ══════════════════════════════════════════════ */
  document.querySelectorAll('.adm-nav__item').forEach(item => {
    item.addEventListener('click', function () { switchTab(this.dataset.tab); });
  });

  function switchTab(tab) {
    activeTab = tab;

    document.querySelectorAll('.adm-nav__item').forEach(item => {
      const active = item.dataset.tab === tab;
      item.classList.toggle('adm-nav__item--active', active);
      item.setAttribute('aria-current', active ? 'page' : 'false');
    });

    document.querySelectorAll('.adm-tab').forEach(panel => {
      panel.classList.toggle('adm-tab--hidden', panel.id !== 'tab-' + tab);
    });

    const titles = {
      pending:      ['Reseñas pendientes',        'Apruebe o rechace las reseñas enviadas por pacientes'],
      approved:     ['Reseñas aprobadas',          'Reseñas publicadas actualmente en el sitio'],
      export:       ['Exportar & publicar',        'Descargue reviews.json y haga push para publicar'],
      appointments: ['Solicitudes de cita',        'Gestione las citas y agréguelas a su calendario'],
    };
    if (titles[tab]) {
      document.getElementById('tab-title').textContent = titles[tab][0];
      document.getElementById('tab-sub').textContent   = titles[tab][1];
    }

    if (tab === 'export') renderExportPreview();
    if (tab === 'appointments') renderAppointments();

    sidebar.classList.remove('open');
    menuToggle.setAttribute('aria-expanded', 'false');
  }

  /* ══════════════════════════════════════════════
     MOBILE SIDEBAR
  ══════════════════════════════════════════════ */
  menuToggle.addEventListener('click', function () {
    const isOpen = sidebar.classList.toggle('open');
    menuToggle.setAttribute('aria-expanded', isOpen);
  });

  document.addEventListener('click', function (e) {
    if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== menuToggle) {
      sidebar.classList.remove('open');
      menuToggle.setAttribute('aria-expanded', 'false');
    }
  });

  /* ══════════════════════════════════════════════
     REFRESH
  ══════════════════════════════════════════════ */
  refreshBtn.addEventListener('click', async function () {
    refreshBtn.disabled    = true;
    refreshBtn.textContent = 'Actualizando…';
    await loadAll();
    refreshBtn.disabled = false;
    refreshBtn.innerHTML = `<svg viewBox="0 0 20 20" fill="none" width="16" height="16" aria-hidden="true"><path d="M4 10a6 6 0 1 0 1.1-3.4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M2 5l3 2-2 3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg> Actualizar`;
    showToast('Datos actualizados.');
  });

  /* ══════════════════════════════════════════════
     SHARED HELPERS
  ══════════════════════════════════════════════ */
  function esc(str) {
    return String(str)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;')
      .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  function animateRemove(el, cb) {
    if (!el) { cb(); return; }
    el.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
    el.style.opacity    = '0';
    el.style.transform  = 'translateX(30px)';
    setTimeout(cb, 270);
  }

  let toastTimer;
  function showToast(msg, type) {
    toast.textContent = msg;
    toast.style.borderColor = type === 'green'
      ? 'rgba(46,204,113,0.3)' : type === 'red'
      ? 'rgba(231,76,60,0.3)' : 'var(--border)';
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 3800);
  }

  /* ══════════════════════════════════════════════
     INIT
  ══════════════════════════════════════════════ */
  if (isLoggedIn()) showApp();

})();
