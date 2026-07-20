<div align="center">
<br>

<img src="media/logo.png" width="72" height="72" alt="LJ">

# levinskyj.art

**Cinematography & Photography** · Portfolio Jana Levínského

<br>

[<img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%232c3e50' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71'%3E%3C/path%3E%3Cpath d='M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71'%3E%3C/path%3E%3C/svg%3E"> levinskyj.art](https://levinskyj.art) · [<img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%232c3e50' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='2' y='2' width='20' height='20' rx='5' ry='5'%3E%3C/rect%3E%3Cpath d='M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z'%3E%3C/path%3E%3Cline x1='17.5' y1='6.5' x2='17.51' y2='6.5'%3E%3C/line%3E%3C/svg%3E"> @levinskyj.cine](https://www.instagram.com/levinskyj.cine/) · [<img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%232c3e50' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 12a29 29 0 0 0 .46 5.58 2.78 2.78 0 0 0 1.94 2C5.12 20 12 20 12 20s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2A29 29 0 0 0 23 12a29 29 0 0 0-.46-5.58z'%3E%3C/path%3E%3Cpolygon points='9.75 15.02 15.5 12 9.75 8.98 9.75 15.02'%3E%3C/polygon%3E%3C/svg%3E"> @LevinskyJ](https://www.youtube.com/@LevinskyJ)

<br>

</div>

---

<div align="center">

```
┌─────────────────────────────────────────────────────┐
│  ⚬⚬⚬⚬  každý snímek nese perforaci  ⚬⚬⚬⚬  │
│  ⚬⚬⚬⚬  každý přechod je jako střih  ⚬⚬⚬⚬  │
│  ⚬⚬⚬⚬  každý projekt je políčko filmu  ⚬⚬⚬⚬  │
└─────────────────────────────────────────────────────┘
```

</div>

## 🎞️ Co to je

Osobní portfolio, které zachází s webem jako s filmovým pásem. Každý obrázek nese **35mm perforace**, rozložení dýchá v **bento gridu** a přechody působí jako střihy mezi scénami.

Čistě vanilkový HTML, CSS a JavaScript. Bez frameworků, bez build stepu. Jen prohlížeč, DOM a hodně pozornosti k detailu.

---

## ✨ Co umí

### 🎬 Filmové perforace
Každý video i foto snímek je orámovaný procedurálně generovanými 35mm okýnky. Perforace se škálují podle poměru stran a vykreslují se jako průhledná vrstva — není to border, je to filmová logika.

### 🍱 Bento Grid Galerie
Projekty plují v responzivní mřížce s reálnými poměry stran. Žádné forced cropování, žádné přednastavené rámečky. Drag & drop pro změnu pořadí.

### ✨ Plynulé animace
- **Přeskupení gridu** při filtrování — kartičky necvakají, cestují na nové pozice
- **Scroll-triggerované odkrytí** — působí kinematograficky, ne korporátně
- **Mikro-interakce** na každém hoveru, kliku, změně stavu
- Plná podpora `prefers-reduced-motion`

### 📱 Responzivní design
Od mobilu po ultra-wide — hamburger menu na mobile, postupně se rozšiřující sidebar na desktopu. Všechny breakpointy dolaďěné ručně.

### 🎨 Vizuální styl
Tmavě modrý akcent (`#2c3e50`) na teplém krémovém pozadí (`#faf8f5`). Žádný čistě bílý povrch, žádná ostrá čerň. Písmo kombinuje Bricolage Grotesque (sans) s Interem (pro data a metriky).

---

## 🧱 Struktura projektu

```
├── index.html          # Hlavní portfolio stránka
├── about.html          # Životopis / O mně
├── project.html        # Detail projektu (dynamický)
├── card.html           # Digitální vizitka
├── style.css           # Sdílené styly
├── main.js             # Sdílené JS (i18n, perforace, animace)
├── projects.json       # Data všech projektů
├── builder.py          # Lokální editor projektů
├── builder.html        # UI pro editor
└── media/              # Fotky, videa, logo
```

---

## 🛠️ Vývoj

```bash
# Editor projektů
python builder.py
# otevře http://localhost:8765

# Stránka je čistě statická — stačí otevřít v prohlížeči
```

---

## 📜 Licence

<div align="center">
<br>
© Jan Levínský · všechna práva vyhrazena
<br><br>
</div>
