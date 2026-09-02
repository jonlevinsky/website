const supabaseUrl = 'https://jmxpqcsywnlbmfrylnhw.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpteHBxY3N5d25sYm1mcnlsbmh3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxODkwNjcsImV4cCI6MjEwMzc2NTA2N30.pFgifOtNk2tLGJLEYeughUByfT6um85kfO2r7OopEtA';
let supabaseClient;
if (typeof supabase !== 'undefined') {
  supabaseClient = supabase.createClient(supabaseUrl, supabaseKey);
}

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

let perfObserver;
function recalcSingleTile(a) {
  const type = a.dataset.perfType;
  if (!type) return;
  const frameW = parseFloat(a.dataset.perfFrameWidth);
  const frameH = parseFloat(a.dataset.perfFrameHeight);
  const holeW = parseFloat(a.dataset.perfHoleWidth);
  const holeH = parseFloat(a.dataset.perfHoleHeight);
  const count = parseInt(a.dataset.perfCount, 10) || 2;
  const rect = a.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return;
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
}

function recalcPerforations() {
  const tiles = Array.from(document.querySelectorAll('.tile'));
  if (window.ResizeObserver) {
    if (!perfObserver) {
      perfObserver = new ResizeObserver(entries => {
        entries.forEach(entry => {
          recalcSingleTile(entry.target);
        });
      });
    }
    tiles.forEach(tile => {
      perfObserver.observe(tile);
    });
  } else {
    tiles.forEach(recalcSingleTile);
  }
}

function updateAriaAttributes() {
  const panel = document.getElementById('brandPanel');
  const toggle = document.getElementById('menuToggle');
  if (!panel) return;
  const isMobile = window.matchMedia('(max-width: 880px)').matches;
  if (!isMobile) {
    panel.setAttribute('aria-hidden', 'false');
    if (toggle) toggle.setAttribute('aria-expanded', 'true');
  } else {
    const isOpen = panel.classList.contains('open');
    panel.setAttribute('aria-hidden', String(!isOpen));
    if (toggle) {
      toggle.setAttribute('aria-expanded', String(isOpen));
      toggle.classList.toggle('active', isOpen);
    }
  }
}

function initGlobalNavigation() {
  const menuToggle = document.getElementById('menuToggle');
  const brandPanel = document.getElementById('brandPanel');
  if (menuToggle && brandPanel) {
    menuToggle.addEventListener('click', function() {
      const isOpen = brandPanel.classList.toggle('open');
      this.classList.toggle('active', isOpen);
      this.setAttribute('aria-expanded', String(isOpen));
      brandPanel.setAttribute('aria-hidden', String(!isOpen));
    });
  }
  updateAriaAttributes();
  window.addEventListener('resize', updateAriaAttributes);
}

