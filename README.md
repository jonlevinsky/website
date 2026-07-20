<div align="center">
<br>
<img src="media/Logo.png" width="72" height="72" alt="LJ">

# levinskyj.art

**Cinematography & Photography** · Portfolio Jana Levínského

<br>

[🌐 levinskyj.art](https://levinskyj.art) · [📷 @levinskyj.cine](https://www.instagram.com/levinskyj.cine/) · [▶ @LevinskyJ](https://www.youtube.com/@LevinskyJ)

</div>

---

> Každý snímek nese perforaci.  
> Každý přechod je jako střih.  
> Každý projekt je políčko filmu.

---

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
Od mobilu po ultra-wide. Hamburger menu na mobilu, sidebar na desktopu. Všechny breakpointy dolaďené ručně. i18n automatický překlad pro návštěvníky mimo ČR.

### 🎨 Vizuální styl
Tmavě modrý akcent (`#2c3e50`) na teplém krémovém pozadí (`#faf8f5`). Žádná čistá bílá, žádná ostrá čerň. Písmo kombinuje Bricolage Grotesque s Interem.

---

## 🧱 Struktura projektu

```
├── index.html         # Hlavní portfolio stránka
├── about.html         # Životopis / O mně
├── project.html       # Detail projektu (dynamický)
├── card.html          # Digitální vizitka
├── style.css          # Sdílené styly
├── main.js            # Sdílené JS (i18n, perforace, animace)
├── projects.json      # Data všech projektů
├── builder.py         # Lokální editor projektů
└── media/             # Fotky, videa, logo
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

<div align="center">

© Jan Levínský · všechna práva vyhrazena

</div>
