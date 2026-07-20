const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const finePointer = window.matchMedia('(pointer: fine)').matches;
let heroChars = [];
let gsapReady = false;

const i18n = {
  en: {
    'kicker': 'Portfolio // 2025',
    'kicker-about': 'About / CV',
    'greeting': 'Prague-based cinematographer, photographer and film student.',
    'greeting-short': 'Prague-based cinematographer, photographer and film student.',
    'nav-about': 'About',
    'back-portfolio': 'Back to portfolio',
    'filter-all': 'All',
    'filter-photo': 'Photo',
    'filter-video': 'Video',
    'film-photo': 'photography',
    'film-video': 'video',
    'film-hint': 'What do the perforations mean?',
    'footer-role': 'Cinematography & Photography',
    'footer-contact': 'Contact',
    'about-kicker': 'About / CV',
    'about-intro': 'Prague-based cinematographer, photographer and film student. I specialize in cinematography and captivating visual storytelling.',
    'profile-role': 'Cinematographer & Photographer',
    'edu-title': 'Education',
    'work-title': 'Filmography & Experience',
    'collabs-title': 'Collaborations',
    'skills-title': 'Skills',
    'gear-title': 'Equipment',
    'lang-title': 'Languages',
    'period-1': '2022 — 2026',
    'period-2': '2026 — present',
    'school-1': 'SPŠST PANSKÁ | Film and Television Production',
    'school-2': 'Silesian University in Opava | Multimedia and Popularization',
    'role-student': 'Student',
    'role-dir': 'Director / Camera / Edit',
    'role-cam': 'Camera / Edit',
    'role-cam-post': 'Camera / Post-production',
    'role-dir-cam': 'Director / Camera / Edit',
    'project-loading': 'Loading project...',
    'project-not-found': 'Project not found.',
    'project-missing': 'Missing project ID.',
    'project-failed': 'Failed to load project.',
    'back': 'Back to portfolio',
  }
};

function detectLang() {
  const lang = (navigator.language || navigator.languages?.[0] || '').toLowerCase();
  return lang.startsWith('cs') ? 'cs' : 'en';
}

function translatePage() {
  const lang = detectLang();
  if (lang === 'cs') return;
  const dict = i18n[lang] || i18n.en;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (dict[key]) {
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = dict[key];
      } else if (el.dataset.i18nHtml) {
        el.innerHTML = dict[key];
      } else {
        el.textContent = dict[key];
      }
    }
  });
  document.querySelectorAll('[data-i18n-aria]').forEach(el => {
    const key = el.dataset.i18nAria;
    if (dict[key]) el.setAttribute('aria-label', dict[key]);
  });
  document.documentElement.lang = lang;
}

translatePage();

function ensureGsap() {
  if (gsapReady) return typeof gsap !== 'undefined';
  if (typeof gsap === 'undefined') return false;
  if (typeof Flip !== 'undefined') gsap.registerPlugin(Flip);
  if (typeof ScrollTrigger !== 'undefined') gsap.registerPlugin(ScrollTrigger);
  gsapReady = true;
  return true;
}

function splitChars(root) {
  const chars = [];
  const pushChars = (text, parent) => {
    for (const ch of text) {
      const c = document.createElement('span');
      c.className = 'h1-char';
      c.textContent = ch === ' ' ? '\u00A0' : ch;
      c.setAttribute('aria-hidden', 'true');
      parent.appendChild(c);
      chars.push(c);
    }
  };
  Array.from(root.childNodes).forEach(node => {
    if (node.nodeType === Node.TEXT_NODE) {
      if (!node.textContent.trim()) return;
      const wrap = document.createElement('span');
      wrap.className = 'h1-word';
      root.insertBefore(wrap, node);
      pushChars(node.textContent, wrap);
      root.removeChild(node);
    } else if (node.nodeType === Node.ELEMENT_NODE && node.tagName === 'BR') {
      root.removeChild(node);
    } else if (node.nodeType === Node.ELEMENT_NODE && node.tagName !== 'BR') {
      const text = node.textContent;
      node.setAttribute('aria-label', text);
      node.textContent = '';
      pushChars(text, node);
    }
  });
  return chars;
}

function prepareHero() {
  if (prefersReduced) return;
  const h1 = document.querySelector('h1');
  if (!h1) return;
  heroChars = splitChars(h1);
  if (heroChars.length) document.documentElement.classList.add('lib-anim');
}

