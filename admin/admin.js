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
  let activeTab       = 'dashboard';

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
          ${appt.phone ? `<div class="adm-appt-detail"><span class="adm-appt-detail-icon">📞</span><a href="tel:${esc(appt.phone)}" onclick="event.stopPropagation();">${esc(appt.phone)}</a></div>` : ''}
          ${appt.email ? `<div class="adm-appt-detail"><span class="adm-appt-detail-icon">✉️</span><a href="mailto:${esc(appt.email)}" onclick="event.stopPropagation();">${esc(appt.email)}</a></div>` : ''}
          ${appt.service ? `<div class="adm-appt-detail"><span class="adm-appt-detail-icon">🩺</span><span>${esc(appt.service)}</span></div>` : ''}
        </div>

        ${appt.message ? `<p class="adm-appt-message">"${esc(appt.message)}"</p>` : ''}
      </div>

      <div class="adm-review-card__actions adm-appt-actions">
        ${status === 'pending' ? `
          <button class="adm-btn adm-btn--green adm-btn--sm" data-action="confirm" data-id="${esc(appt.id)}" onclick="event.stopPropagation();">✔ Confirmar</button>
          <button class="adm-btn adm-btn--danger adm-btn--sm" data-action="cancel-appt" data-id="${esc(appt.id)}" onclick="event.stopPropagation();">✕ Cancelar</button>
        ` : ''}
        ${status === 'confirmed' ? `
          <button class="adm-btn adm-btn--danger adm-btn--sm" data-action="cancel-appt" data-id="${esc(appt.id)}" onclick="event.stopPropagation();">✕ Cancelar</button>
        ` : ''}
        <button class="adm-btn adm-btn--ghost adm-btn--sm adm-calendar-btn" data-action="calendar" data-id="${esc(appt.id)}"
          title="Agregar a Apple Calendar" aria-label="Descargar evento de calendario" onclick="event.stopPropagation();">
          <svg viewBox="0 0 20 20" fill="none" width="14" height="14" aria-hidden="true">
            <rect x="2" y="4" width="16" height="13" rx="2" stroke="currentColor" stroke-width="1.5"/>
            <path d="M6 2v4M14 2v4M2 9h16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M6 13h2v2H6z" fill="currentColor"/>
          </svg>
          .ics
        </button>
        <button class="adm-btn adm-btn--primary adm-btn--sm" 
                onclick="event.stopPropagation(); window.openMedicalRecordsById('${esc(appt.id)}');" 
                title="Open Medical Records">
          🩺 Records
        </button>
        <button class="adm-btn adm-btn--danger adm-btn--sm" data-action="delete-appt" data-id="${esc(appt.id)}" onclick="event.stopPropagation();">🗑</button>
      </div>
    `;

    card.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', handleApptAction);
    });

    // Add double-click and long-press functionality for medical records
    addMedicalRecordsInteraction(card, appt);

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
     MEDICAL RECORDS INTERACTION
  ══════════════════════════════════════════════ */
  function addMedicalRecordsInteraction(card, appt) {
    let longPressTimer = null;
    let touchStartX = 0;
    let touchStartY = 0;
    let isLongPress = false;

    // Add visual interaction class
    card.classList.add('medical-interactive');

    // Prevent double-click on buttons from interfering
    const cardBody = card.querySelector('.adm-review-card__body');
    if (cardBody) {
      // Double-click handler on card body (not buttons)
      cardBody.addEventListener('dblclick', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('Double-click detected, opening medical records for:', appt.name);
        openMedicalRecords(appt);
      });

      // Touch handlers for long press on card body
      cardBody.addEventListener('touchstart', function(e) {
        if (e.target.closest('button') || e.target.closest('a')) {
          return; // Don't trigger on buttons or links
        }
        
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
        isLongPress = false;
        
        longPressTimer = setTimeout(() => {
          isLongPress = true;
          // Add haptic feedback if available
          if (navigator.vibrate) {
            navigator.vibrate(50);
          }
          console.log('Long press detected, opening medical records for:', appt.name);
          openMedicalRecords(appt);
        }, 800); // 800ms for long press
      }, { passive: true });

      cardBody.addEventListener('touchend', function(e) {
        clearTimeout(longPressTimer);
        // Prevent click if it was a long press
        if (isLongPress) {
          e.preventDefault();
          e.stopPropagation();
        }
      }, { passive: false });

      cardBody.addEventListener('touchmove', function(e) {
        if (longPressTimer) {
          const currentX = e.touches[0].clientX;
          const currentY = e.touches[0].clientY;
          const deltaX = Math.abs(currentX - touchStartX);
          const deltaY = Math.abs(currentY - touchStartY);
          
          // Cancel long press if user moves finger too much (scrolling)
          if (deltaX > 15 || deltaY > 15) {
            clearTimeout(longPressTimer);
            longPressTimer = null;
          }
        }
      }, { passive: true });
    }

    // Fallback: whole card double-click if body not found
    if (!cardBody) {
      card.addEventListener('dblclick', function(e) {
        if (!e.target.closest('button') && !e.target.closest('a')) {
          e.preventDefault();
          e.stopPropagation();
          openMedicalRecords(appt);
        }
      });
    }
  }

  function openMedicalRecords(appt) {
    console.log('openMedicalRecords called with:', appt);
    
    if (!appt || !appt.id) {
      console.error('Invalid appointment data:', appt);
      showToast('Error: Invalid appointment data', 'red');
      return;
    }

    // Show loading state
    showToast('Opening medical records...', 'green');

    // Open medical records in new tab
    const url = `./medical-records.html?booking_id=${encodeURIComponent(appt.id)}`;
    console.log('Opening URL:', url);
    
    try {
      const medicalWindow = window.open(url, '_blank', 'width=1400,height=900,scrollbars=yes,resizable=yes');
      
      if (!medicalWindow) {
        console.error('Window.open blocked');
        showToast('Please allow popups to open medical records', 'red');
      } else {
        console.log('Medical records window opened successfully');
        showToast('Medical records opened in new tab', 'green');
      }
    } catch (error) {
      console.error('Error opening medical records:', error);
      showToast('Error opening medical records: ' + error.message, 'red');
    }
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
      dashboard:    ['Dashboard',                  'Overview of your medical practice'],
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
    if (tab === 'dashboard') renderDashboard();

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
     DASHBOARD & CHARTS
  ══════════════════════════════════════════════ */
  function renderDashboard() {
    updateDashboardStats();
    renderAppointmentsChart();
    renderStatusChart();
    renderReviewsChart();
    renderServiceBars();
    renderRecentActivity();
  }

  function updateDashboardStats() {
    // Total unique patients (by email)
    const uniquePatients = new Set(appointments.map(a => a.email)).size;
    document.getElementById('total-patients').textContent = uniquePatients;
    
    // Total appointments
    document.getElementById('total-appointments').textContent = appointments.length;
    
    // Total reviews
    const totalReviews = pendingReviews.length + mergeApproved().length;
    document.getElementById('total-reviews').textContent = totalReviews;
    
    // Average rating
    const approvedReviews = mergeApproved();
    const avgRating = approvedReviews.length > 0
      ? (approvedReviews.reduce((sum, review) => sum + review.rating, 0) / approvedReviews.length).toFixed(1)
      : '0.0';
    document.getElementById('avg-rating').textContent = avgRating;
    
    // Update change indicators
    const thisWeekAppts = appointments.filter(a => {
      const apptDate = new Date(a.date || a.submitted);
      const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
      return apptDate > weekAgo;
    }).length;
    
    document.getElementById('appointments-change').textContent = `+${thisWeekAppts} this week`;
    document.getElementById('reviews-change').textContent = `+${pendingReviews.length} pending approval`;
    document.getElementById('rating-change').textContent = `Based on ${approvedReviews.length} reviews`;
    document.getElementById('patients-change').textContent = `${uniquePatients} unique patients`;
  }

  function renderAppointmentsChart() {
    const canvas = document.getElementById('appointments-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const period = parseInt(document.getElementById('appointments-period')?.value || '7');
    
    // Generate last N days data
    const days = [];
    const counts = [];
    const colors = [];
    
    for (let i = period - 1; i >= 0; i--) {
      const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000);
      const dateStr = date.toISOString().split('T')[0];
      
      const dayAppointments = appointments.filter(a => a.date === dateStr).length;
      days.push(date.toLocaleDateString('es-CR', { weekday: 'short', day: 'numeric' }));
      counts.push(dayAppointments);
      colors.push(dayAppointments > 2 ? 'rgba(46,204,113,0.8)' : dayAppointments > 0 ? 'rgba(243,156,18,0.8)' : 'rgba(127,140,141,0.3)');
    }
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Chart dimensions
    const padding = 40;
    const chartWidth = canvas.width - (padding * 2);
    const chartHeight = canvas.height - (padding * 2);
    const barWidth = chartWidth / days.length * 0.8;
    const maxCount = Math.max(...counts) || 1;
    
    // Draw bars
    days.forEach((day, index) => {
      const barHeight = (counts[index] / maxCount) * chartHeight;
      const x = padding + (index * chartWidth / days.length) + (chartWidth / days.length - barWidth) / 2;
      const y = padding + chartHeight - barHeight;
      
      // Bar
      ctx.fillStyle = colors[index];
      ctx.fillRect(x, y, barWidth, barHeight);
      
      // Value label
      if (counts[index] > 0) {
        ctx.fillStyle = '#ffffff';
        ctx.font = '12px Inter';
        ctx.textAlign = 'center';
        ctx.fillText(counts[index], x + barWidth / 2, y - 5);
      }
      
      // Day label
      ctx.fillStyle = '#9a9a9a';
      ctx.font = '10px Inter';
      ctx.textAlign = 'center';
      ctx.fillText(day, x + barWidth / 2, canvas.height - 10);
    });
  }

  function renderStatusChart() {
    const canvas = document.getElementById('status-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const statusCounts = {
      pending: appointments.filter(a => (a.status || 'pending') === 'pending').length,
      confirmed: appointments.filter(a => a.status === 'confirmed').length,
      cancelled: appointments.filter(a => a.status === 'cancelled').length
    };
    
    const total = Object.values(statusCounts).reduce((sum, count) => sum + count, 0);
    if (total === 0) {
      ctx.fillStyle = '#9a9a9a';
      ctx.font = '14px Inter';
      ctx.textAlign = 'center';
      ctx.fillText('No appointments yet', canvas.width / 2, canvas.height / 2);
      return;
    }
    
    const colors = {
      pending: '#f39c12',
      confirmed: '#2ecc71',
      cancelled: '#e74c3c'
    };
    
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 20;
    
    let startAngle = -Math.PI / 2; // Start at top
    
    // Draw pie slices
    Object.entries(statusCounts).forEach(([status, count]) => {
      if (count === 0) return;
      
      const sliceAngle = (count / total) * 2 * Math.PI;
      
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
      ctx.lineTo(centerX, centerY);
      ctx.fillStyle = colors[status];
      ctx.fill();
      
      // Label
      const labelAngle = startAngle + sliceAngle / 2;
      const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7);
      const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7);
      
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 12px Inter';
      ctx.textAlign = 'center';
      ctx.fillText(count, labelX, labelY);
      
      startAngle += sliceAngle;
    });
    
    // Update legend
    const legend = document.getElementById('status-legend');
    if (legend) {
      legend.innerHTML = Object.entries(statusCounts)
        .filter(([_, count]) => count > 0)
        .map(([status, count]) => `
          <div class="adm-legend-item">
            <div class="adm-legend-color" style="background: ${colors[status]}"></div>
            <span>${status.charAt(0).toUpperCase() + status.slice(1)}: ${count}</span>
          </div>
        `).join('');
    }
  }

  function renderReviewsChart() {
    const canvas = document.getElementById('reviews-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Generate 30-day review data
    const days = [];
    const pendingCounts = [];
    const approvedCounts = [];
    
    for (let i = 29; i >= 0; i--) {
      const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000);
      const dateStr = date.toISOString().split('T')[0];
      
      // For demo purposes, generate some sample data
      const dayPending = Math.floor(Math.random() * 3);
      const dayApproved = Math.floor(Math.random() * 2);
      
      days.push(i % 5 === 0 ? date.toLocaleDateString('es-CR', { day: 'numeric', month: 'short' }) : '');
      pendingCounts.push(dayPending);
      approvedCounts.push(dayApproved);
    }
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    const padding = 30;
    const chartWidth = canvas.width - (padding * 2);
    const chartHeight = canvas.height - (padding * 2);
    const maxCount = Math.max(...pendingCounts, ...approvedCounts) || 1;
    
    // Draw lines
    ctx.strokeStyle = '#f39c12';
    ctx.lineWidth = 2;
    ctx.beginPath();
    pendingCounts.forEach((count, index) => {
      const x = padding + (index / (pendingCounts.length - 1)) * chartWidth;
      const y = padding + chartHeight - (count / maxCount) * chartHeight;
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    
    ctx.strokeStyle = '#2ecc71';
    ctx.beginPath();
    approvedCounts.forEach((count, index) => {
      const x = padding + (index / (approvedCounts.length - 1)) * chartWidth;
      const y = padding + chartHeight - (count / maxCount) * chartHeight;
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    
    // Draw labels
    ctx.fillStyle = '#9a9a9a';
    ctx.font = '10px Inter';
    ctx.textAlign = 'center';
    days.forEach((day, index) => {
      if (day) {
        const x = padding + (index / (days.length - 1)) * chartWidth;
        ctx.fillText(day, x, canvas.height - 5);
      }
    });
  }

  function renderServiceBars() {
    const container = document.getElementById('service-bars');
    if (!container) return;
    
    // Count services
    const serviceCounts = {};
    appointments.forEach(appt => {
      if (appt.service) {
        serviceCounts[appt.service] = (serviceCounts[appt.service] || 0) + 1;
      }
    });
    
    const sortedServices = Object.entries(serviceCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5); // Top 5 services
    
    if (sortedServices.length === 0) {
      container.innerHTML = '<div class="adm-empty-chart">No service data yet</div>';
      return;
    }
    
    const maxCount = sortedServices[0][1];
    
    container.innerHTML = sortedServices.map(([service, count]) => {
      const percentage = (count / maxCount) * 100;
      return `
        <div class="adm-service-bar">
          <div class="adm-service-bar__label">
            <span>${service}</span>
            <span class="adm-service-bar__count">${count}</span>
          </div>
          <div class="adm-service-bar__progress">
            <div class="adm-service-bar__fill" style="width: ${percentage}%"></div>
          </div>
        </div>
      `;
    }).join('');
  }

  function renderRecentActivity() {
    const container = document.getElementById('activity-list');
    if (!container) return;
    
    // Combine recent appointments and reviews
    const recentActivities = [];
    
    // Recent appointments
    appointments.slice(-5).forEach(appt => {
      recentActivities.push({
        type: 'appointment',
        text: `New appointment from ${appt.name}`,
        service: appt.service,
        time: new Date(appt.submitted || Date.now()).toLocaleDateString('es-CR', { 
          month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
        }),
        icon: '📅'
      });
    });
    
    // Recent reviews
    pendingReviews.slice(-3).forEach(review => {
      recentActivities.push({
        type: 'review',
        text: `New review from ${review.name}`,
        rating: review.rating,
        time: 'Recently',
        icon: '⭐'
      });
    });
    
    // Sort by most recent
    recentActivities.sort((a, b) => new Date(b.time) - new Date(a.time));
    
    if (recentActivities.length === 0) {
      container.innerHTML = '<div class="adm-activity-empty">No recent activity</div>';
      return;
    }
    
    container.innerHTML = recentActivities.slice(0, 8).map(activity => `
      <div class="adm-activity-item">
        <div class="adm-activity-item__icon">${activity.icon}</div>
        <div class="adm-activity-item__content">
          <div class="adm-activity-item__text">${activity.text}</div>
          ${activity.service ? `<div class="adm-activity-item__meta">${activity.service}</div>` : ''}
          ${activity.rating ? `<div class="adm-activity-item__meta">${'★'.repeat(activity.rating)} (${activity.rating}/5)</div>` : ''}
        </div>
        <div class="adm-activity-item__time">${activity.time}</div>
      </div>
    `).join('');
  }

  // Event listeners for dashboard
  document.addEventListener('DOMContentLoaded', () => {
    const periodSelect = document.getElementById('appointments-period');
    if (periodSelect) {
      periodSelect.addEventListener('change', renderAppointmentsChart);
    }
    
    const refreshActivity = document.getElementById('refresh-activity');
    if (refreshActivity) {
      refreshActivity.addEventListener('click', renderRecentActivity);
    }
  });

  /* ══════════════════════════════════════════════
     INIT
  ══════════════════════════════════════════════ */
  if (isLoggedIn()) showApp();

  // Expose functions globally for inline event handlers
  window.adminApp = {
    openMedicalRecords: openMedicalRecords,
    appointments: appointments
  };
  
  window.openMedicalRecordsById = function(appointmentId) {
    const appt = appointments.find(a => a.id === appointmentId);
    if (appt) {
      openMedicalRecords(appt);
    } else {
      console.error('Appointment not found:', appointmentId);
      showToast('Appointment not found', 'red');
    }
  };

})();