function initCuteAssistant() {
  const lang = detectLang();
  const dicts = {
    cs: {
      name: "Asistent",
      status: "online",
      welcome: "Dobrý den. Jak vám mohu pomoci?",
      askMoreGeneral: "Mohu vám pomoci s něčím dalším?",
      askMoreProject: "Potřebujete další informace k projektu?",
      optAbout: "O autorovi",
      optContact: "Kontakt",
      optGear: "Technika autora",
      optProcess: "Pracovní proces",
      optProjectInfo: "O projektu",
      optProjectGear: "Použitá technika",
      optProjectTechniques: "Speciální techniky",
      optBack: "← Hlavní menu",
      respAbout: "Jan Levínský je kameraman a fotograf zaměřený na dokumentární a atmosférickou kinematografii. Studuje filmovou tvorbu a věnuje se jak komerčním, tak autorskim projektům.",
      respAboutFollow: "Jeho práce se vyznačuje pečlivou kompozicí, přirozeným světlem a detailním zachycením atmosféry prostředí.",
      respContact: "Pro spolupráci nebo dotazy kontaktujte Jana na <a href='mailto:levinskyj.cine@gmail.com' style='color: var(--accent);'>levinskyj.cine@gmail.com</a>",
      respContactFollow: "Můžete se také podívat na kompletní kontaktní informace v sekci <a href='./contact.html' style='color: var(--accent);'>Kontakt</a>.",
      respGear: "Jan standardně pracuje s těmito kamerami:",
      respGearList: "<div style='margin: 12px 0; line-height: 1.8;'><strong>Sony FX3</strong> – hlavní kamera pro video projekty<br><strong>Blackmagic Pocket Cinema 6K Pro</strong> – dokumentární a filmové projekty<br><strong>Analogový 35mm film</strong> – fotografie</div>",
      respGearLenses: "Pro objektivy kombinuje vintage sovětské sklo (Helios-44M) s moderními zoom objektivy (Tamron 24-105mm).",
      respProcess: "Pracovní proces Jana zahrnuje několik fází:",
      respProcessList: "<div style='margin: 12px 0; line-height: 1.8;'><strong>1. Příprava</strong> – Location scouting, vizuální reference, technický plán<br><strong>2. Natáčení</strong> – Práce s přirozeným světlem, důraz na atmosféru<br><strong>3. Postprodukce</strong> – Color grading v DaVinci Resolve, zvuková úprava</div>",
      respProcessFollow: "Každý projekt přistupuje individuálně podle specifických požadavků a vizuální koncepce."
    },
    en: {
      name: "Assistant",
      status: "online",
      welcome: "Hello. How can I help you?",
      askMoreGeneral: "Can I help you with anything else?",
      askMoreProject: "Do you need more information about the project?",
      optAbout: "About the author",
      optContact: "Contact",
      optGear: "Author's equipment",
      optProcess: "Workflow",
      optProjectInfo: "About the project",
      optProjectGear: "Equipment used",
      optProjectTechniques: "Special techniques",
      optBack: "← Main menu",
      respAbout: "Jan Levínský is a cinematographer and photographer focused on documentary and atmospheric cinematography. He studies filmmaking and works on both commercial and personal projects.",
      respAboutFollow: "His work is characterized by careful composition, natural light, and detailed capture of environmental atmosphere.",
      respContact: "For collaboration or inquiries, contact Jan at <a href='mailto:levinskyj.cine@gmail.com' style='color: var(--accent);'>levinskyj.cine@gmail.com</a>",
      respContactFollow: "You can also check complete contact information in the <a href='./contact.html' style='color: var(--accent);'>Contact</a> section.",
      respGear: "Jan typically works with these cameras:",
      respGearList: "<div style='margin: 12px 0; line-height: 1.8;'><strong>Sony FX3</strong> – main camera for video projects<br><strong>Blackmagic Pocket Cinema 6K Pro</strong> – documentary and film projects<br><strong>Analog 35mm film</strong> – photography</div>",
      respGearLenses: "For lenses, he combines vintage Soviet glass (Helios-44M) with modern zoom lenses (Tamron 24-105mm).",
      respProcess: "Jan's workflow includes several phases:",
      respProcessList: "<div style='margin: 12px 0; line-height: 1.8;'><strong>1. Preparation</strong> – Location scouting, visual references, technical planning<br><strong>2. Production</strong> – Working with natural light, focus on atmosphere<br><strong>3. Post-production</strong> – Color grading in DaVinci Resolve, audio editing</div>",
      respProcessFollow: "Each project is approached individually according to specific requirements and visual concept."
    }
  };

  const dict = dicts[lang] || dicts.cs;

  const container = document.createElement('div');
  container.className = 'assistant-container';
  container.innerHTML = `
    <div class="assistant-chat" id="assistantChat">
      <div class="assistant-header">
        <div class="assistant-header-title">
          <div class="assistant-status-dot"></div>
          <span>${dict.name}</span>
          <span class="assistant-status-text">(${dict.status})</span>
        </div>
        <button class="assistant-close" id="assistantClose" aria-label="Close">&times;</button>
      </div>
      <div class="assistant-messages" id="assistantMsgs">
        <div class="assistant-msg bot">${dict.welcome}</div>
      </div>
      <div class="assistant-options" id="assistantOpts"></div>
    </div>
    <div class="assistant-btn" id="assistantBtn" aria-label="Open assistant">
      <div class="orb-wrapper" id="orbWrapper">
        <div class="orb-rings">
          <div class="orb-ring orb-ring-1"></div>
          <div class="orb-ring orb-ring-2"></div>
          <div class="orb-ring orb-ring-3"></div>
        </div>
        <div class="orb-core"></div>
      </div>
      <div class="assistant-badge" id="assistantBadge"></div>
    </div>
  `;
  document.body.appendChild(container);

  const btn = document.getElementById('assistantBtn');
  const lensBody = document.getElementById('lensBody');
  const chat = document.getElementById('assistantChat');
  const msgs = document.getElementById('assistantMsgs');
  const closeBtn = document.getElementById('assistantClose');
  const badge = document.getElementById('assistantBadge');
  const optsContainer = document.getElementById('assistantOpts');
  
  let currentProjectData = null;
  let conversationState = 'main';
  
  // Detect if we're on project page and load project data
  const urlParams = new URLSearchParams(window.location.search);
  const projectId = urlParams.get('id');
  
  if (projectId) {
    fetch('./projects.json')
      .then(res => res.json())
      .then(projects => {
        currentProjectData = projects.find(p => p.id == projectId);
      })
      .catch(() => {});
  }

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = chat.classList.toggle('open');
    if (isOpen && badge) {
      badge.style.display = 'none';
    }
  });

  closeBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    chat.classList.remove('open');
  });

  document.addEventListener('click', (e) => {
    if (!container.contains(e.target)) {
      chat.classList.remove('open');
    }
  });
  
  chat.addEventListener('click', (e) => {
    e.stopPropagation();
  });
  
  // Initialize options on first load
  renderMainOptions();
  
  // Project hover reactions
  const orbWrapper = document.getElementById('orbWrapper');
  const orbCore = orbWrapper?.querySelector('.orb-core');
  const orbRings = orbWrapper?.querySelector('.orb-rings');
  
  document.addEventListener('mouseenter', (e) => {
    const tile = e.target && typeof e.target.closest === 'function' ? e.target.closest('.tile') : null;
    if (tile && orbWrapper) {
      orbWrapper.classList.add('orb-excited');
      if (orbCore) {
        orbCore.style.transform = 'scale(1.3)';
        orbCore.style.boxShadow = '0 0 24px rgba(44, 62, 80, 0.8), inset 0 0 10px rgba(255, 255, 255, 0.3)';
      }
      if (orbRings) {
        orbRings.style.animationPlayState = 'running';
        orbRings.style.animationDuration = '1s';
      }
    }
  }, true);
  
  document.addEventListener('mouseleave', (e) => {
    const tile = e.target && typeof e.target.closest === 'function' ? e.target.closest('.tile') : null;
    if (tile && orbWrapper) {
      orbWrapper.classList.remove('orb-excited');
      if (orbCore) {
        orbCore.style.transform = '';
        orbCore.style.boxShadow = '';
      }
      if (orbRings) {
        orbRings.style.animationDuration = '3s';
      }
    }
  }, true);

  optsContainer.addEventListener('click', (e) => {
    const optBtn = e.target.closest('.assistant-opt-btn');
    if (!optBtn) return;
    
    const action = optBtn.dataset.action;
    const userText = optBtn.textContent;
    
    addMessage(userText, 'user');
    optsContainer.innerHTML = '';
    
    setTimeout(() => {
      let botHtml = '';
      let followUpOptions = [];
      
      if (action === 'back') {
        conversationState = 'main';
        renderMainOptions();
        return;
      }
      
      if (action === 'projectInfo' && currentProjectData) {
        const mediaCount = currentProjectData.media ? currentProjectData.media.length : 0;
        const videoCount = currentProjectData.media ? currentProjectData.media.filter(m => m.type === 'video').length : 0;
        const photoCount = currentProjectData.media ? currentProjectData.media.filter(m => m.type === 'photo').length : 0;
        
        botHtml = `<strong>${currentProjectData.title}</strong><br><span style="color: var(--muted); font-size: 13px;">${currentProjectData.year} • ${currentProjectData.type === 'video' ? 'Video projekt' : 'Foto projekt'}</span><br><br>`;
        
        if (currentProjectData.bio) {
          botHtml += `${currentProjectData.bio}<br><br>`;
        }
        
        if (mediaCount > 0) {
          botHtml += `<span style="color: var(--muted); font-size: 13px;">Obsahuje ${videoCount} videí a ${photoCount} fotografií</span>`;
        }
        
        followUpOptions = [
          { action: 'projectGear', text: dict.optProjectGear },
          { action: 'projectTechniques', text: dict.optProjectTechniques },
          { action: 'back', text: dict.optBack }
        ];
      } else if (action === 'projectGear' && currentProjectData) {
        const gear = currentProjectData.gear;
        let gearList = '<div style="line-height: 1.8;">';
        
        if (gear) {
          if (gear.camera && gear.camera.length) {
            gearList += `<div style="margin-bottom: 8px;"><strong>Kamera</strong><br><span style="color: var(--muted);">${gear.camera.join(', ')}</span></div>`;
          }
          if (gear.lenses && gear.lenses.length) {
            gearList += `<div style="margin-bottom: 8px;"><strong>Objektivy</strong><br><span style="color: var(--muted);">${gear.lenses.join(', ')}</span></div>`;
          }
          if (gear.lighting && gear.lighting.length) {
            gearList += `<div style="margin-bottom: 8px;"><strong>Světla</strong><br><span style="color: var(--muted);">${gear.lighting.join(', ')}</span></div>`;
          }
          if (gear.audio && gear.audio.length) {
            gearList += `<div style="margin-bottom: 8px;"><strong>Zvuk</strong><br><span style="color: var(--muted);">${gear.audio.join(', ')}</span></div>`;
          }
          if (gear.software && gear.software.length) {
            gearList += `<div style="margin-bottom: 8px;"><strong>Software</strong><br><span style="color: var(--muted);">${gear.software.join(', ')}</span></div>`;
          }
          if (gear.filter && gear.filter.length) {
            gearList += `<div style="margin-bottom: 8px;"><strong>Filtry</strong><br><span style="color: var(--muted);">${gear.filter.join(', ')}</span></div>`;
          }
          if (gear.drone && gear.drone.length) {
            gearList += `<div style="margin-bottom: 8px;"><strong>Dron</strong><br><span style="color: var(--muted);">${gear.drone.join(', ')}</span></div>`;
          }
          if (gear['gimbal/stabilization'] && gear['gimbal/stabilization'].length) {
            gearList += `<div style="margin-bottom: 8px;"><strong>Stabilizace</strong><br><span style="color: var(--muted);">${gear['gimbal/stabilization'].join(', ')}</span></div>`;
          }
        }
        
        gearList += '</div>';
        botHtml = gearList.includes('<div style="margin-bottom') ? gearList : 'Pro tento projekt není dostupný detailní seznam techniky.';
        
        followUpOptions = [
          { action: 'projectInfo', text: dict.optProjectInfo },
          { action: 'projectTechniques', text: dict.optProjectTechniques },
          { action: 'back', text: dict.optBack }
        ];
      } else if (action === 'projectTechniques' && currentProjectData) {
        const techniques = currentProjectData.techniques;
        
        if (techniques && techniques.length > 0) {
          botHtml = `<div style="line-height: 1.8;"><strong>Použité techniky</strong><br><span style="color: var(--muted);">${techniques.join(', ')}</span></div>`;
        } else {
          botHtml = 'Pro tento projekt nejsou specifikované speciální techniky nebo postupy.';
        }
        
        followUpOptions = [
          { action: 'projectInfo', text: dict.optProjectInfo },
          { action: 'projectGear', text: dict.optProjectGear },
          { action: 'back', text: dict.optBack }
        ];
      } else if (action === 'gear') {
        addMessage(dict.respGear, 'bot');
        setTimeout(() => {
          addMessage(dict.respGearList, 'bot');
          setTimeout(() => {
            addMessage(dict.respGearLenses, 'bot');
            setTimeout(() => {
              addMessage(dict.askMoreGeneral, 'bot');
              renderOptions([
                { action: 'process', text: dict.optProcess },
                { action: 'about', text: dict.optAbout },
                { action: 'back', text: dict.optBack }
              ]);
            }, 500);
          }, 600);
        }, 600);
        return;
      } else if (action === 'about') {
        addMessage(dict.respAbout, 'bot');
        setTimeout(() => {
          addMessage(dict.respAboutFollow, 'bot');
          setTimeout(() => {
            addMessage(dict.askMoreGeneral, 'bot');
            renderOptions([
              { action: 'gear', text: dict.optGear },
              { action: 'process', text: dict.optProcess },
              { action: 'contact', text: dict.optContact },
              { action: 'back', text: dict.optBack }
            ]);
          }, 500);
        }, 600);
        return;
      } else if (action === 'contact') {
        addMessage(dict.respContact, 'bot');
        setTimeout(() => {
          addMessage(dict.respContactFollow, 'bot');
          setTimeout(() => {
            addMessage(dict.askMoreGeneral, 'bot');
            renderOptions([
              { action: 'about', text: dict.optAbout },
              { action: 'gear', text: dict.optGear },
              { action: 'back', text: dict.optBack }
            ]);
          }, 500);
        }, 600);
        return;
      } else if (action === 'process') {
        addMessage(dict.respProcess, 'bot');
        setTimeout(() => {
          addMessage(dict.respProcessList, 'bot');
          setTimeout(() => {
            addMessage(dict.respProcessFollow, 'bot');
            setTimeout(() => {
              addMessage(dict.askMoreGeneral, 'bot');
              renderOptions([
                { action: 'gear', text: dict.optGear },
                { action: 'about', text: dict.optAbout },
                { action: 'back', text: dict.optBack }
              ]);
            }, 500);
          }, 600);
        }, 600);
        return;
      }
      
      addMessage(botHtml, 'bot');
      
      if (followUpOptions.length > 0) {
        setTimeout(() => {
          addMessage(currentProjectData ? dict.askMoreProject : dict.askMoreGeneral, 'bot');
          renderOptions(followUpOptions);
        }, 600);
      }
    }, 450);
  });
  
  function renderMainOptions() {
    const mainOptions = currentProjectData 
      ? [
          { action: 'projectInfo', text: dict.optProjectInfo },
          { action: 'projectGear', text: dict.optProjectGear },
          { action: 'about', text: dict.optAbout },
          { action: 'contact', text: dict.optContact }
        ]
      : [
          { action: 'about', text: dict.optAbout },
          { action: 'gear', text: dict.optGear },
          { action: 'contact', text: dict.optContact },
          { action: 'process', text: dict.optProcess }
        ];
    renderOptions(mainOptions);
  }
  
  function renderOptions(options) {
    optsContainer.innerHTML = options.map(opt => 
      `<button class="assistant-opt-btn" data-action="${opt.action}">${opt.text}</button>`
    ).join('');
  }

  function addMessage(html, sender) {
    const msg = document.createElement('div');
    msg.className = `assistant-msg ${sender}`;
    msg.innerHTML = html;
    msgs.appendChild(msg);
    msgs.scrollTop = msgs.scrollHeight;
  }
}