function initHeroAnim() {
  if (!heroChars.length) return;
  if (!window.Motion) { document.documentElement.classList.remove('lib-anim'); return; }
  Motion.animate(
    heroChars,
    { opacity: [0, 1], y: ['0.6em', '0em'], rotate: [8, 0] },
    { delay: Motion.stagger(0.03, { start: 0.12 }), duration: 0.75, easing: [0.22, 1, 0.36, 1] }
  );
}

function recalcPerforations() {
  const tiles = Array.from(document.querySelectorAll('.tile'));
  tiles.forEach(a => {
    const type = a.dataset.perfType;
    if (!type) return;
    const frameW = parseFloat(a.dataset.perfFrameWidth);
    const frameH = parseFloat(a.dataset.perfFrameHeight);
    const holeW = parseFloat(a.dataset.perfHoleWidth);
    const holeH = parseFloat(a.dataset.perfHoleHeight);
    const count = parseInt(a.dataset.perfCount, 10) || 2;
    const rect = a.getBoundingClientRect();
    const isVideo = type === 'video';
    const pitchPx = isVideo ? (4.75 / frameH) * rect.height : (4.75 / frameW) * rect.width;
    const dotWidthPx = (holeW / frameW) * rect.width;
    const dotHeightPx = (holeH / frameH) * rect.height;
    const gapForH = Math.max(1, pitchPx - dotWidthPx);
    const gapForV = Math.max(1, pitchPx - dotHeightPx);
    a.style.setProperty('--perf-dot-width', Math.round(dotWidthPx) + 'px');
    a.style.setProperty('--perf-dot-height', Math.round(dotHeightPx) + 'px');

    const perfHTop = a.querySelector('.film-perf-h.top');
    const perfHBottom = a.querySelector('.film-perf-h.bottom');
    const perfVLeft = a.querySelector('.film-perf-v.left');
    const perfVRight = a.querySelector('.film-perf-v.right');

    if (perfHTop || perfHBottom) {
      const containerW = (count * dotWidthPx) + ((count - 1) * gapForH);
      [perfHTop, perfHBottom].forEach(el => {
        if (!el) return;
        el.style.width = Math.round(containerW) + 'px';
        el.style.left = '50%';
        el.style.transform = 'translateX(-50%)';
        el.style.justifyContent = 'flex-start';
        el.style.gap = Math.round(gapForH) + 'px';
        el.querySelectorAll('.perf-dot').forEach(d => {
          d.style.width = Math.round(dotWidthPx) + 'px';
          d.style.height = Math.round(dotHeightPx) + 'px';
          d.style.borderRadius = Math.max(2, Math.round(Math.min(dotWidthPx, dotHeightPx) / 4)) + 'px';
        });
      });
    }

    if (perfVLeft || perfVRight) {
      const containerH = (count * dotHeightPx) + ((count - 1) * gapForV);
      [perfVLeft, perfVRight].forEach(el => {
        if (!el) return;
        el.style.height = Math.round(containerH) + 'px';
        el.style.top = '50%';
        el.style.transform = 'translateY(-50%)';
        el.style.justifyContent = 'flex-start';
        el.style.gap = Math.round(gapForV) + 'px';
        el.querySelectorAll('.perf-dot').forEach(d => {
          d.style.width = Math.round(dotWidthPx) + 'px';
          d.style.height = Math.round(dotHeightPx) + 'px';
          d.style.borderRadius = Math.max(2, Math.round(Math.min(dotWidthPx, dotHeightPx) / 4)) + 'px';
        });
      });
    }
  });
}

function imgErrorFallback(img) {
  const orig = img.getAttribute('data-orig-src') || img.src;
  if (!img.getAttribute('data-orig-src')) img.setAttribute('data-orig-src', orig);
  const n = parseInt(img.getAttribute('data-attempt') || '0');
  img.setAttribute('data-attempt', String(n + 1));
  const variants = [orig.toLowerCase(), orig.toLowerCase().replace(/ /g, '-'), orig.toLowerCase().replace(/%20/g, '-')];
  if (n < variants.length && variants[n] !== img.src) {
    img.src = variants[n];
  } else {
    img.removeAttribute('onerror');
  }
}
