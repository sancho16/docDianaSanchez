/* ══════════════════════════════════════════════
   ADMIN PANEL — Full Logic
   Password: diana2024  (change ADMIN_PASS below)
   ══════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ── Config ── */
  const APPT_KEY    = 'dds_appointments';
  const API_URL     = 'https://api.docdianasanchez.com';
  const API_HOST_KEY = 'dds_api_host';

  /* ── State ── */
  let approvedReviews = [];
  let pendingReviews  = [];
  let sessionApproved = [];
  let appointments    = [];
  let apptFilter      = 'all';
  let activeTab       = 'pending';

  /* ── DOM ── */
  const appScreen   = document.getElementById('adm-app');
  const refreshBtn  = document.getElementById('refresh-btn');
  const menuToggle  = document.getElementById('adm-menu-toggle');
  const sidebar     = document.getElementById('adm-sidebar');
  const downloadBtn = document.getElementById('download-btn');
  const toast       = document.getElementById('adm-toast');
  const searchInput = document.getElementById('adm-search');
  const themeToggle = document.getElementById('theme-toggle');

  /* ══════════════════════════════════════════════
     THEME TOGGLE
  ══════════════════════════════════════════════ */
  const THEME_KEY = 'dds_admin_theme';
  
  function loadTheme() {
    const savedTheme = localStorage.getItem(THEME_KEY);
    if (savedTheme === 'light') {
      document.body.classList.add('light-theme');
      updateThemeToggleText('dark');
    } else {
      document.body.classList.remove('light-theme');
      updateThemeToggleText('light');
    }
  }

  function updateThemeToggleText(nextTheme) {
    if (nextTheme === 'light') {
      themeToggle.innerHTML = `
        <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" width="16" height="16">
          <path d="M10 2.5a.5.5 0 01.5.5v1a.5.5 0 01-1 0V3a.5.5 0 01.5-.5zM16 10a.5.5 0 01.5-.5h1a.5.5 0 010 1h-1a.5.5 0 01-.5-.5zM10 16a.5.5 0 01.5.5v1a.5.5 0 01-1 0v-1a.5.5 0 01.5-.5zM3 10a.5.5 0 01-.5-.5 .5.5 0 01-.5 0h1a.5.5 0 010 1H2.5a.5.5 0 01-.5-.5z" stroke="currentColor" stroke-width="1.5"/>
          <circle cx="10" cy="10" r="4" stroke="currentColor" stroke-width="1.5"/>
        </svg>
        Tema claro
      `;
    } else {
      themeToggle.innerHTML = `
        <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" width="16" height="16">
          <path d="M17 11a8 8 0 01-15 0 8 8 0 0113-6 6 6 0 002 6z" stroke="currentColor" stroke-width="1.5"/>
        </svg>
        Tema oscuro
      `;
    }
  }

  themeToggle.addEventListener('click', function() {
    const isLight = document.body.classList.toggle('light-theme');
    localStorage.setItem(THEME_KEY, isLight ? 'light' : 'dark');
    updateThemeToggleText(isLight ? 'dark' : 'light');
    showToast(`Tema ${isLight ? 'claro' : 'oscuro'} activado`);
  });

  /* ══════════════════════════════════════════════
     SEARCH FUNCTIONALITY
  ══════════════════════════════════════════════ */
  let searchQuery = '';

  searchInput.addEventListener('input', function(e) {
    searchQuery = e.target.value.toLowerCase().trim();
    renderAll();
  });

  function matchesSearch(item) {
    if (!searchQuery) return true;
    
    const searchableText = [
      item.name || '',
      item.email || '',
      item.phone || '',
      item.patient_id || '',
      item.text || '',
      item.message || '',
      item.service || ''
    ].join(' ').toLowerCase();
    
    return searchableText.includes(searchQuery);
  }

  /* ══════════════════════════════════════════════
     AUTH (Server-side)
     Note: Authentication is now handled by the server.
     This page is only served if user is authenticated.
     Logout is handled by navigating to /admin/logout
  ══════════════════════════════════════════════ */

  /* ══════════════════════════════════════════════
     LOAD ALL DATA
  ══════════════════════════════════════════════ */
  async function loadAll() {
    try {
      console.log('[loadAll] Starting...');
      
      // Load pending reviews (local)
      try {
        pendingReviews  = ReviewsDB.getPending();
        console.log('[loadAll] pendingReviews:', pendingReviews?.length || 0);
      } catch (e) {
        console.error('[loadAll] Error getting pending reviews:', e);
        pendingReviews = [];
      }
      
      // Load approved reviews (from JSON)
      try {
        approvedReviews = await ReviewsDB.fetchApproved(true);
        console.log('[loadAll] approvedReviews:', approvedReviews?.length || 0);
      } catch (e) {
        console.error('[loadAll] Error fetching approved reviews:', e);
        approvedReviews = [];
      }
      
      // Load appointments (from API)
      try {
        appointments    = await loadAppointments();
        console.log('[loadAll] appointments:', appointments?.length || 0);
      } catch (e) {
        console.error('[loadAll] Error loading appointments:', e);
        appointments = [];
      }
      
      // Render all data
      try {
        renderAll();
        console.log('[loadAll] renderAll complete');
      } catch (e) {
        console.error('[loadAll] Error rendering:', e);
        showToast('Error renderizando datos: ' + e.message, 'red');
        throw e;
      }
      
      showToast('Datos cargados exitosamente', 'green');
    } catch (error) {
      console.error('[loadAll] FATAL ERROR:', error.message, error);
      showToast('Error cargando datos: ' + error.message, 'red');
    }
  }

  /* API host override UI */
  const apiHostDisplay = document.getElementById('api-host-display');
  const apiEditBtn = document.getElementById('api-edit');

  function getApiBase() {
    return localStorage.getItem(API_HOST_KEY) || API_URL;
  }

  function setApiBase(url) {
    localStorage.setItem(API_HOST_KEY, url);
    if (apiHostDisplay) apiHostDisplay.textContent = 'API: ' + url.replace(/^https?:\/\//, '');
  }

  // Init display
  if (apiHostDisplay) apiHostDisplay.textContent = 'API: ' + getApiBase().replace(/^https?:\/\//, '');

  if (apiEditBtn) {
    apiEditBtn.addEventListener('click', function () {
      const current = getApiBase();
      const val = prompt('API base URL', current);
      if (val && val.trim()) {
        let normalized = val.trim();
        if (!/^https?:\/\//.test(normalized)) normalized = 'http://' + normalized;
        setApiBase(normalized);
        showToast('API apuntando a ' + normalized, 'green');
      }
    });
  }

  function renderAll() {
    renderPending();
    renderApproved();
    renderAppointments();
    updateBadges();
    if (activeTab === 'export') renderExportPreview();
  }

  /* ══════════════════════════════════════════════
     APPOINTMENTS — API + localStorage CRUD
  ══════════════════════════════════════════════ */
  async function loadAppointmentsFromAPI() {
    try {
      const baseUrl = getApiBase();
      console.log('Loading appointments from API:', baseUrl);
      
      const response = await fetch(`${baseUrl}/api/bookings`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      console.log('API Response status:', response.status);

      if (!response.ok) {
        console.error(`API returned ${response.status}`);
        throw new Error(`API returned ${response.status}`);
      }

      const data = await response.json();
      console.log('API data received:', data);
      
      // Handle both response formats
      const bookings = data.bookings || data.rows || [];
      
      if (bookings && Array.isArray(bookings)) {
        // Transform API data to match our local format
        return bookings.map(booking => ({
          id: 'b' + booking.id,
          dbId: booking.id,
          name: booking.name,
          patient_id: booking.patient_id || '',
          phone: booking.phone,
          email: booking.email || '',
          channel: booking.channel || '',
          platform: booking.virtual_platform || '',
          address: booking.address || '',
          service: booking.service || '',
          date: booking.preferred_date || '',
          time: booking.preferred_time || '',
          message: booking.message || '',
          status: booking.status || 'pending',
          submitted: booking.created_at || new Date().toISOString(),
          tracking: {
            ip: booking.ip_address || 'unknown',
            ipCountry: booking.ip_country || 'unknown',
            ipCity: booking.ip_city || 'unknown',
            deviceType: booking.device_type || 'unknown',
            deviceBrand: booking.device_brand || 'unknown',
            deviceModel: booking.device_model || 'unknown',
            os: booking.device_os || 'unknown',
            browser: booking.device_browser || 'unknown',
            screenSize: booking.screen_size || 'unknown',
            language: booking.user_language || 'unknown',
            timezone: booking.user_timezone || 'unknown',
            connection: booking.connection_type || 'unknown',
            capturedAt: booking.created_at
          }
        }));
      }

      console.warn('API response has no bookings/rows array');
      return [];
    } catch (err) {
      console.error('Failed to load appointments from API:', err);
      return null; // Signal fallback to localStorage
    }
  }

  async function loadAppointments() {
    // Try to load from API first
    const apiData = await loadAppointmentsFromAPI();
    
    if (apiData !== null) {
      // Successfully loaded from API
      return apiData;
    }

    // Fallback to localStorage
    try {
      return JSON.parse(localStorage.getItem(APPT_KEY) || '[]');
    } catch {
      return [];
    }
  }

  function saveAppointments(list) {
    localStorage.setItem(APPT_KEY, JSON.stringify(list));
  }

  async function updateAppointmentStatus(id, status) {
    const appointment = appointments.find(a => a.id === id);
    if (!appointment) return;

    // Update locally
    appointments = appointments.map(a => a.id === id ? { ...a, status } : a);
    saveAppointments(appointments);

    // Update in API if available
    if (appointment.dbId) {
      try {
        const response = await fetch(`${getApiBase()}/api/bookings/${appointment.dbId}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ status }),
        });

        if (!response.ok) {
          console.warn('Failed to update appointment on server');
        }
      } catch (err) {
        console.warn('API update failed:', err);
      }
    }
  }

  async function deleteAppointment(id) {
    const appointment = appointments.find(a => a.id === id);
    
    // Delete locally
    appointments = appointments.filter(a => a.id !== id);
    saveAppointments(appointments);

    // Delete from API if available
    if (appointment && appointment.dbId) {
      try {
        const response = await fetch(`${getApiBase()}/api/bookings/${appointment.dbId}`, {
          method: 'DELETE',
        });

        if (!response.ok) {
          console.warn('Failed to delete appointment on server');
        }
      } catch (err) {
        console.warn('API delete failed:', err);
      }
    }
  }

  /* ══════════════════════════════════════════════
     RENDER APPOINTMENTS
  ══════════════════════════════════════════════ */
  function renderAppointments() {
    const list  = document.getElementById('appointments-list');
    const empty = document.getElementById('appointments-empty');
    if (!list) return;
    list.innerHTML = '';

    let filtered = apptFilter === 'all'
      ? appointments
      : appointments.filter(a => (a.status || 'pending') === apptFilter);
    
    filtered = filtered.filter(matchesSearch);

    if (!filtered.length) {
      empty.hidden = false;
      empty.innerHTML = `
        <div class="adm-empty__icon" aria-hidden="true">📅</div>
        <p>${searchQuery ? 'No se encontraron resultados para tu búsqueda.' : 'No hay solicitudes de cita aún.'}</p>
        <small>${searchQuery ? 'Intenta con otros términos de búsqueda.' : 'Cuando un paciente complete el formulario en el sitio, la solicitud aparecerá aquí automáticamente.'}</small>
      `;
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

    // Format tracking info if available
    const tracking = appt.tracking || {};
    const hasTracking = tracking.ip && tracking.ip !== 'unknown';
    const trackingHTML = hasTracking ? `
      <div class="adm-appt-tracking">
        <div class="adm-appt-tracking-row">
          <span class="adm-appt-tracking-icon">🌐</span>
          <span>${esc(tracking.ip)}${tracking.ipCity && tracking.ipCity !== 'unknown' ? ` · ${esc(tracking.ipCity)}, ${esc(tracking.ipCountry)}` : ''}</span>
        </div>
        <div class="adm-appt-tracking-row">
          <span class="adm-appt-tracking-icon">📱</span>
          <span>${esc(tracking.deviceType || 'unknown')}${tracking.deviceBrand && tracking.deviceBrand !== 'Unknown' ? ` · ${esc(tracking.deviceBrand)}` : ''}</span>
        </div>
        <div class="adm-appt-tracking-row">
          <span class="adm-appt-tracking-icon">💻</span>
          <span>${esc(tracking.os || 'unknown')} · ${esc(tracking.browser || 'unknown')}</span>
        </div>
      </div>
    ` : '';

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
          ${trackingHTML}
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
        <button class="adm-btn adm-btn--primary adm-btn--sm" data-action="open-medical" data-id="${esc(appt.id)}"
          title="Abrir historial médico en nueva pestaña" aria-label="Abrir historial médico">
          <svg viewBox="0 0 20 20" fill="none" width="14" height="14" aria-hidden="true">
            <path d="M4 6h12v10a2 2 0 01-2 2H6a2 2 0 01-2-2V6z" stroke="currentColor" stroke-width="1.5"/>
            <path d="M8 6V4a2 2 0 012-2h0a2 2 0 012 2v2M8 10h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          Historial
        </button>
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
        if (appt) openAppointmentInNewTab(appt);
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
    openAppointmentInNewTab(appt);
  }

  function showDetailModal(appt) {
    openDetailModal(appt);
  }

  function openAppointmentInNewTab(appt) {
    // Open medical records page in new tab with booking ID
    // Use relative path since admin pages are served from GitHub Pages
    const bookingId = appt.dbId || appt.id;
    const medicalRecordsUrl = `medical-records.html?booking_id=${bookingId}`;
    window.open(medicalRecordsUrl, '_blank', 'width=1400,height=900');
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
      updateAppointmentStatus(id, 'confirmed').then(() => {
        renderAppointments();
        showToast('✔ Cita confirmada.', 'green');
      });
    }

    if (action === 'cancel-appt') {
      updateAppointmentStatus(id, 'cancelled').then(() => {
        renderAppointments();
        showToast('Cita marcada como cancelada.', 'red');
      });
    }

    if (action === 'delete-appt') {
      animateRemove(btn.closest('.adm-appt-card'), () => {
        deleteAppointment(id).then(() => {
          renderAppointments();
          updateBadges();
          showToast('Solicitud eliminada.');
        });
      });
    }

    if (action === 'calendar' && appt) {
      downloadICS(appt);
    }

    if (action === 'open-medical' && appt) {
      openAppointmentInNewTab(appt);
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

    const filtered = pendingReviews.filter(matchesSearch);

    if (!filtered.length) { 
      empty.hidden = false; 
      empty.innerHTML = `
        <div class="adm-empty__icon" aria-hidden="true">📭</div>
        <p>${searchQuery ? 'No se encontraron resultados para tu búsqueda.' : 'No hay reseñas pendientes por revisar.'}</p>
        <small>${searchQuery ? 'Intenta con otros términos de búsqueda.' : 'Cuando un paciente envíe una reseña desde <strong>review.html</strong>, aparecerá aquí.'}</small>
      `;
      return; 
    }
    empty.hidden = true;

    filtered.forEach((review, idx) => {
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

    const merged = mergeApproved().filter(matchesSearch);
    
    if (!merged.length) { 
      empty.hidden = false; 
      empty.innerHTML = `
        <div class="adm-empty__icon" aria-hidden="true">✨</div>
        <p>${searchQuery ? 'No se encontraron resultados para tu búsqueda.' : 'Aún no hay reseñas aprobadas en reviews.json.'}</p>
        <small>${searchQuery ? 'Intenta con otros términos de búsqueda.' : 'Apruebe reseñas en la pestaña "Pendientes" y exporte el archivo.'}</small>
      `;
      return; 
    }
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
  loadTheme();
  // User is already authenticated (server checked), load data immediately
  loadAll();

})();