// Dynamic settings, tracking & newsletter integrations
async function applySiteSettings() {
  try {
    if (typeof supabaseClient === 'undefined') return;
    const { data, error } = await supabaseClient.from('site_settings').select('key, value');
    if (error || !data) return;
    
    const settings = {};
    data.forEach(item => {
      settings[item.key] = item.value;
    });

    // Check Maintenance Mode
    if (settings.maintenance_mode === 'true') {
      const isPathAdmin = window.location.pathname.endsWith('admin.html');
      const isAdminLoggedIn = !!localStorage.getItem('admin_password');
      const isBypass = new URLSearchParams(window.location.search).has('bypass');

      if (!isPathAdmin && !isAdminLoggedIn && !isBypass) {
        showMaintenanceOverlay(settings.maintenance_message);
        return;
      }
    }
    
    // Apply home_intro
    if (settings.home_intro) {
      const homeIntroEl = document.querySelector('.intro .greeting-row span:not(.emoji)');
      if (homeIntroEl) homeIntroEl.textContent = settings.home_intro;
    }
    
    // Apply about_sidebar_intro
    if (settings.about_sidebar_intro) {
      const aboutIntroEl = document.querySelector('.brand-panel .intro[data-i18n="about-intro"]');
      if (aboutIntroEl) aboutIntroEl.textContent = settings.about_sidebar_intro;
    }
    
    // Apply about_bio
    if (settings.about_bio) {
      const bioEl = document.querySelector('.profile-block .profile-text');
      if (bioEl) {
        const paras = bioEl.querySelectorAll('p');
        if (paras.length > 0) {
          paras[0].innerHTML = settings.about_bio.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
          for (let i = 1; i < paras.length; i++) paras[i].remove();
        }
      }
    }
    
    // Apply contact_email
    if (settings.contact_email) {
      document.querySelectorAll('a[href^="mailto:"]').forEach(el => {
        el.href = `mailto:${settings.contact_email}`;
        el.childNodes.forEach(child => {
          if (child.nodeType === Node.TEXT_NODE) {
            const txt = child.textContent.trim();
            if (txt === 'levinskyj.cine@gmail.com' || txt.includes('@')) {
              child.textContent = settings.contact_email;
            }
          }
        });
      });
    }
    
    // Apply instagram_link
    if (settings.instagram_link) {
      document.querySelectorAll('a[href*="instagram.com"]').forEach(el => {
        el.href = settings.instagram_link;
      });
    }
    
    // Apply youtube_link
    if (settings.youtube_link) {
      document.querySelectorAll('a[href*="youtube.com"]').forEach(el => {
        el.href = settings.youtube_link;
      });
    }
  } catch (err) {
    console.error('Error applying site settings:', err);
  }
}

