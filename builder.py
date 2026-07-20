#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
projects_builder.py — Editor pro projects.json s auto-strukturou složek
======================================================================
Ulož vedle index.html, project.html, projects.json, Kamera.md a Optika.md.
Spusť: python projects_builder.py
Otevři: http://localhost:8765

NOVÉ FUNKCE:
- Validace: duplicitní ID, nefunkční cesty, povinná pole
- Bulk operace: multi-select, bulk gear, bulk rename
- Preview: náhled projektu, JSON diff
- Undo/Redo: stack změn v session
- SEO: auto slug, auto alt text, word count
- Placeholders: LQIP (low-res) generace
- Sitemap + deploy: generátor + git push
"""

# ═══════════════════════════════════════════════════════════════
# Imports
# ═══════════════════════════════════════════════════════════════

import base64
import datetime
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

# --- Paths & Server ---
PORT = 8765
JSON_FILE = Path("projects.json")
MEDIA_DIR = Path("media")
BACKUP_DIR = Path(".builder_backups")
KAMERA_MD = Path("./gear/Kamera.md")
OPTIKA_MD = Path("./gear/Optika.md")
HTML_FILE = Path(__file__).parent / "builder.html"
SITE_URL = "https://levinskyj.art"

# --- Gear Categories ---
GEAR_CATEGORIES = [
    "camera", "lenses", "gimbal/stabilization", "lighting",
    "audio", "software", "color", "drone", "filter",
    "tripod", "monitor", "recorder"
]

GEAR_LABELS = {
    "camera": "Camera",
    "lenses": "Lenses",
    "gimbal/stabilization": "Gimbal / Stabilization",
    "lighting": "Lighting",
    "audio": "Audio",
    "software": "Software",
    "color": "Color",
    "drone": "Drone",
    "filter": "Filter",
    "tripod": "Tripod",
    "monitor": "Monitor",
    "recorder": "Recorder"
}

# --- WebP Conversion ---
WEBP_QUALITY = 85
WEBP_THUMB_QUALITY = 80
MAX_IMAGE_WIDTH = 1920
MAX_THUMB_WIDTH = 640

# --- LQIP / Placeholder ---
LQIP_WIDTH = 32
LQIP_BLUR = 10
LQIP_QUALITY = 30

# --- OG Image (style.css light theme) ---
OG_WIDTH = 1200
OG_HEIGHT = 630
OG_BG = (250, 248, 245)        # --bg: #faf8f5
OG_ACCENT = (44, 62, 80)       # --accent: #2c3e50
OG_TEXT = (28, 25, 23)         # --text: #1c1917
OG_MUTED = (107, 101, 96)      # --muted: #6b6560
PERF_COLOR = (250, 248, 245)

# --- Undo / Redo ---
MAX_UNDO = 50
undo_stack = []
redo_stack = []


# ═══════════════════════════════════════════════════════════════
# Undo / Redo
# ═══════════════════════════════════════════════════════════════

def push_undo_state():
    global undo_stack, redo_stack
    state = json.dumps(data["projects"], ensure_ascii=False, sort_keys=True)
    if undo_stack and undo_stack[-1] == state:
        return
    undo_stack.append(state)
    if len(undo_stack) > MAX_UNDO:
        undo_stack.pop(0)
    redo_stack.clear()

def undo():
    global undo_stack, redo_stack
    if len(undo_stack) < 2:
        return False
    current = undo_stack.pop()
    redo_stack.append(current)
    previous = undo_stack[-1]
    data["projects"] = json.loads(previous)
    return True

def redo():
    global undo_stack, redo_stack
    if not redo_stack:
        return False
    state = redo_stack.pop()
    undo_stack.append(state)
    data["projects"] = json.loads(state)
    return True


# ═══════════════════════════════════════════════════════════════
# Tech Inventory (from Markdown)
# ═══════════════════════════════════════════════════════════════

def load_tech_inventory():
    inv = {}
    if KAMERA_MD.exists():
        with open(KAMERA_MD, "r", encoding="utf-8") as f:
            text = f.read()
        sections = text.split("\n#")
        for sec in sections:
            sec_title = sec.splitlines()[0].strip().lower() if sec else ''
            lines = sec.splitlines()
            in_table = False
            for line in lines:
                line = line.strip()
                if line.startswith("|") and line.count("|") >= 2:
                    if "---" in line:
                        in_table = True
                        continue
                    if in_table:
                        cells = [c.strip() for c in line.split("|")[1:-1]]
                        if cells:
                            name = cells[0].replace("***", "").replace("**", "").replace("*", "").strip()
                            if name and name.lower() not in ("nazev", "name", ""):
                                if "foto" in sec_title or "photo" in sec_title:
                                    inv.setdefault("camera", []).append(name)
                                elif "video" in sec_title:
                                    inv.setdefault("camera", []).append(name)
    if OPTIKA_MD.exists():
        with open(OPTIKA_MD, "r", encoding="utf-8") as f:
            text = f.read()
        sections = text.split("\n#")
        for sec in sections:
            sec_title = sec.splitlines()[0].strip().lower() if sec else ''
            lines = sec.splitlines()
            in_table = False
            for line in lines:
                line = line.strip()
                if line.startswith("|") and line.count("|") >= 2:
                    if "---" in line:
                        in_table = True
                        continue
                    if in_table:
                        cells = [c.strip() for c in line.split("|")[1:-1]]
                        if cells:
                            name = cells[0].replace("***", "").replace("**", "").replace("*", "").strip()
                            if name and name.lower() not in ("nazev", "name", ""):
                                if "objektiv" in sec_title or "lens" in sec_title or "optika" in sec_title:
                                    inv.setdefault("lenses", []).append(name)
                                elif "filtr" in sec_title or "filter" in sec_title:
                                    inv.setdefault("filter", []).append(name)
    for k in inv:
        seen = set()
        dedup = []
        for item in inv[k]:
            if item not in seen:
                seen.add(item)
                dedup.append(item)
        inv[k] = dedup
    return inv


# ═══════════════════════════════════════════════════════════════
# Data Load / Save
# ═══════════════════════════════════════════════════════════════

data = {"projects": []}
tech_inventory = {}

def load_json():
    global data
    if JSON_FILE.exists():
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
            data["projects"] = raw if isinstance(raw, list) else raw.get("projects", [])
    else:
        data["projects"] = []

def save_json():
    BACKUP_DIR.mkdir(exist_ok=True)
    if JSON_FILE.exists():
        ts = datetime.datetime.now().strftime("%H%M%S")
        shutil.copy(JSON_FILE, BACKUP_DIR / f"projects_{ts}.json")
    MEDIA_DIR.mkdir(exist_ok=True)
    tmp = JSON_FILE.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data["projects"], f, ensure_ascii=False, indent=2)
    tmp.replace(JSON_FILE)


# ═══════════════════════════════════════════════════════════════
# Utility Functions
# ═══════════════════════════════════════════════════════════════

def safe_folder_name(s):
    s = re.sub(r'[\\/:*?"<>|]', "", str(s))
    s = s.strip().replace(" ", "-")
    return s or "projekt"

def normalize_filename(filename):
    name = Path(filename).stem
    ext = Path(filename).suffix.lower()
    name = name.lower()
    name = name.replace(" ", "-")
    name = re.sub(r'[^a-z0-9_-]', '', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    return (name or "file") + ext

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def word_count(text):
    if not text:
        return 0
    return len(text.split())

def reading_time(text):
    wc = word_count(text)
    return max(1, round(wc / 200))


# ═══════════════════════════════════════════════════════════════
# File Type Detection
# ═══════════════════════════════════════════════════════════════

def is_image_ext(path):
    return Path(path).suffix.lower() in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif")

def is_image_file(path):
    ext = Path(path).suffix.lower()
    return ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp")

def is_video_ext(path):
    return Path(path).suffix.lower() in (".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v")


# ═══════════════════════════════════════════════════════════════
# WebP Conversion
# ═══════════════════════════════════════════════════════════════

def convert_to_webp(image_bytes, quality=WEBP_QUALITY, max_width=MAX_IMAGE_WIDTH):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ('RGBA', 'P'):
            if img.mode == 'P':
                img = img.convert('RGBA')
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        if max_width > 0 and img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)
        output = io.BytesIO()
        img.save(output, format='WEBP', quality=quality, method=6)
        output.seek(0)
        return output.read(), img.width, img.height
    except Exception as e:
        print(f"[WebP] Conversion error: {e}")
        return None, 0, 0

def generate_webp_thumbnail(image_bytes, quality=WEBP_THUMB_QUALITY, max_width=MAX_THUMB_WIDTH):
    return convert_to_webp(image_bytes, quality=quality, max_width=max_width)


# ═══════════════════════════════════════════════════════════════
# LQIP / Placeholder Generation
# ═══════════════════════════════════════════════════════════════

def generate_lqip(image_bytes, width=LQIP_WIDTH, quality=LQIP_QUALITY, blur=LQIP_BLUR):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        ratio = img.height / img.width
        new_height = max(1, int(width * ratio))
        img = img.resize((width, new_height), Image.LANCZOS)
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        b64 = base64.b64encode(output.read()).decode('utf-8')
        return f"data:image/jpeg;base64,{b64}"
    except Exception as e:
        print(f"[LQIP] Error: {e}")
        return None

def generate_lqip_for_file(filepath):
    try:
        with open(filepath, "rb") as f:
            return generate_lqip(f.read())
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════
# Video Utilities
# ═══════════════════════════════════════════════════════════════

def generate_video_thumbnail(source_path, thumb_path, seek_time=3.0):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    try:
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            ffmpeg, "-hide_banner", "-loglevel", "error",
            "-ss", str(seek_time), "-i", str(source_path),
            "-frames:v", "1", "-q:v", "2", "-y", str(thumb_path)
        ], check=True)
        return thumb_path.exists()
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════
# OG Image Generation — matches style.css (light theme)
# ═══════════════════════════════════════════════════════════════

FONT_DIR = Path(__file__).parent / "fonts"

def _load_og_fonts():
    brico = _try_font(str(FONT_DIR / "BricolageGrotesque-Regular.ttf"), size=52) or ImageFont.load_default()
    inter_m = _try_font(str(FONT_DIR / "Inter" / "extras" / "ttf" / "Inter-Medium.ttf"), size=22) or ImageFont.load_default()
    inter_r = _try_font(str(FONT_DIR / "Inter" / "extras" / "ttf" / "Inter-Regular.ttf"), size=16) or ImageFont.load_default()
    inter_s = _try_font(str(FONT_DIR / "Inter" / "extras" / "ttf" / "Inter-Regular.ttf"), size=13) or ImageFont.load_default()
    return brico, inter_m, inter_r, inter_s

def _draw_perforations(draw, x, y, w, h, count=8, horizontal=True):
    if horizontal:
        dot_w = max(3, w // count // 3)
        dot_h = max(4, h // 8)
        gap = (w - dot_w * count) // (count + 1)
        for i in range(count):
            dx = x + gap + i * (dot_w + gap)
            draw.ellipse([dx, y, dx + dot_w, y + dot_h], fill=PERF_COLOR)
            draw.ellipse([dx, y + h - dot_h, dx + dot_w, y + h], fill=PERF_COLOR)
    else:
        dot_w = max(4, w // 8)
        dot_h = max(3, h // count // 3)
        gap = (h - dot_h * count) // (count + 1)
        for i in range(count):
            dy = y + gap + i * (dot_h + gap)
            draw.ellipse([x, dy, x + dot_w, dy + dot_h], fill=PERF_COLOR)
            draw.ellipse([x + w - dot_w, dy, x + w - dot_w, dy + dot_h], fill=PERF_COLOR)

def _load_thumbnail(path):
    try:
        if not path or not Path(path).exists():
            return None
        return Image.open(path)
    except Exception:
        return None

def _paste_thumb_tile(base, thumb, x, y, tw, th, is_video=False, index=0):
    if thumb is None:
        return
    thumb_copy = thumb.copy()
    r = thumb_copy.width / thumb_copy.height
    target_r = tw / th
    if r > target_r:
        new_h = th
        new_w = int(th * r)
    else:
        new_w = tw
        new_h = int(tw / r)
    thumb_copy = thumb_copy.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - tw) // 2
    top = (new_h - th) // 2
    thumb_copy = thumb_copy.crop((left, top, left + tw, top + th))
    dark = Image.new('RGB', (tw, th), (0, 0, 0))
    thumb_copy = Image.blend(thumb_copy, dark, 0.15)
    base.paste(thumb_copy, (x, y))

    draw = ImageDraw.Draw(base)
    if is_video:
        hole_count = max(3, th // 60)
        _draw_perforations(draw, x, y, tw, th, count=hole_count, horizontal=False)
    else:
        hole_count = max(3, tw // 60)
        _draw_perforations(draw, x, y, tw, th, count=hole_count, horizontal=True)

def _try_font(*paths, size=28):
    for p in paths:
        try:
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
        except Exception:
            continue
    return None

def generate_simple_og_image(project, output_path=None):
    """OG image — style.css light theme, single project image as full background."""
    from PIL import ImageDraw

    brico, inter_m, inter_r, inter_s = _load_og_fonts()
    W, H = 1200, 630

    src = project.get("thumbnail")
    if not src or not Path(src).exists():
        for m in (project.get("media") or []):
            src = m.get("thumbnail") or m.get("src")
            if src and Path(src).exists():
                break
            src = None

    img = Image.new('RGB', (W, H), OG_BG)
    draw = ImageDraw.Draw(img)

    if src:
        thumb = _load_thumbnail(src)
        if thumb:
            r = thumb.width / thumb.height
            target_r = W / H
            if r > target_r:
                new_w = W
                new_h = int(W / r)
            else:
                new_h = H
                new_w = int(H * r)
            thumb = thumb.resize((new_w, new_h), Image.LANCZOS)
            left = (new_w - W) // 2
            top = (new_h - H) // 2
            thumb = thumb.crop((left, top, left + W, top + H)).convert('RGBA')
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            gh = int(H * 0.55)
            for i in range(gh):
                a = int(46 * (1 - i / gh))
                od.rectangle([0, H - gh + i, W, H - gh + i + 1], fill=(44, 62, 80, a))
            img = Image.alpha_composite(thumb, overlay).convert('RGB')

    # Accent lines (style.css top/bottom border)
    draw.rectangle([0, 0, W, 3], fill=OG_ACCENT)
    draw.rectangle([0, H - 3, W, H], fill=OG_ACCENT)

    # Badge top-right (style.css accent bg)
    badge = project.get("type", "photo").upper()
    try:
        bb = draw.textbbox((0, 0), " " + badge + " ", font=inter_s)
        bw, bh = bb[2] - bb[0], bb[3] - bb[1]
    except Exception:
        bw, bh = 80, 18
    bx, by = W - bw - 32, 16
    draw.rounded_rectangle([bx, by, bx + bw + 14, by + bh + 10], radius=4, fill=OG_ACCENT)
    draw.text((bx + 7, by + 5), " " + badge + " ", fill=OG_BG, font=inter_s)

    # Title bottom-left (style.css serif, dark text)
    title = project.get("title", "Untitled")
    year = project.get("year", "")
    yp = H - 120
    try:
        words = title.split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            tw = draw.textbbox((0, 0), test, font=brico)[2]
            if tw <= 750:
                cur = test
            else:
                if cur: lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        for line in lines[:2]:
            draw.text((32, yp), line, fill=OG_TEXT, font=brico)
            yp += 64
    except Exception:
        draw.text((32, yp), title[:50], fill=OG_TEXT, font=brico)
        yp += 64
    if year:
        draw.text((32, yp + 4), str(year), fill=OG_ACCENT, font=inter_m)

    # Logo top-left
    lp = Path("media/logo.png")
    if lp.exists():
        try:
            logo = Image.open(lp)
            if logo.mode == 'RGBA':
                logo.thumbnail((40, 40), Image.LANCZOS)
                img.paste(logo, (32, 20), logo)
            else:
                logo.thumbnail((40, 40), Image.LANCZOS)
                img.paste(logo, (32, 20))
        except Exception:
            pass
    draw.text((80, 28), "Jan Levínský", fill=OG_TEXT, font=inter_s)

    if output_path:
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, "PNG", optimize=True)
            return output_path
        except Exception:
            return None
    try:
        out = io.BytesIO()
        img.save(out, "PNG", optimize=True)
        out.seek(0)
        return out.read()
    except Exception:
        return None

def generate_main_og_image(output_path=None):
    """Main OG cover matching style.css — light theme with bento grid."""
    from PIL import ImageDraw

    brico, inter_m, inter_r, inter_s = _load_og_fonts()

    img = Image.new('RGB', (OG_WIDTH, OG_HEIGHT), OG_BG)
    draw = ImageDraw.Draw(img)

    all_thumbs = []
    for proj in data["projects"]:
        src = proj.get("thumbnail") or (proj.get("media", [{}])[0].get("thumbnail") if proj.get("media") else None) or (proj.get("media", [{}])[0].get("src") if proj.get("media") else None)
        if src:
            thumb = _load_thumbnail(src)
            if thumb:
                all_thumbs.append((thumb, proj.get("type", "photo") == "video"))

    tiles_to_show = all_thumbs[:6]
    if tiles_to_show:
        cols = 3 if len(tiles_to_show) >= 3 else len(tiles_to_show)
        rows = (len(tiles_to_show) + cols - 1) // cols
        tw = OG_WIDTH // cols
        th = OG_HEIGHT // rows
        for i, (t, is_vid) in enumerate(tiles_to_show):
            cx = (i % cols) * tw
            cy = (i // cols) * th
            _paste_thumb_tile(img, t, cx, cy, tw, th, is_vid, i)

    # Subtle top gradient overlay for readability
    for i in range(80):
        r = (1 - i / 80) ** 2
        draw.rectangle([0, i, OG_WIDTH, i + 1], fill=(250 - int(r * 8), 248 - int(r * 8), 245 - int(r * 8)))

    # Accent lines
    draw.rectangle([0, 0, OG_WIDTH, 3], fill=OG_ACCENT)
    draw.rectangle([0, OG_HEIGHT - 3, OG_WIDTH, OG_HEIGHT], fill=OG_ACCENT)

    # Name centered (style.css serif)
    name_text = "Jan Levínský"
    tb = draw.textbbox((0, 0), name_text, font=brico)
    tx = (OG_WIDTH - (tb[2] - tb[0])) // 2
    draw.text((tx, OG_HEIGHT // 2 - 60), name_text, fill=OG_TEXT, font=brico)

    # Subtitle (style.css accent)
    sub_text = "CINEMATOGRAPHY  &  PHOTOGRAPHY"
    tb = draw.textbbox((0, 0), sub_text, font=inter_m)
    sx = (OG_WIDTH - (tb[2] - tb[0])) // 2
    draw.text((sx, OG_HEIGHT // 2 + 20), sub_text, fill=OG_ACCENT, font=inter_m)

    # Count (style.css muted)
    count_text = f"{len(data['projects'])} projects"
    tb = draw.textbbox((0, 0), count_text, font=inter_r)
    cx2 = (OG_WIDTH - (tb[2] - tb[0])) // 2
    draw.text((cx2, OG_HEIGHT // 2 + 60), count_text, fill=OG_MUTED, font=inter_r)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG", optimize=True)
        return output_path
    output = io.BytesIO()
    img.save(output, "PNG", optimize=True)
    output.seek(0)
    return output.read()


# ═══════════════════════════════════════════════════════════════
# Validation
# ═══════════════════════════════════════════════════════════════

def find_case_insensitive_path(rel_path):
    parts = Path(rel_path).parts
    if not parts:
        return None
    current = Path(parts[0])
    if not current.exists():
        return None
    for part in parts[1:]:
        found = None
        for child in current.iterdir():
            if child.name.lower() == part.lower():
                found = child
                break
        if not found:
            return None
        current = found
    return str(current).replace("\\", "/")

def validate_projects():
    issues = []
    seen_ids = set()
    for i, project in enumerate(data["projects"]):
        proj_name = project.get("title", f"Projekt #{i+1}")
        pid = project.get("id")
        if pid is not None:
            if pid in seen_ids:
                issues.append({"type": "error", "project": proj_name, "message": f"Duplicitni ID: {pid}"})
            seen_ids.add(pid)
        if not project.get("title"):
            issues.append({"type": "warning", "project": proj_name, "message": "Chybi nazev projektu"})
        if not project.get("year"):
            issues.append({"type": "warning", "project": proj_name, "message": "Chybi rok"})
        for field in ["thumbnail", "full"]:
            path = project.get(field)
            if path:
                if not Path(path).exists():
                    ci = find_case_insensitive_path(path)
                    if ci:
                        issues.append({"type": "warning", "project": proj_name, "message": f"Case mismatch {field}: {path} -> {ci}"})
                    else:
                        issues.append({"type": "error", "project": proj_name, "message": f"Nefunkcni cesta: {path}"})
        for mi, media in enumerate(project.get("media", [])):
            src = media.get("src")
            if src:
                if not Path(src).exists():
                    ci = find_case_insensitive_path(src)
                    if ci:
                        issues.append({"type": "warning", "project": proj_name, "message": f"Case mismatch src: {src} -> {ci}"})
                    else:
                        issues.append({"type": "error", "project": proj_name, "message": f"Nefunkcni media src: {src}"})
            thumb = media.get("thumbnail")
            if thumb:
                if not Path(thumb).exists():
                    ci = find_case_insensitive_path(thumb)
                    if ci:
                        issues.append({"type": "warning", "project": proj_name, "message": f"Case mismatch thumb: {thumb} -> {ci}"})
                    else:
                        issues.append({"type": "warning", "project": proj_name, "message": f"Nefunkcni thumbnail: {thumb}"})
    return issues

def get_json_diff():
    if not JSON_FILE.exists():
        return "Soubor projects.json neexistuje."
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        saved = f.read()
    current = json.dumps(data["projects"], ensure_ascii=False, indent=2)
    if saved == current:
        return "Zadne zmeny."
    return f"ZMENENO: {len(current)} vs {len(saved)} znaku"


# ═══════════════════════════════════════════════════════════════
# Force WebP Convert
# ═══════════════════════════════════════════════════════════════

def find_all_image_files():
    image_files = []
    if not MEDIA_DIR.exists():
        return image_files
    for root, dirs, files in os.walk(MEDIA_DIR):
        for filename in files:
            filepath = Path(root) / filename
            if is_image_ext(filepath) and filepath.suffix.lower() != '.webp':
                image_files.append(filepath)
    return image_files

def convert_file_to_webp(filepath):
    try:
        with open(filepath, "rb") as f:
            image_bytes = f.read()
        webp_bytes, width, height = convert_to_webp(image_bytes, quality=WEBP_QUALITY, max_width=MAX_IMAGE_WIDTH)
        if not webp_bytes:
            return False, None, "Conversion failed"
        new_path = filepath.with_suffix('.webp')
        counter = 1
        while new_path.exists():
            new_path = filepath.parent / f"{filepath.stem}_{counter}.webp"
            counter += 1
        with open(new_path, "wb") as f:
            f.write(webp_bytes)
        filepath.unlink()
        return True, new_path, None
    except Exception as e:
        return False, None, str(e)

def update_json_paths(old_path, new_path):
    old_rel = str(old_path).replace('\\', '/')
    new_rel = str(new_path).replace('\\', '/')
    changed = False
    for project in data["projects"]:
        if project.get("thumbnail") and old_rel in project["thumbnail"]:
            project["thumbnail"] = project["thumbnail"].replace(old_rel, new_rel)
            changed = True
        if project.get("full") and old_rel in project["full"]:
            project["full"] = project["full"].replace(old_rel, new_rel)
            changed = True
        for media in project.get("media", []):
            if media.get("src") and old_rel in media["src"]:
                media["src"] = media["src"].replace(old_rel, new_rel)
                changed = True
            if media.get("thumbnail") and old_rel in media["thumbnail"]:
                media["thumbnail"] = media["thumbnail"].replace(old_rel, new_rel)
                changed = True
            if media.get("poster") and old_rel in media["poster"]:
                media["poster"] = media["poster"].replace(old_rel, new_rel)
                changed = True
    return changed

def process_force_convert():
    results = {"converted": [], "failed": [], "skipped": []}
    image_files = find_all_image_files()
    for filepath in image_files:
        if filepath.suffix.lower() == '.webp':
            results["skipped"].append(str(filepath))
            continue
        success, new_path, error = convert_file_to_webp(filepath)
        if success and new_path:
            json_changed = update_json_paths(filepath, new_path)
            results["converted"].append({"old": str(filepath), "new": str(new_path), "json_updated": json_changed})
        else:
            results["failed"].append({"file": str(filepath), "error": error})
    if results["converted"]:
        save_json()
    return results


# ═══════════════════════════════════════════════════════════════
# Normalize Project Filenames
# ═══════════════════════════════════════════════════════════════

def find_existing_project_folder(project):
    ptype = project.get("type", "photo")
    pyear = project.get("year", "unknown")
    ptitle = project.get("title", "untitled")
    expected = MEDIA_DIR / ptype / pyear / safe_folder_name(ptitle)
    if expected.exists():
        return expected
    base_dir = MEDIA_DIR / ptype / pyear
    if not base_dir.exists():
        return None
    for media in project.get("media", []):
        src = media.get("src", "")
        if src:
            src_path = Path(src)
            if len(src_path.parts) >= 4:
                folder_name = src_path.parts[3]
                candidate = base_dir / folder_name
                if candidate.exists():
                    return candidate
    for field in ["thumbnail", "full"]:
        path = project.get(field, "")
        if path:
            src_path = Path(path)
            if len(src_path.parts) >= 4:
                folder_name = src_path.parts[3]
                candidate = base_dir / folder_name
                if candidate.exists():
                    return candidate
    return None

def normalize_project_filenames():
    renamed = []

    for project in data["projects"]:
        ptype = project.get("type", "photo")
        pyear = project.get("year", "unknown")
        ptitle = project.get("title", "untitled")
        pid = project.get("id", 0)

        folder_path = find_existing_project_folder(project)
        if not folder_path or not folder_path.exists():
            continue

        safe_title = safe_folder_name(ptitle)
        new_folder_name = safe_title
        new_folder_path = MEDIA_DIR / ptype / pyear / new_folder_name

        old_folder_name = folder_path.name
        old_rel_prefix = f"media/{ptype}/{pyear}/{old_folder_name}"

        if folder_path != new_folder_path:
            if new_folder_path.exists():
                counter = 1
                while (MEDIA_DIR / ptype / pyear / f"{safe_title}_{counter}").exists():
                    counter += 1
                new_folder_name = f"{safe_title}_{counter}"
                new_folder_path = MEDIA_DIR / ptype / pyear / new_folder_name

            try:
                folder_path.rename(new_folder_path)
                renamed.append({
                    "type": "folder",
                    "old": old_folder_name,
                    "new": new_folder_name,
                    "project": ptitle
                })
                new_rel_prefix = f"media/{ptype}/{pyear}/{new_folder_name}"
                for p in data["projects"]:
                    if p.get("thumbnail") and old_rel_prefix in p["thumbnail"]:
                        p["thumbnail"] = p["thumbnail"].replace(old_rel_prefix, new_rel_prefix)
                    if p.get("full") and old_rel_prefix in p["full"]:
                        p["full"] = p["full"].replace(old_rel_prefix, new_rel_prefix)
                    for media in p.get("media", []):
                        if media.get("src") and old_rel_prefix in media["src"]:
                            media["src"] = media["src"].replace(old_rel_prefix, new_rel_prefix)
                        if media.get("thumbnail") and old_rel_prefix in media["thumbnail"]:
                            media["thumbnail"] = media["thumbnail"].replace(old_rel_prefix, new_rel_prefix)
                        if media.get("poster") and old_rel_prefix in media["poster"]:
                            media["poster"] = media["poster"].replace(old_rel_prefix, new_rel_prefix)
                    if p.get("og_image") and old_rel_prefix in p["og_image"]:
                        p["og_image"] = p["og_image"].replace(old_rel_prefix, new_rel_prefix)
                folder_path = new_folder_path
                old_rel_prefix = new_rel_prefix
            except Exception as e:
                print(f"[Normalize] Error renaming folder {old_folder_name}: {e}")
                continue

        new_rel_prefix = f"media/{ptype}/{pyear}/{new_folder_name}"

        if not folder_path.exists():
            continue

        files_in_folder = sorted([f for f in folder_path.iterdir() if f.is_file()])

        rename_plan = []
        used_names = set()
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        base_new_name = f"{safe_title}_{today}_{pid}"

        for fpath in files_in_folder:
            old_name = fpath.name
            ext = fpath.suffix.lower()
            stem = fpath.stem

            is_thumb = "_thumb" in stem.lower() or stem.endswith("_thumb")

            if is_thumb:
                new_name = f"{base_new_name}_thumb{ext}"
            else:
                new_name = f"{base_new_name}{ext}"

            counter = 1
            while new_name in used_names:
                if is_thumb:
                    new_name = f"{base_new_name}_{counter}_thumb{ext}"
                else:
                    new_name = f"{base_new_name}_{counter}{ext}"
                counter += 1

            used_names.add(new_name)

            if old_name != new_name:
                rename_plan.append({
                    "old_path": fpath,
                    "new_path": folder_path / new_name,
                    "old_name": old_name,
                    "new_name": new_name,
                    "old_rel": f"{new_rel_prefix}/{old_name}",
                    "new_rel": f"{new_rel_prefix}/{new_name}"
                })

        for plan in rename_plan:
            try:
                plan["old_path"].rename(plan["new_path"])
                renamed.append({
                    "type": "file",
                    "old": plan["old_name"],
                    "new": plan["new_name"],
                    "project": ptitle
                })
                old_rel = plan["old_rel"]
                new_rel = plan["new_rel"]
                for p in data["projects"]:
                    if p.get("thumbnail") and old_rel in p["thumbnail"]:
                        p["thumbnail"] = p["thumbnail"].replace(old_rel, new_rel)
                    if p.get("full") and old_rel in p["full"]:
                        p["full"] = p["full"].replace(old_rel, new_rel)
                    for media in p.get("media", []):
                        if media.get("src") and old_rel in media["src"]:
                            media["src"] = media["src"].replace(old_rel, new_rel)
                        if media.get("thumbnail") and old_rel in media["thumbnail"]:
                            media["thumbnail"] = media["thumbnail"].replace(old_rel, new_rel)
                        if media.get("poster") and old_rel in media["poster"]:
                            media["poster"] = media["poster"].replace(old_rel, new_rel)
                    if p.get("og_image") and old_rel in p["og_image"]:
                        p["og_image"] = p["og_image"].replace(old_rel, new_rel)
            except Exception as e:
                print(f"[Normalize] Error renaming file {plan['old_name']}: {e}")

    return renamed


# ═══════════════════════════════════════════════════════════════
# Sitemap & Deploy
# ═══════════════════════════════════════════════════════════════

def generate_sitemap():
    urls = []
    urls.append(f"  <url>\n    <loc>{SITE_URL}/</loc>\n    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>")
    urls.append(f"  <url>\n    <loc>{SITE_URL}/about.html</loc>\n    <changefreq>monthly</changefreq>\n    <priority>0.6</priority>\n  </url>")
    for project in data["projects"]:
        slug = slugify(project.get("title", ""))
        if slug:
            urls.append(f"  <url>\n    <loc>{SITE_URL}/project.html?id={project.get('id', '')}</loc>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>")
    sitemap = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n{chr(10).join(urls)}\n</urlset>"
    return sitemap

def git_deploy():
    try:
        if not Path(".git").exists():
            return False, "Git repository neexistuje. Inicializuj ho: git init"
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        if not result.stdout.strip():
            return True, "Zadne zmeny k deploy."
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        commit_msg = f"Update projects {ts}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
        push_result = subprocess.run(["git", "push"], capture_output=True, text=True)
        if push_result.returncode == 0:
            return True, f"Deploy hotov! {commit_msg}"
        else:
            return False, f"Push selhal: {push_result.stderr}"
    except subprocess.CalledProcessError as e:
        return False, f"Git chyba: {e.stderr if e.stderr else str(e)}"
    except FileNotFoundError:
        return False, "Git neni nainstalovan."
    except Exception as e:
        return False, f"Chyba: {str(e)}"


# ═══════════════════════════════════════════════════════════════
# Multipart Parser
# ═══════════════════════════════════════════════════════════════

def parse_multipart(body, boundary):
    boundary = boundary.encode() if isinstance(boundary, str) else boundary
    parts = body.split(b"--" + boundary)
    files = []
    fields = {}
    for part in parts[1:-1]:
        part = part.strip(b"\r\n")
        if not part:
            continue
        header_end = part.find(b"\r\n\r\n")
        if header_end == -1:
            continue
        headers = part[:header_end].decode("utf-8", errors="ignore")
        content = part[header_end + 4:]
        if content.endswith(b"\r\n"):
            content = content[:-2]
        filename = None
        name = None
        for line in headers.split("\r\n"):
            if line.lower().startswith("content-disposition:"):
                for item in line.split(";"):
                    item = item.strip()
                    if item.startswith("filename="):
                        filename = item[9:].strip('"')
                    elif item.startswith("name="):
                        name = item[5:].strip('"')
        if filename and content:
            files.append({"name": name, "filename": filename, "content": content})
        elif name and content:
            fields[name] = content.decode("utf-8", errors="ignore")
    return files, fields


# ═══════════════════════════════════════════════════════════════
# Editor HTML
# ═══════════════════════════════════════════════════════════════

def load_editor_html():
    if HTML_FILE.exists():
        return HTML_FILE.read_text(encoding="utf-8")
    return "<h1>Chyba: builder.html nenalezen</h1><p>Uloz builder.html vedle builder.py</p>"

EDITOR_HTML = load_editor_html()


# ═══════════════════════════════════════════════════════════════
# HTTP Server
# ═══════════════════════════════════════════════════════════════

class Handler(SimpleHTTPRequestHandler):

    # --- Logging ---
    def log_message(self, format, *args):
        pass

    # --- Response Helpers ---
    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def send_json(self, obj, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def send_xml(self, xml, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/xml; charset=utf-8")
        self.end_headers()
        self.wfile.write(xml.encode("utf-8"))

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()

    # --- GET Handlers ---
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            self.send_html(EDITOR_HTML)
        elif path == "/api/projects":
            self.send_json(data["projects"])
        elif path == "/api/tech":
            self.send_json(tech_inventory)
        elif path == "/api/validate":
            self.send_json(validate_projects())
        elif path == "/api/diff":
            self.send_json({"diff": get_json_diff()})
        elif path == "/api/sitemap":
            self.send_xml(generate_sitemap())
        elif path == "/api/generate-main-og":
            self.handle_generate_main_og()
        else:
            super().do_GET()

    # --- POST Handlers ---
    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/api/save":
            self.handle_save()
        elif path == "/api/upload":
            self.handle_upload()
        elif path == "/api/force-convert":
            self.handle_force_convert()
        elif path == "/api/undo":
            self.handle_undo()
        elif path == "/api/redo":
            self.handle_redo()
        elif path == "/api/bulk-delete":
            self.handle_bulk_delete()
        elif path == "/api/bulk-gear":
            self.handle_bulk_gear()
        elif path == "/api/bulk-year":
            self.handle_bulk_year()
        elif path == "/api/generate-lqip":
            self.handle_generate_lqip()
        elif path == "/api/generate-simple-og":
            self.handle_generate_simple_og()
        elif path == "/api/deploy":
            self.handle_deploy()
        elif path == "/api/normalize-filenames":
            self.handle_normalize_filenames()
        else:
            self.send_response(404)
            self.end_headers()

    # --- POST Handler Implementations ---
    def handle_save(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        try:
            new_data = json.loads(body)
            push_undo_state()
            data["projects"] = new_data
            save_json()
            self.send_json({"ok": True})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)}, 400)

    def handle_upload(self):
        content_type = self.headers.get("Content-Type", "")
        if "boundary=" not in content_type:
            self.send_json({"ok": False, "error": "No boundary"}, 400)
            return
        boundary = content_type.split("boundary=")[1].strip('"')
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len)
        files, fields = parse_multipart(body, boundary)
        file_parts = [f for f in files if f.get('name') and (f['name'].startswith('file_') or f['name'] == 'files')]
        thumb_parts = {f['name']: f for f in files if f.get('name') and f['name'].startswith('thumb_')}
        ptype = fields.get("project_type", "photo")
        pyear = fields.get("project_year", "unknown")
        ptitle = fields.get("project_title", "untitled")
        sub_dir = MEDIA_DIR / ptype / pyear / safe_folder_name(ptitle)
        sub_dir.mkdir(parents=True, exist_ok=True)
        saved = []
        for f in file_parts:
            filename = Path(f["filename"]).name
            if not filename:
                continue
            filename = normalize_filename(filename)
            original_stem = Path(filename).stem
            original_suffix = Path(filename).suffix.lower()
            should_convert_webp = is_image_ext(filename)
            is_video_file = is_video_ext(filename)
            if should_convert_webp:
                webp_stem = original_stem
                dest = sub_dir / f"{webp_stem}.webp"
                counter = 1
                while dest.exists():
                    dest = sub_dir / f"{webp_stem}_{counter}.webp"
                    counter += 1
                webp_bytes, img_width, img_height = convert_to_webp(f["content"], quality=WEBP_QUALITY, max_width=MAX_IMAGE_WIDTH)
                if webp_bytes:
                    with open(dest, "wb") as out:
                        out.write(webp_bytes)
                    ftype = "photo"
                    rel = f"media/{ptype}/{pyear}/{safe_folder_name(ptitle)}/{dest.name}"
                    lqip = generate_lqip(f["content"], width=LQIP_WIDTH, quality=LQIP_QUALITY, blur=LQIP_BLUR)
                    thumb_bytes, thumb_w, thumb_h = generate_webp_thumbnail(f["content"], quality=WEBP_THUMB_QUALITY, max_width=MAX_THUMB_WIDTH)
                    if thumb_bytes:
                        thumb_name = f"{webp_stem}_thumb.webp"
                        thumb_dest = sub_dir / thumb_name
                        thumb_counter = 1
                        while thumb_dest.exists():
                            thumb_dest = sub_dir / f"{webp_stem}_thumb_{thumb_counter}.webp"
                            thumb_counter += 1
                        with open(thumb_dest, "wb") as out:
                            out.write(thumb_bytes)
                        thumb_rel = f"media/{ptype}/{pyear}/{safe_folder_name(ptitle)}/{thumb_dest.name}"
                    else:
                        thumb_rel = rel
                else:
                    dest = sub_dir / filename
                    counter = 1
                    while dest.exists():
                        dest = sub_dir / f"{original_stem}_{counter}{original_suffix}"
                        counter += 1
                    with open(dest, "wb") as out:
                        out.write(f["content"])
                    ftype = "photo"
                    rel = f"media/{ptype}/{pyear}/{safe_folder_name(ptitle)}/{dest.name}"
                    thumb_rel = rel
                    lqip = None
            elif is_video_file:
                dest = sub_dir / filename
                counter = 1
                while dest.exists():
                    dest = sub_dir / f"{original_stem}_{counter}{original_suffix}"
                    counter += 1
                with open(dest, "wb") as out:
                    out.write(f["content"])
                ftype = "video"
                rel = f"media/{ptype}/{pyear}/{safe_folder_name(ptitle)}/{dest.name}"
                thumb_key = f"thumb_{f['name'].split('_', 1)[1]}" if f['name'].startswith('file_') else None
                thumb_source = thumb_parts.get(thumb_key)
                if thumb_source:
                    thumb_stem = original_stem
                    thumb_name = f"{thumb_stem}_thumb.webp"
                    thumb_dest = sub_dir / thumb_name
                    thumb_counter = 1
                    while thumb_dest.exists():
                        thumb_dest = sub_dir / f"{thumb_stem}_thumb_{thumb_counter}.webp"
                        thumb_counter += 1
                    thumb_bytes, _, _ = convert_to_webp(thumb_source["content"], quality=WEBP_THUMB_QUALITY, max_width=MAX_THUMB_WIDTH)
                    if thumb_bytes:
                        with open(thumb_dest, "wb") as out:
                            out.write(thumb_bytes)
                        thumb_rel = f"media/{ptype}/{pyear}/{safe_folder_name(ptitle)}/{thumb_dest.name}"
                    else:
                        thumb_name = f"{thumb_stem}_thumb.jpg"
                        thumb_dest = sub_dir / thumb_name
                        thumb_counter = 1
                        while thumb_dest.exists():
                            thumb_dest = sub_dir / f"{thumb_stem}_thumb_{thumb_counter}.jpg"
                            thumb_counter += 1
                        with open(thumb_dest, "wb") as out:
                            out.write(thumb_source["content"])
                        thumb_rel = f"media/{ptype}/{pyear}/{safe_folder_name(ptitle)}/{thumb_dest.name}"
                elif generate_video_thumbnail(dest, sub_dir / f"{original_stem}_thumb.jpg", seek_time=3.0):
                    jpg_thumb = sub_dir / f"{original_stem}_thumb.jpg"
                    if jpg_thumb.exists():
                        webp_thumb = sub_dir / f"{original_stem}_thumb.webp"
                        try:
                            with open(jpg_thumb, "rb") as jf:
                                jpg_bytes = jf.read()
                            thumb_bytes, _, _ = convert_to_webp(jpg_bytes, quality=WEBP_THUMB_QUALITY, max_width=MAX_THUMB_WIDTH)
                            if thumb_bytes:
                                with open(webp_thumb, "wb") as wf:
                                    wf.write(thumb_bytes)
                                thumb_rel = f"media/{ptype}/{pyear}/{safe_folder_name(ptitle)}/{webp_thumb.name}"
                                jpg_thumb.unlink(missing_ok=True)
                            else:
                                thumb_rel = f"media/{ptype}/{pyear}/{safe_folder_name(ptitle)}/{jpg_thumb.name}"
                        except Exception:
                            thumb_rel = f"media/{ptype}/{pyear}/{safe_folder_name(ptitle)}/{jpg_thumb.name}"
                    else:
                        thumb_rel = rel
                else:
                    thumb_rel = rel
                lqip = None
            else:
                dest = sub_dir / filename
                counter = 1
                while dest.exists():
                    dest = sub_dir / f"{original_stem}_{counter}{original_suffix}"
                    counter += 1
                with open(dest, "wb") as out:
                    out.write(f["content"])
                ftype = "photo"
                rel = f"media/{ptype}/{pyear}/{safe_folder_name(ptitle)}/{dest.name}"
                thumb_rel = rel
                lqip = None

            saved.append({
                "filename": dest.name,
                "rel_path": rel,
                "type": ftype,
                "thumbnail": thumb_rel,
                "lqip": lqip
            })
        self.send_json({"ok": True, "files": saved})

    def handle_undo(self):
        if undo():
            save_json()
            self.send_json({"ok": True, "message": "Undo provedeno"})
        else:
            self.send_json({"ok": False, "error": "Neni co undo"})

    def handle_redo(self):
        if redo():
            save_json()
            self.send_json({"ok": True, "message": "Redo provedeno"})
        else:
            self.send_json({"ok": False, "error": "Neni co redo"})

    def handle_bulk_delete(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        try:
            indices = json.loads(body)
            push_undo_state()
            for idx in sorted(indices, reverse=True):
                if 0 <= idx < len(data["projects"]):
                    data["projects"].pop(idx)
            save_json()
            self.send_json({"ok": True, "deleted": len(indices)})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)}, 400)

    def handle_bulk_gear(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        try:
            payload = json.loads(body)
            indices = payload.get("indices", [])
            category = payload.get("category", "")
            item = payload.get("item", "")
            action = payload.get("action", "add")
            push_undo_state()
            for idx in indices:
                if 0 <= idx < len(data["projects"]):
                    project = data["projects"][idx]
                    if not project.get("gear"):
                        project["gear"] = {}
                    if category not in project["gear"]:
                        project["gear"][category] = []
                    if action == "add" and item not in project["gear"][category]:
                        project["gear"][category].append(item)
                    elif action == "remove" and item in project["gear"][category]:
                        project["gear"][category].remove(item)
            save_json()
            self.send_json({"ok": True, "message": f"Gear {action} pro {len(indices)} projektu"})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)}, 400)

    def handle_bulk_year(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        try:
            payload = json.loads(body)
            indices = payload.get("indices", [])
            new_year = payload.get("year", "")
            push_undo_state()
            for idx in indices:
                if 0 <= idx < len(data["projects"]):
                    data["projects"][idx]["year"] = new_year
            save_json()
            self.send_json({"ok": True, "message": f"Rok zmenen na {new_year} pro {len(indices)} projektu"})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)}, 400)

    def handle_generate_lqip(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        try:
            payload = json.loads(body)
            project_idx = payload.get("project_idx", -1)
            media_idx = payload.get("media_idx", -1)
            if project_idx < 0 or project_idx >= len(data["projects"]):
                self.send_json({"ok": False, "error": "Neplatny projekt"})
                return
            project = data["projects"][project_idx]
            media_list = project.get("media", [])
            generated = 0
            if media_idx < 0:
                for m in media_list:
                    src = m.get("src")
                    if src and Path(src).exists() and is_image_file(src):
                        lqip = generate_lqip_for_file(src)
                        if lqip:
                            m["lqip"] = lqip
                            generated += 1
            else:
                if media_idx < len(media_list):
                    m = media_list[media_idx]
                    src = m.get("src")
                    if src and Path(src).exists() and is_image_file(src):
                        lqip = generate_lqip_for_file(src)
                        if lqip:
                            m["lqip"] = lqip
                            generated = 1
            save_json()
            self.send_json({"ok": True, "generated": generated})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)}, 400)

    def handle_generate_simple_og(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        try:
            payload = json.loads(body)
            project_idx = payload.get("project_idx", -1)
            if project_idx < 0 or project_idx >= len(data["projects"]):
                self.send_json({"ok": False, "error": "Neplatny projekt"})
                return
            project = data["projects"][project_idx]
            ptype = project.get("type", "photo")
            pyear = project.get("year", "unknown")
            ptitle = project.get("title", "untitled")
            sub_dir = MEDIA_DIR / ptype / pyear / safe_folder_name(ptitle)
            sub_dir.mkdir(parents=True, exist_ok=True)
            output_path = sub_dir / "og-image.png"
            result = generate_simple_og_image(project, output_path)
            if result:
                rel_path = f"media/{ptype}/{pyear}/{safe_folder_name(ptitle)}/og-image.png"
                project["og_image"] = rel_path
                save_json()
                self.send_json({"ok": True, "path": rel_path})
            else:
                self.send_json({"ok": False, "error": "Generation failed"})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)}, 400)

    def handle_deploy(self):
        success, message = git_deploy()
        if success:
            self.send_json({"ok": True, "message": message})
        else:
            self.send_json({"ok": False, "error": message}, 500)

    def handle_force_convert(self):
        try:
            results = process_force_convert()
            self.send_json({
                "ok": True,
                "message": f"Konvertovano {len(results['converted'])} souboru, {len(results['failed'])} selhalo, {len(results['skipped'])} preskoceno",
                "results": results
            })
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)}, 500)

    def handle_normalize_filenames(self):
        try:
            push_undo_state()
            renamed = normalize_project_filenames()
            if renamed:
                save_json()
            folder_count = sum(1 for r in renamed if r["type"] == "folder")
            file_count = sum(1 for r in renamed if r["type"] == "file")
            self.send_json({
                "ok": True,
                "message": f"Prejmenovano {folder_count} slozek a {file_count} souboru",
                "renamed": renamed,
                "folder_count": folder_count,
                "file_count": file_count
            })
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)}, 500)

    def handle_generate_main_og(self):
        try:
            output_path = MEDIA_DIR / "og-cover.png"
            result = generate_main_og_image(output_path)
            if result:
                self.send_json({"ok": True, "path": str(output_path)})
            else:
                self.send_json({"ok": False, "error": "Generation failed"})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)}, 500)


# ═══════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════

def main():
    global tech_inventory
    load_json()
    tech_inventory = load_tech_inventory()
    save_json()

    server = HTTPServer(("127.0.0.1", PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    url = f"http://localhost:{PORT}"
    print("=" * 50)
    print(f"  Projects Builder bezi na {url}")
    print(f"  Nacteno z Kamera.md: {len(tech_inventory.get('camera', []))} kamer")
    print(f"  Nacteno z Optika.md: {len(tech_inventory.get('lenses', []))} objektivu, {len(tech_inventory.get('filter', []))} filtru")
    print("=" * 50)

    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        while True:
            __import__('time').sleep(1)
    except KeyboardInterrupt:
        print("\nUkoncuji...")
        server.shutdown()

if __name__ == "__main__":
    main()
