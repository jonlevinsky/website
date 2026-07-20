const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const finePointer = window.matchMedia('(pointer: fine)').matches;
let heroChars = [];
let gsapReady = false;

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