function showMaintenanceOverlay(customMessage) {
  const msg = customMessage || 'Na webu právě probíhají plánované úpravy a aktualizace. Vracíme se již brzy!';
  
  const maintenanceHtml = `
    <div id="maintenance-overlay" style="
      position: fixed;
      inset: 0;
      z-index: 99999;
      background: #faf8f5;
      color: #1c1917;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 32px 24px;
      text-align: center;
      font-family: 'Outfit', system-ui, -apple-system, sans-serif;
    ">
      <div style="max-width: 520px; width: 100%; background: #ffffff; border: 1px solid #e8e4dd; border-radius: 20px; padding: 48px 36px; box-shadow: 0 12px 32px rgba(0,0,0,0.06);">
        <div style="width: 56px; height: 56px; margin: 0 auto 24px; background: rgba(44, 62, 80, 0.08); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 28px; color: #2c3e50;">
          <i class="ph ph-wrench"></i>
        </div>
        <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.16em; color: #6b6560; margin-bottom: 8px;">
          Režim údržby
        </div>
        <h1 style="font-family: 'Bricolage Grotesque', Georgia, serif; font-size: 32px; font-weight: 600; color: #1c1917; margin: 0 0 16px 0; line-height: 1.25; letter-spacing: -0.02em;">
          Jan Levínský
        </h1>
        <p style="font-size: 15px; color: #6b6560; line-height: 1.6; margin: 0 0 32px 0;">
          ${msg}
        </p>
        <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
          <a href="mailto:levinskyj.cine@gmail.com" style="display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px; background: #2c3e50; color: #faf8f5; border-radius: 999px; text-decoration: none; font-size: 14px; font-weight: 500; transition: opacity 0.2s;">
            <i class="ph ph-envelope"></i> Napsat e-mail
          </a>
          <a href="admin.html" style="display: inline-flex; align-items: center; gap: 6px; padding: 12px 20px; background: #f0ece6; color: #1c1917; border-radius: 999px; text-decoration: none; font-size: 13px; font-weight: 500;">
            <i class="ph ph-lock-key"></i> Administrace
          </a>
        </div>
      </div>
    </div>
  `;

  document.body.style.overflow = 'hidden';
  const existing = document.getElementById('maintenance-overlay');
  if (existing) existing.remove();
  document.body.insertAdjacentHTML('beforeend', maintenanceHtml);
}

