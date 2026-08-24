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
    const tile = e.target.closest('.tile');
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
    const tile = e.target.closest('.tile');
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

// Call on startup
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    initGlobalNavigation();
    recalcPerforations();
    initCuteAssistant();
  });
} else {
  initGlobalNavigation();
  recalcPerforations();
  initCuteAssistant();
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
