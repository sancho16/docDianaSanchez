/* ══════════════════════════════════════════════
   i18n — Bilingual EN/ES engine
   Default: English. Toggle saves to localStorage.
   ══════════════════════════════════════════════ */
const I18N = (function () {
  'use strict';

  const STORAGE_KEY = 'dds_lang';

  const translations = {
    en: {
      /* ── Meta ── */
      'meta.title':       'Dr. Diana Carolina Sánchez Dávila | Surgeon & General Physician – Costa Rica',
      'meta.description': 'Dr. Diana Carolina Sánchez Dávila – Surgeon and General Physician in Costa Rica. Medical consultations and personalized care.',

      /* ── Navbar ── */
      'nav.home':      'Home',
      'nav.about':     'About',
      'nav.services':  'Services',
      'nav.schedule':  'Hours',
      'nav.contact':   'Book Appointment',
      'nav.logo.aria': 'Go to home',
      'nav.open.aria': 'Open menu',

      /* ── Hero ── */
      'hero.badge':    'Available for consultations · Costa Rica',
      'hero.subtitle': 'Surgeon & General Physician · Comprehensive Care',
      'hero.desc':     'Professional, empathetic and personalized medical care for you and your family.<br/>In-person and virtual consultations in Costa Rica.',
      'hero.cta1':     'Book Appointment',
      'hero.cta2':     'View Services',
      'hero.stat1':    'Years of experience',
      'hero.stat2':    'Patients treated',
      'hero.stat3':    'Commitment',
      'hero.scroll.aria': 'Scroll down',

      /* ── Video scrub ── */
      'video.label': 'Surgery & Medicine',
      'video.title': 'Precision that<br/><span class="text-red">transforms lives</span>',
      'video.desc':  'High-level surgical training at the service of every patient in Costa Rica.',

      /* ── About ── */
      'about.label':   'About Me',
      'about.title':   'Your health, my calling',
      'about.p1':      'I am Dr. Diana Carolina Sánchez Dávila, a surgeon and general physician with over 7 years of experience providing comprehensive care to patients of all ages in Costa Rica. My approach combines scientific rigor with a human and personal touch.',
      'about.p2':      'I graduated from the <a href="https://uia.ac.cr" target="_blank" rel="noopener noreferrer" class="about__link">Universidad Internacional de las Américas (UIA)</a>, one of Costa Rica\'s leading private universities committed to academic excellence, and have dedicated my career to general surgery, preventive medicine, and chronic disease management.',
      'about.cred1':   'Surgeon – Medical College of Costa Rica',
      'about.cred2':   'Graduate – <a href="https://uia.ac.cr" target="_blank" rel="noopener noreferrer" class="about__link">Universidad Internacional de las Américas (UIA)</a>',
      'about.cred3':   'Specialty in General Surgery & Preventive Medicine',
      'about.cred4':   '7+ years of experience in Costa Rica',
      'about.cta':     'Request Consultation',
      'about.badge':   'Surgeon',
      'about.img.alt': 'Dr. Diana Carolina Sánchez Dávila, Surgeon and General Physician',

      /* ── Services ── */
      'services.label': 'Services',
      'services.title': 'How can I help you?',
      'services.desc':  'Complete, personalized medical care for the whole family.',
      's1.title': 'Vitamin C IV',
      's1.desc':  'High-dose intravenous vitamin C therapy to strengthen the immune system, boost energy, and promote cellular recovery.',
      's1.tag':   'IV Therapy',
      's2.title': 'B-Complex IV',
      's2.desc':  'Intravenous B-vitamin complex infusion to improve energy metabolism, neurological function, and reduce oxidative stress.',
      's2.tag':   'IV Therapy',
      's3.title': 'IV Rehydration',
      's3.desc':  'Rapid intravenous rehydration therapy with electrolyte solutions for dehydration, exhaustion, or post-exercise recovery.',
      's3.tag':   'IV Therapy',
      's4.title': 'Symptomatic IV',
      's4.desc':  'Personalized IV therapy for symptomatic management of migraine, nausea, fever, and general discomfort with rapid relief.',
      's4.tag':   'IV Therapy',
      's5.title': 'Facial Harmonization',
      's5.desc':  'Medical aesthetic procedures to naturally enhance and balance facial features. Includes biofiller, botulinum toxin, and more.',
      's5.tag':   'Medical Aesthetics',
      's6.title': 'General Consultation',
      's6.desc':  'Comprehensive health assessment, diagnosis, and personalized treatment plan for adults and children.',
      's6.tag':   'In-person & Virtual',
      's7.title': 'Preventive Medicine',
      's7.desc':  'Periodic health check-ups, vaccinations, screenings, and strategies to maintain your long-term health.',
      's7.tag':   'Preventive',
      's8.title': 'Home Visit',
      's8.desc':  'Medical care at your home for patients with reduced mobility, elderly patients, or special situations.',
      's8.tag':   'Home Care',
      's9.title': 'Virtual Consultation',
      's9.desc':  'Safe telemedicine consultation from the comfort of your home. Digital prescriptions and online follow-up.',
      's9.tag':   'Online',

      /* ── Schedule ── */
      'schedule.label':    'Hours',
      'schedule.title':    'When do we attend?',
      'schedule.desc':     'Appointments required. For emergencies, contact us directly via WhatsApp.',
      'schedule.cta':      'Book via WhatsApp',
      'schedule.aria':     'Office hours',
      'schedule.th.day':   'Day',
      'schedule.th.hours': 'Hours',
      'schedule.th.mode':  'Mode',
      'schedule.r1.day':   'Mon – Fri',
      'schedule.r1.hours': '8:00 am – 5:00 pm',
      'schedule.r1.mode':  'In-person',
      'schedule.r2.day':   'Mon – Fri',
      'schedule.r2.hours': '6:00 pm – 8:00 pm',
      'schedule.r2.mode':  'Virtual',
      'schedule.r3.day':   'Saturday',
      'schedule.r3.hours': '8:00 am – 12:00 pm',
      'schedule.r3.mode':  'In-person',
      'schedule.r4.day':   'Sunday',
      'schedule.r4.hours': 'Closed',

      /* ── Testimonials ── */
      'testimonials.label': 'Testimonials',
      'testimonials.title': 'What my patients say',
      'testimonials.desc':  'Real experiences from those who trust our care.',
      'testimonials.cta':   'Leave a review',
      'testimonials.empty': 'Patient reviews coming soon.',

      /* ── Contact ── */
      'contact.label':       'Contact',
      'contact.title':       'Book your appointment',
      'contact.desc':        'We are ready to assist you. Write or call us and we will gladly coordinate your consultation.',
      'contact.location':    'Location',
      'contact.phone':       'Phone',
      'contact.email':       'Email',
      'contact.whatsapp':    'WhatsApp',
      'form.name':           'Full name',
      'form.name.ph':        'Your name',
      'form.phone':          'Phone',
      'form.email':          'Email address',
      'form.date':           'Preferred date',
      'form.time':           'Preferred time',
      'form.time.ph':        'Select a time',
      'form.service':        'Type of consultation',
      'form.service.ph':     'Select a service',
      'form.message':        'Message',
      'form.message.ph':     'Briefly describe your consultation or appointment reason',
      'form.submit':         'Send request',
      'form.success':        '✔ Your request was sent. We will contact you to confirm your appointment.',
      'form.s1': 'General Consultation',
      'form.s2': 'Preventive Medicine',
      'form.s3': 'Chronic Diseases',
      'form.s4': 'Pediatric Care',
      'form.s5': 'Virtual Consultation',
      'form.s6': 'Home Visit',

      'service.hint': 'Tap to learn more',
      'service.book': 'Book now',
      /* ── New form fields ── */
      'form.id':                  'ID / Document',
      'form.id.ph':               'e.g. 1-1234-5678',
      'form.channel':             'Appointment type',
      'form.channel.virtual':     'Virtual',
      'form.channel.virtual.sub': 'Video call or phone',
      'form.channel.express':     'Express to Home',
      'form.channel.express.sub': 'Doctor visits you',
      'form.channel.error':       'Please select an appointment type.',
      'form.platform':            'Preferred platform',
      'form.platform.ph':         'Select platform',
      'form.platform.phone':      'Phone',
      'form.platform.error':      'Please select a platform.',
      'form.address':             'Home address',
      'form.address.ph':          'Street, building, neighborhood',
      'form.address.error':       'Please enter your address.',
      'form.address.section':     'Your location',
      'form.address.city':        'City / Canton',
      'form.address.province':    'Province',
      'form.gps.title':           'Precise location',
      'form.gps.sub':             'Tap to auto-fill your GPS coordinates',
      'form.gps.btn':             'Detect',
      'form.gps.view':            'View on map',
      'form.section.personal':    'Personal information',
      'form.section.schedule':    'Consultation details',
      'form.required.badge':      'required',
      'form.s.vitc':              'Vitamin C IV',
      'form.s.vitb':              'B-Complex IV',
      'form.s.rehyd':             'IV Rehydration',
      'form.s.symp':              'Symptomatic IV',
      'form.s.facial':            'Facial Harmonization',

      /* ── Footer ── */
      'footer.tagline': 'Surgeon & General Physician · Costa Rica',
      'footer.nav.home':     'Home',
      'footer.nav.about':    'About',
      'footer.nav.services': 'Services',
      'footer.nav.schedule': 'Hours',
      'footer.nav.contact':  'Contact',

      /* ── Back to top ── */
      'backtop.aria': 'Back to top',

      /* ── Language toggle ── */
      'lang.switch': 'ES',
      'lang.current': 'EN',
    },

    es: {
      /* ── Meta ── */
      'meta.title':       'Dra. Diana Carolina Sánchez Dávila | Cirujana y Médico General – Costa Rica',
      'meta.description': 'Dra. Diana Carolina Sánchez Dávila – Médico General en Costa Rica. Consultas médicas y atención personalizada.',

      /* ── Navbar ── */
      'nav.home':      'Inicio',
      'nav.about':     'Sobre mí',
      'nav.services':  'Servicios',
      'nav.schedule':  'Horarios',
      'nav.contact':   'Agendar cita',
      'nav.logo.aria': 'Ir al inicio',
      'nav.open.aria': 'Abrir menú',

      /* ── Hero ── */
      'hero.badge':    'Disponible para consultas · Costa Rica',
      'hero.subtitle': 'Cirujana &amp; Médico General · Atención Integral',
      'hero.desc':     'Atención médica profesional, empática y personalizada para usted y su familia.<br/>Consultas presenciales y virtuales en Costa Rica.',
      'hero.cta1':     'Agendar cita',
      'hero.cta2':     'Ver servicios',
      'hero.stat1':    'Años de experiencia',
      'hero.stat2':    'Pacientes atendidos',
      'hero.stat3':    'Compromiso',
      'hero.scroll.aria': 'Desplazarse hacia abajo',

      /* ── Video scrub ── */
      'video.label': 'Cirugía &amp; Medicina',
      'video.title': 'Precisión que<br/><span class="text-red">transforma vidas</span>',
      'video.desc':  'Formación quirúrgica de alto nivel al servicio de cada paciente en Costa Rica.',

      /* ── About ── */
      'about.label':   'Sobre mí',
      'about.title':   'Su salud, mi vocación',
      'about.p1':      'Soy la Dra. Diana Carolina Sánchez Dávila, cirujana y médico general con más de 7 años de experiencia brindando atención integral a pacientes de todas las edades en Costa Rica. Mi enfoque combina el rigor científico con un trato humano y cercano.',
      'about.p2':      'Me gradué de la <a href="https://uia.ac.cr" target="_blank" rel="noopener noreferrer" class="about__link">Universidad Internacional de las Américas (UIA)</a>, una de las principales universidades privadas de Costa Rica comprometida con la excelencia académica, y he dedicado mi carrera a la cirugía general, medicina preventiva y el manejo de enfermedades crónicas.',
      'about.cred1':   'Cirujana General – Colegio de Médicos y Cirujanos de CR',
      'about.cred2':   'Graduada – <a href="https://uia.ac.cr" target="_blank" rel="noopener noreferrer" class="about__link">Universidad Internacional de las Américas (UIA)</a>',
      'about.cred3':   'Especialidad en Cirugía General y Medicina Preventiva',
      'about.cred4':   '7+ años de experiencia en Costa Rica',
      'about.cta':     'Solicitar consulta',
      'about.badge':   'Cirujana',
      'about.img.alt': 'Dra. Diana Carolina Sánchez Dávila, Cirujana y Médico General',

      /* ── Services ── */
      'services.label': 'Servicios',
      'services.title': '¿En qué le puedo ayudar?',
      'services.desc':  'Atención médica completa y personalizada para toda la familia.',
      'service.hint': 'Toque para más info',
      'service.book': 'Agendar ahora',
      's1.title': 'Vitamina C IV',
      's1.desc':  'Terapia intravenosa de vitamina C de alta dosis para fortalecer el sistema inmune, aumentar energía y promover la recuperación celular.',
      's1.tag':   'Terapia IV',
      's2.title': 'Complejo B IV',
      's2.desc':  'Infusión intravenosa de complejo vitamínico B para mejorar el metabolismo energético, función neurológica y reducir el estrés oxidativo.',
      's2.tag':   'Terapia IV',
      's3.title': 'Rehidratación IV',
      's3.desc':  'Terapia de rehidratación intravenosa rápida con soluciones electrolíticas para deshidratación, agotamiento o recuperación post-ejercicio.',
      's3.tag':   'Terapia IV',
      's4.title': 'IV Sintomática',
      's4.desc':  'Terapia intravenosa personalizada para el manejo sintomático de migraña, náuseas, fiebre y malestar general con alivio rápido.',
      's4.tag':   'Terapia IV',
      's5.title': 'Armonización Facial',
      's5.desc':  'Procedimientos estéticos médicos para realzar y equilibrar los rasgos faciales de forma natural. Incluye biorelleno, toxina botulínica y más.',
      's5.tag':   'Estética Médica',
      's6.title': 'Consulta General',
      's6.desc':  'Evaluación integral del estado de salud, diagnóstico y plan de tratamiento personalizado para adultos y niños.',
      's6.tag':   'Presencial &amp; Virtual',
      's7.title': 'Medicina Preventiva',
      's7.desc':  'Chequeos médicos periódicos, vacunación, tamizajes y estrategias para mantener su salud a largo plazo.',
      's7.tag':   'Preventivo',
      's8.title': 'Visita Domiciliaria',
      's8.desc':  'Atención médica en su hogar para pacientes con movilidad reducida, adultos mayores o situaciones especiales.',
      's8.tag':   'A domicilio',
      's9.title': 'Consulta Virtual',
      's9.desc':  'Teleconsulta médica segura desde la comodidad de su hogar. Recetas digitales y seguimiento en línea.',
      's9.tag':   'En línea',

      /* ── Schedule ── */
      'schedule.label':    'Horarios',
      'schedule.title':    '¿Cuándo atendemos?',
      'schedule.desc':     'Consultas con cita previa. Para emergencias, contáctenos directamente por WhatsApp.',
      'schedule.cta':      'Agendar por WhatsApp',
      'schedule.aria':     'Horario de atención',
      'schedule.th.day':   'Día',
      'schedule.th.hours': 'Horario',
      'schedule.th.mode':  'Modalidad',
      'schedule.r1.day':   'Lunes – Viernes',
      'schedule.r1.hours': '8:00 am – 5:00 pm',
      'schedule.r1.mode':  'Presencial',
      'schedule.r2.day':   'Lunes – Viernes',
      'schedule.r2.hours': '6:00 pm – 8:00 pm',
      'schedule.r2.mode':  'Virtual',
      'schedule.r3.day':   'Sábado',
      'schedule.r3.hours': '8:00 am – 12:00 pm',
      'schedule.r3.mode':  'Presencial',
      'schedule.r4.day':   'Domingo',
      'schedule.r4.hours': 'Cerrado',

      /* ── Testimonials ── */
      'testimonials.label': 'Testimonios',
      'testimonials.title': 'Lo que dicen mis pacientes',
      'testimonials.desc':  'Experiencias reales de quienes confían en nuestra atención.',
      'testimonials.cta':   'Dejar mi reseña',
      'testimonials.empty': 'Próximamente reseñas de pacientes.',

      /* ── Contact ── */
      'contact.label':    'Contacto',
      'contact.title':    'Agendar su cita',
      'contact.desc':     'Estamos listos para atenderle. Escríbanos o llámenos y con gusto coordinaremos su consulta.',
      'contact.location': 'Ubicación',
      'contact.phone':    'Teléfono',
      'contact.email':    'Correo',
      'contact.whatsapp': 'WhatsApp',
      'form.name':        'Nombre completo',
      'form.name.ph':     'Su nombre',
      'form.phone':       'Teléfono',
      'form.email':       'Correo electrónico',
      'form.date':        'Fecha preferida',
      'form.time':        'Hora preferida',
      'form.time.ph':     'Seleccione una hora',
      'form.service':     'Tipo de consulta',
      'form.service.ph':  'Seleccione un servicio',
      'form.message':     'Mensaje',
      'form.message.ph':  'Describa brevemente su consulta o motivo de cita',
      'form.submit':      'Enviar solicitud',
      'form.success':     '✔ Su solicitud fue enviada. Le contactaremos para confirmar su cita.',
      'form.s1': 'Consulta General',
      'form.s2': 'Medicina Preventiva',
      'form.s3': 'Enfermedades Crónicas',
      'form.s4': 'Atención Pediátrica',
      'form.s5': 'Consulta Virtual',
      'form.s5': 'Consulta Virtual',
      'form.s6': 'Visita Domiciliaria',

      /* ── Nuevos campos del formulario ── */
      'form.id':                  'Cédula / Identificación',
      'form.id.ph':               'Ej. 1-1234-5678',
      'form.channel':             'Tipo de cita',
      'form.channel.virtual':     'Virtual',
      'form.channel.virtual.sub': 'Videollamada o teléfono',
      'form.channel.express':     'Express a domicilio',
      'form.channel.express.sub': 'La doctora va a su hogar',
      'form.channel.error':       'Por favor seleccione el tipo de cita.',
      'form.platform':            'Plataforma preferida',
      'form.platform.ph':         'Seleccione plataforma',
      'form.platform.phone':      'Llamada',
      'form.platform.error':      'Por favor seleccione una plataforma.',
      'form.address':             'Dirección de domicilio',
      'form.address.ph':          'Calle, edificio, barrio',
      'form.address.error':       'Por favor ingrese su dirección.',
      'form.address.section':     'Su ubicación',
      'form.address.city':        'Ciudad / Cantón',
      'form.address.province':    'Provincia',
      'form.gps.title':           'Ubicación precisa',
      'form.gps.sub':             'Toque para capturar sus coordenadas GPS',
      'form.gps.btn':             'Detectar',
      'form.gps.view':            'Ver en mapa',
      'form.section.personal':    'Información personal',
      'form.section.schedule':    'Detalles de la consulta',
      'form.required.badge':      'requerido',
      'form.s.vitc':              'Vitamina C IV',
      'form.s.vitb':              'Complejo B IV',
      'form.s.rehyd':             'Rehidratación IV',
      'form.s.symp':              'IV Sintomática',
      'form.s.facial':            'Armonización Facial',

      /* ── Footer ── */
      'footer.tagline':      'Médico General · Costa Rica',
      'footer.nav.home':     'Inicio',
      'footer.nav.about':    'Sobre mí',
      'footer.nav.services': 'Servicios',
      'footer.nav.schedule': 'Horarios',
      'footer.nav.contact':  'Contacto',

      /* ── Back to top ── */
      'backtop.aria': 'Volver arriba',

      /* ── Language toggle ── */
      'lang.switch':  'ES',
      'lang.current': 'EN',
    }
  };

  /* ── Current language ── */
  let currentLang = localStorage.getItem(STORAGE_KEY) || 'en';

  function t(key) {
    return (translations[currentLang] && translations[currentLang][key]) ||
           (translations['en'][key]) || key;
  }

  function applyLanguage() {
    const lang = currentLang;
    document.documentElement.lang = lang;
    document.title = t('meta.title');
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) metaDesc.setAttribute('content', t('meta.description'));

    /* Helper to set innerHTML safely for keys with HTML (links, spans) */
    function set(selector, key, attr) {
      const els = document.querySelectorAll('[data-i18n="' + key + '"]');
      els.forEach(el => {
        if (attr) { el.setAttribute(attr, t(key)); }
        else { el.innerHTML = t(key); }
      });
    }

    /* Apply all keyed elements */
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key  = el.dataset.i18n;
      const attr = el.dataset.i18nAttr;
      if (attr) { el.setAttribute(attr, t(key)); }
      else { el.innerHTML = t(key); }
    });

    /* Apply placeholder attributes */
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
      el.setAttribute('placeholder', t(el.dataset.i18nPh));
    });

    /* Language toggle button label */
    const btn = document.getElementById('lang-toggle');
    if (btn) {
      btn.textContent  = lang === 'en' ? 'ES' : 'EN';
      btn.setAttribute('aria-label', lang === 'en' ? 'Cambiar a Español' : 'Switch to English');
      btn.setAttribute('lang', lang === 'en' ? 'es' : 'en');
    }
  }

  function toggle() {
    currentLang = currentLang === 'en' ? 'es' : 'en';
    localStorage.setItem(STORAGE_KEY, currentLang);
    /* Brief fade-out → swap text → fade-in */
    document.body.classList.add('lang-switching');
    setTimeout(() => {
      applyLanguage();
      document.body.classList.remove('lang-switching');
    }, 140);
    document.dispatchEvent(new CustomEvent('langchange', { detail: { lang: currentLang } }));
  }

  function getLang() { return currentLang; }

  /* Public API */
  return { t, applyLanguage, toggle, getLang };
})();