async function initTracker() {
  try {
    if (typeof supabaseClient === 'undefined') return;
    
    const pagePath = window.location.pathname;
    let projectId = null;
    if (pagePath.includes('project.html')) {
      const params = new URLSearchParams(window.location.search);
      const idVal = params.get('id');
      if (idVal) {
        projectId = parseInt(idVal) || null;
      }
    }
    
    const trackKey = (projectId ? `project_${projectId}` : 'page') + '_' + pagePath;
    const today = new Date().toISOString().split('T')[0];
    
    let localViews = {};
    try {
      localViews = JSON.parse(localStorage.getItem('last_page_views')) || {};
    } catch(e) {}
    
    if (localViews[trackKey] === today) {
      return;
    }
    
    const referrerVal = document.referrer || '';
    const { error } = await supabaseClient
      .from('page_views')
      .insert({
        project_id: projectId,
        page_path: pagePath,
        referrer: referrerVal
      });
      
    if (!error) {
      localViews[trackKey] = today;
      localStorage.setItem('last_page_views', JSON.stringify(localViews));
    }
  } catch (err) {
    console.error('Error tracking page view:', err);
  }
}

function initNewsletter() {
  // ── Inject modal styles (single source of truth, injected once) ──
  const styleId = 'newsletter-modal-styles';
  if (!document.getElementById(styleId)) {
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `
      /* Footer trigger button */
      .footer-newsletter { margin-top: 16px; }
      .newsletter-trigger {
        font-family: var(--sans);
        font-size: 13px;
        font-weight: 500;
        color: var(--muted);
        background: none;
        border: none;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 6px 12px;
        border-radius: var(--r-full);
        transition: color 0.3s ease, background 0.3s ease;
        letter-spacing: 0.02em;
      }
      .newsletter-trigger:hover {
        color: var(--accent);
        background: var(--accent-subtle);
      }
      .newsletter-trigger i { font-size: 15px; }

      /* Modal overlay */
      .nl-overlay {
        position: fixed; inset: 0;
        background: rgba(28, 25, 23, 0.45);
        backdrop-filter: blur(6px);
        -webkit-backdrop-filter: blur(6px);
        z-index: 9998;
        display: flex; align-items: center; justify-content: center;
        opacity: 0; pointer-events: none;
        transition: opacity 0.35s var(--ease-out-expo);
      }
      .nl-overlay.open { opacity: 1; pointer-events: auto; }

      /* Modal card */
      .nl-modal {
        background: var(--bg);
        border: 1px solid var(--border);
        border-radius: var(--r-lg);
        padding: 36px 32px 32px;
        width: 420px; max-width: calc(100vw - 40px);
        position: relative;
        box-shadow:
          0 24px 80px rgba(28, 25, 23, 0.18),
          0 4px 16px rgba(28, 25, 23, 0.08);
        transform: scale(0.95) translateY(12px);
        transition: transform 0.4s var(--ease-out-expo);
      }
      .nl-overlay.open .nl-modal {
        transform: scale(1) translateY(0);
      }

      /* Close button */
      .nl-close {
        position: absolute; top: 14px; right: 14px;
        width: 32px; height: 32px;
        display: flex; align-items: center; justify-content: center;
        border-radius: var(--r-full);
        color: var(--muted);
        background: none; border: none;
        cursor: pointer;
        font-size: 18px;
        transition: background 0.2s ease, color 0.2s ease;
      }
      .nl-close:hover {
        background: var(--surface);
        color: var(--text);
      }

      /* Content */
      .nl-icon {
        width: 44px; height: 44px;
        border-radius: var(--r-md);
        background: var(--accent-subtle);
        display: flex; align-items: center; justify-content: center;
        margin-bottom: 16px;
      }
      .nl-icon i { font-size: 22px; color: var(--accent); }
      .nl-title {
        font-family: var(--serif);
        font-size: 22px;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 6px;
      }
      .nl-desc {
        font-size: 13.5px;
        color: var(--muted);
        line-height: 1.55;
        margin-bottom: 20px;
      }

      /* Already-subscribed note */
      .nl-already {
        display: none;
        font-size: 12.5px;
        color: var(--muted);
        background: var(--surface);
        border: 1px solid var(--border-subtle);
        border-radius: var(--r-sm);
        padding: 8px 12px;
        margin-bottom: 14px;
        line-height: 1.45;
        gap: 6px;
        align-items: center;
      }
      .nl-already.visible { display: flex; }
      .nl-already i { font-size: 14px; color: var(--accent); flex-shrink: 0; }

      /* Form row */
      .nl-form { display: flex; gap: 8px; }
      .nl-input {
        flex: 1;
        font-family: var(--sans);
        font-size: 13.5px;
        padding: 10px 14px;
        border: 1px solid var(--border);
        border-radius: var(--r-sm);
        background: var(--bg-subtle);
        color: var(--text);
        outline: none;
        transition: border-color 0.25s ease, box-shadow 0.25s ease;
      }
      .nl-input::placeholder { color: var(--muted); opacity: 0.6; }
      .nl-input:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 3px var(--accent-subtle);
      }
      .nl-submit {
        display: flex; align-items: center; justify-content: center;
        width: 42px; height: 42px;
        border-radius: var(--r-sm);
        background: var(--accent);
        color: var(--text-on-accent);
        border: none; cursor: pointer;
        font-size: 16px;
        transition: opacity 0.2s ease, transform 0.2s ease;
        flex-shrink: 0;
      }
      .nl-submit:hover { opacity: 0.88; transform: scale(1.04); }
      .nl-submit:active { transform: scale(0.97); }
      .nl-submit:disabled { opacity: 0.5; cursor: default; transform: none; }
      .nl-submit i { font-size: 17px; }

      /* Status */
      .nl-status {
        font-size: 13px;
        margin-top: 12px;
        min-height: 0;
        opacity: 0;
        transform: translateY(-4px);
        transition: opacity 0.3s ease, transform 0.3s ease;
      }
      .nl-status.show { opacity: 1; transform: translateY(0); }
      .nl-status.success { color: var(--accent); }
      .nl-status.error { color: #b33a3a; }

      /* Responsive */
      @media (max-width: 480px) {
        .nl-modal { padding: 28px 24px 24px; }
        .nl-title { font-size: 20px; }
        .nl-form { flex-direction: column; }
        .nl-submit { width: 100%; height: 42px; border-radius: var(--r-sm); }
      }
    `;
    document.head.appendChild(style);
  }

  // ── Inject modal HTML (single source of truth) ──
  if (!document.getElementById('newsletterModal')) {
    const modal = document.createElement('div');
    modal.id = 'newsletterModal';
    modal.innerHTML = `
      <div class="nl-overlay" role="dialog" aria-modal="true" aria-labelledby="nlTitle">
        <div class="nl-modal">
          <button class="nl-close" type="button" aria-label="Zavřít">
            <i class="ph ph-x"></i>
          </button>
          <div class="nl-icon">
            <i class="ph ph-newspaper"></i>
          </div>
          <h2 class="nl-title" id="nlTitle">Newsletter</h2>
          <p class="nl-desc">Přihlas se k odběru novinek z portfolia. Žádný spam — jen to nejdůležitější.</p>
          <div class="nl-already" id="nlAlready">
            <i class="ph ph-check-circle"></i>
            <span>Už jsi přihlášený/a</span>
          </div>
          <form class="nl-form" id="nlForm" onsubmit="return false;">
            <input class="nl-input" type="email" id="nlEmail" placeholder="Tvůj e-mail..." required autocomplete="email">
            <button class="nl-submit" type="submit" aria-label="Odebírat">
              <i class="ph ph-paper-plane-tilt"></i>
            </button>
          </form>
          <div class="nl-status" id="nlStatus"></div>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }

  // ── References ──
  const overlay = document.querySelector('#newsletterModal .nl-overlay');
  const closeBtn = document.querySelector('#newsletterModal .nl-close');
  const nlForm = document.getElementById('nlForm');
  const nlEmail = document.getElementById('nlEmail');
  const nlStatus = document.getElementById('nlStatus');
  const nlSubmit = document.querySelector('.nl-submit');
  const nlAlready = document.getElementById('nlAlready');

  function openModal() {
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
    // Check if already subscribed
    if (localStorage.getItem('newsletter_subscribed') === '1') {
      nlAlready.classList.add('visible');
    } else {
      nlAlready.classList.remove('visible');
    }
    // Reset status & focus
    nlStatus.textContent = '';
    nlStatus.className = 'nl-status';
    setTimeout(() => nlEmail.focus(), 350);
  }

  function closeModal() {
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  // ── Open modal on footer trigger click ──
  document.addEventListener('click', (e) => {
    const trigger = e.target.closest('.newsletter-trigger');
    if (!trigger) return;
    openModal();
  });

  // ── Close on overlay click ──
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal();
  });

  // ── Close button ──
  closeBtn.addEventListener('click', closeModal);

  // ── ESC key ──
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('open')) {
      closeModal();
    }
  });

  // ── Form submission (Supabase logic unchanged) ──
  nlForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = nlEmail.value.trim();
    if (!email) return;

    nlSubmit.disabled = true;
    nlStatus.innerHTML = '<span style="opacity: 0.7;">Přihlašuji...</span>';
    nlStatus.className = 'nl-status show';

    try {
      if (typeof supabaseClient === 'undefined') {
        throw new Error('Supabase není dostupný. Zkus to prosím později.');
      }

      const { error } = await supabaseClient
        .from('subscribers')
        .insert({ email });

      if (error) {
        if (error.code === '23505') {
          throw new Error('Tento e-mail už byl přihlášen k odběru.');
        }
        throw error;
      }

      localStorage.setItem('newsletter_subscribed', '1');
      nlAlready.classList.add('visible');
      nlStatus.innerHTML = '✓ Díky za odběr! Brzy dostaneš novinky.';
      nlStatus.className = 'nl-status show success';
      nlEmail.value = '';

      // Show unsubscribe hint after a beat
      setTimeout(() => {
        nlStatus.innerHTML = '✓ Díky za odběr! <small style="display: block; margin-top: 6px; opacity: 0.7; font-size: 12px;">Odhlásit se můžeš z každého emailu.</small>';
      }, 2200);
    } catch (err) {
      console.error('Newsletter error:', err);
      nlStatus.textContent = '✗ ' + (err.message || 'Něco se pokazilo. Zkuste to prosím znovu.');
      nlStatus.className = 'nl-status show error';
    } finally {
      nlSubmit.disabled = false;
    }
  });
}

// Helper to canonicalize media_src paths
function normalizeMediaSrc(src) {
  if (!src) return '';
  try {
    return decodeURIComponent(src);
  } catch (e) {
    return src;
  }
}

// Browser fingerprinting for likes (with robust fallback)
async function getUserFingerprint() {
  try {
    let canvasData = '';
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('fingerprint', 2, 2);
        canvasData = canvas.toDataURL();
      }
    } catch (e) {}

    const data = [
      navigator.userAgent || '',
      navigator.language || '',
      screen.width + 'x' + screen.height,
      new Date().getTimezoneOffset(),
      canvasData
    ].join('|');

    if (window.crypto && crypto.subtle) {
      const msgUint8 = new TextEncoder().encode(data);
      const hashBuffer = await crypto.subtle.digest('SHA-256', msgUint8);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }
  } catch (err) {
    console.warn('Fingerprint computation fallback used:', err);
  }

  // Fallback to persistent local storage ID
  let anonId = localStorage.getItem('anon_user_fp');
  if (!anonId) {
    anonId = 'anon_' + Math.random().toString(36).substring(2) + Date.now().toString(36);
    localStorage.setItem('anon_user_fp', anonId);
  }
  return anonId;
}

// Initialize likes functionality for individual media items
async function initMediaLikes(retryCount = 0) {
  const params = new URLSearchParams(window.location.search);
  const projectId = params.get('id');
  if (!projectId) return;
  
  // Check if Supabase client is available (with retry)
  if (typeof supabaseClient === 'undefined' || !supabaseClient) {
    if (retryCount < 5) {
      setTimeout(() => initMediaLikes(retryCount + 1), 300);
    } else {
      console.warn('Supabase client not initialized, skipping likes initialization');
    }
    return;
  }
  
  try {
    const fingerprint = await getUserFingerprint();
    const likeBtns = document.querySelectorAll('.tile-like-btn');
    
    if (likeBtns.length === 0) {
      if (retryCount < 5) {
        setTimeout(() => initMediaLikes(retryCount + 1), 300);
      }
      return;
    }
    
    // Load likes for all media items
    for (const btn of likeBtns) {
      const rawMediaSrc = btn.dataset.mediaSrc;
      if (!rawMediaSrc) continue;
      const mediaSrc = normalizeMediaSrc(rawMediaSrc);
      
      try {
        // Load like count
        const { data: countData, error: countError } = await supabaseClient
          .rpc('get_media_likes_count', { 
            p_project_id: projectId, 
            p_media_src: mediaSrc 
          });
        
        if (!countError && countData !== null) {
          btn.querySelector('.like-count').textContent = countData;
        }
        
        // Check if user liked this media
        const { data: likedData, error: likedError } = await supabaseClient
          .rpc('check_user_liked_media', { 
            p_project_id: projectId, 
            p_media_src: mediaSrc,
            p_user_fingerprint: fingerprint 
          });
        
        if (!likedError && likedData) {
          btn.classList.add('liked');
          const icon = btn.querySelector('i');
          if (icon) {
            icon.classList.remove('ph');
            icon.classList.add('ph-fill', 'ph-heart');
          }
        }
        
        // Add click handler (only once)
        if (!btn.dataset.listenerAttached) {
          btn.dataset.listenerAttached = 'true';
          
          btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (btn.disabled) return;
            btn.disabled = true;
            
            try {
              const { data, error } = await supabaseClient
                .rpc('toggle_media_like', {
                  p_project_id: projectId,
                  p_media_src: mediaSrc,
                  p_user_fingerprint: fingerprint
                });
              
              if (error) throw error;
              
              const isLiked = data.liked;
              const newCount = data.count;
              
              const countEl = btn.querySelector('.like-count');
              if (countEl) countEl.textContent = newCount;
              
              const icon = btn.querySelector('i');
              if (isLiked) {
                btn.classList.add('liked');
                if (icon) {
                  icon.classList.remove('ph');
                  icon.classList.add('ph-fill', 'ph-heart');
                }
                btn.style.transform = 'scale(1.15)';
                setTimeout(() => { btn.style.transform = ''; }, 200);
              } else {
                btn.classList.remove('liked');
                if (icon) {
                  icon.classList.remove('ph-fill');
                  icon.classList.add('ph', 'ph-heart');
                }
                btn.style.transform = 'scale(0.9)';
                setTimeout(() => { btn.style.transform = ''; }, 200);
              }
            } catch (err) {
              console.error('Error toggling like:', err);
            } finally {
              btn.disabled = false;
            }
          });
        }
        
      } catch (err) {
        console.error('Error loading likes for media:', mediaSrc, err);
      }
    }
    
  } catch (err) {
    console.error('Error initializing media likes:', err);
  }
}

function initSupabaseFeatures() {
  applySiteSettings();
  initTracker();
  initNewsletter();
  
  // Initialize likes on project page for individual media items
  if (window.location.pathname.includes('project.html')) {
    // Delay to ensure gallery is rendered
    setTimeout(() => {
      initMediaLikes();
    }, 500);
  }
}

// ── Web Audio API ASMR Sound Engine ──
let audioCtx = null;

function getAudioContext() {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) {
      audioCtx = new AudioContextClass();
    }
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume().catch(() => {});
  }
  return audioCtx;
}

// Audio preloader cache for custom MP3 files
const audioCache = {};

function playMp3Sound(filename) {
  const path = `media/audio/${filename}`;
  if (!audioCache[path]) {
    const audio = new Audio(path);
    audio.volume = 0.1;
    audioCache[path] = audio;
  }
  const audio = audioCache[path];
  if (audio) {
    audio.currentTime = 0;
    const playPromise = audio.play();
    if (playPromise !== undefined) {
      playPromise.catch(() => {
        // MP3 file not found or blocked, fallback to Web Audio synthesis
        return false;
      });
      return true;
    }
  }
  return false;
}

function playAsmrSound(type) {
  if (localStorage.getItem('site_sound_muted') === 'true') return;

  const keyMap = {
    'shutter': 'shutter.mp3',
    'like': 'shutter.mp3',
    'dial': 'dial.mp3',
    'filter': 'dial.mp3',
    'pop': 'pop.mp3',
    'modal': 'pop.mp3',
    'tile': 'pop.mp3',
    'whoosh': 'whoosh.mp3',
    'newsletter': 'whoosh.mp3'
  };

  const mp3File = keyMap[type];
  if (mp3File) {
    // Attempt MP3 playback first
    const path = `media/audio/${mp3File}`;
    if (!audioCache[path]) {
      const audio = new Audio(path);
      audio.volume = 0.1;
      audioCache[path] = audio;
    }
    const audio = audioCache[path];
    if (audio) {
      audio.currentTime = 0;
      const promise = audio.play();
      if (promise !== undefined) {
        promise.then(() => {
          console.log('[ASMR MP3 Audio]', mp3File);
        }).catch(() => {
          // MP3 file missing in media/audio/, fallback to Web Audio API synthesis
          synthAsmrSound(type);
        });
        return;
      }
    }
  }

  synthAsmrSound(type);
}

function synthAsmrSound(type) {
  const ctx = getAudioContext();
  if (!ctx) return;

  const now = ctx.currentTime;
  console.log('[ASMR Synth Audio]', type, 'AudioContext state:', ctx.state);

  try {
    if (type === 'shutter' || type === 'like') {
      // Camera shutter click (sine pitch drop + noise burst)
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(950, now);
      osc.frequency.exponentialRampToValueAtTime(140, now + 0.05);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.05);

      // Secondary metallic mechanical click
      setTimeout(() => {
        if (!ctx) return;
        const osc2 = ctx.createOscillator();
        const gain2 = ctx.createGain();
        osc2.type = 'triangle';
        osc2.frequency.setValueAtTime(1300, ctx.currentTime);
        osc2.frequency.exponentialRampToValueAtTime(220, ctx.currentTime + 0.03);
        gain2.gain.setValueAtTime(0.06, ctx.currentTime);
        gain2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.03);
        osc2.connect(gain2);
        gain2.connect(ctx.destination);
        osc2.start();
        osc2.stop(ctx.currentTime + 0.03);
      }, 25);

    } else if (type === 'dial' || type === 'filter') {
      // Camera dial click (crisp wood/metal click)
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(1500, now);
      osc.frequency.exponentialRampToValueAtTime(350, now + 0.02);
      gain.gain.setValueAtTime(0.07, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.02);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.02);

    } else if (type === 'pop' || type === 'modal' || type === 'tile') {
      // Soft lens aperture pop / modal open
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(350, now);
      osc.frequency.exponentialRampToValueAtTime(950, now + 0.04);
      gain.gain.setValueAtTime(0.06, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.04);

    } else if (type === 'whoosh' || type === 'newsletter') {
      // Paper / envelope slide whoosh (filtered noise)
      const bufferSize = ctx.sampleRate * 0.1;
      const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const output = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        output[i] = Math.random() * 2 - 1;
      }
      const whiteNoise = ctx.createBufferSource();
      whiteNoise.buffer = buffer;

      const filter = ctx.createBiquadFilter();
      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(700, now);
      filter.frequency.exponentialRampToValueAtTime(2200, now + 0.1);
      filter.Q.value = 2.5;

      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0.05, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);

      whiteNoise.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);
      whiteNoise.start(now);
      whiteNoise.stop(now + 0.1);
    }
  } catch (e) {
    console.error('[ASMR Synth Error]', e);
  }
}

// Global debug test helper accessible from DevTools console
window.testAsmrSound = function(type) {
  const ctx = getAudioContext();
  if (ctx && ctx.state === 'suspended') ctx.resume();
  playAsmrSound(type || 'shutter');
};

// ── Attach sound triggers to user UI actions in CAPTURE phase ──
['pointerdown', 'touchstart', 'click'].forEach(evtType => {
  document.addEventListener(evtType, (e) => {
    getAudioContext();

    if (evtType === 'click') {
      if (e.target.closest('.tile-like-btn')) {
        playAsmrSound('shutter');
      } else if (e.target.closest('.filter-row a')) {
        playAsmrSound('dial');
      } else if (e.target.closest('.newsletter-trigger')) {
        playAsmrSound('whoosh');
      } else if (e.target.closest('.tile')) {
        playAsmrSound('pop');
      }
    }
  }, true); // Use capture phase so stopPropagation doesn't block audio triggers
});

// Call on startup
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    initGlobalNavigation();
    recalcPerforations();
    initCuteAssistant();
    initSupabaseFeatures();
  });
} else {
  initGlobalNavigation();
  recalcPerforations();
  initCuteAssistant();
  initSupabaseFeatures();
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

// Keyboard accessibility support for bento / gallery tiles
document.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    const tile = e.target && typeof e.target.closest === 'function' ? e.target.closest('.tile') : null;
    if (tile) {
      const isLink = tile.tagName === 'A';
      if (e.key === ' ' || !isLink) {
        e.preventDefault();
        tile.click();
      }
    }
  }
});
