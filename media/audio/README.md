# ASMR Vlastní Audio Soubory

Pro použití vlastních reálných zvukových nahrávek stačí vložit `.mp3` soubory do této složky (`media/audio/`):

1. **`shutter.mp3`** — Cvaknutí spouště fotoaparátu (přehraje se při kliknutí na lajk)
2. **`dial.mp3`** — Cvaknutí voliče režimů (přehraje se při přepínání filtrů Vše / Photo / Video)
3. **`pop.mp3`** — Zvuk clony / otvoru (přehraje se při otevření fotky / modálu)
4. **`whoosh.mp3`** — Zvuk zasunutí papíru / obálky (přehraje se u newsletteru)

### 💡 Jak to funguje:
- Pokud `.mp3` soubor ve složce existuje, přehraje se vaše reálné audio.
- Pokud `.mp3` soubor chybí, systém automaticky použije záložní generátor zvuků přímo z JavaScriptu.
