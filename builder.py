#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
projects_builder.py — Editor pro projects.json s auto-strukturou složek
======================================================================
Ulož vedle index.html, project.html, projects.json, Kamera.md a Optika.md.
Spusť: python projects_builder.py
Otevři: http://localhost:8765
"""

import json
import os
import re
import shutil
import subprocess
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# ─── CONFIG ──────────────────────────────────────────────────────────
PORT = 8765
JSON_FILE = Path("projects.json")
MEDIA_DIR = Path("media")
BACKUP_DIR = Path(".builder_backups")
KAMERA_MD = Path("./gear/Kamera.md")
OPTIKA_MD = Path("./gear/Optika.md")

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

# ─── PARSE TECHNIKA ────────────────────────────────────────────────────
def load_tech_inventory():
    inv = {}
    # Kamera.md
    if KAMERA_MD.exists():
        with open(KAMERA_MD, "r", encoding="utf-8") as f:
            text = f.read()
        sections = re.split(r'\n#+\s*', text)
        for sec in sections:
            sec_title = sec.split('\n')[0].strip().lower() if sec else ''
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
                            if name and name.lower() not in ("název", "name", "nazev", ""):
                                if "foto" in sec_title or "photo" in sec_title:
                                    inv.setdefault("camera", []).append(name)
                                elif "video" in sec_title:
                                    inv.setdefault("camera", []).append(name)
    # Optika.md
    if OPTIKA_MD.exists():
        with open(OPTIKA_MD, "r", encoding="utf-8") as f:
            text = f.read()
        sections = re.split(r'\n#+\s*', text)
        for sec in sections:
            sec_title = sec.split('\n')[0].strip().lower() if sec else ''
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
                            if name and name.lower() not in ("název", "name", "nazev", ""):
                                if "objektiv" in sec_title or "lens" in sec_title or "optika" in sec_title:
                                    inv.setdefault("lenses", []).append(name)
                                elif "filtr" in sec_title or "filter" in sec_title:
                                    inv.setdefault("filter", []).append(name)
    # deduplikace
    for k in inv:
        seen = set()
        dedup = []
        for item in inv[k]:
            if item not in seen:
                seen.add(item)
                dedup.append(item)
        inv[k] = dedup
    return inv

# ─── DATA ──────────────────────────────────────────────────────────────
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
        import datetime
        ts = datetime.datetime.now().strftime("%H%M%S")
        shutil.copy(JSON_FILE, BACKUP_DIR / f"projects_{ts}.json")
    MEDIA_DIR.mkdir(exist_ok=True)
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data["projects"], f, ensure_ascii=False, indent=2)

def safe_folder_name(s):
    s = re.sub(r'[\\/:*?"<>|]', "", str(s))
    s = s.strip().replace(" ", "-")
    return s or "projekt"

# ─── MULTIPART PARSER ──────────────────────────────────────────────────
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
        content = part[header_end + 4 :]
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

def is_video_ext(path):
    return Path(path).suffix.lower() in (".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v")

def generate_video_thumbnail(source_path, thumb_path, seek_time=3.0):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    try:
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            ffmpeg,
            "-hide_banner",
            "-loglevel", "error",
            "-ss", str(seek_time),
            "-i", str(source_path),
            "-frames:v", "1",
            "-q:v", "2",
            "-y",
            str(thumb_path)
        ], check=True)
        return thumb_path.exists()
    except Exception:
        return False

# ─── HTTP SERVER ───────────────────────────────────────────────────────
class Handler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            self.send_html(EDITOR_HTML)
        elif path == "/api/projects":
            self.send_json(data["projects"])
        elif path == "/api/tech":
            self.send_json(tech_inventory)
        else:
            super().do_GET()

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/api/save":
            self.handle_save()
        elif path == "/api/upload":
            self.handle_upload()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_save(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        try:
            new_data = json.loads(body)
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

            dest = sub_dir / filename
            stem = Path(filename).stem
            suffix = Path(filename).suffix
            counter = 1
            while dest.exists():
                dest = sub_dir / f"{stem}_{counter}{suffix}"
                counter += 1

            with open(dest, "wb") as out:
                out.write(f["content"])

            ext = suffix.lower()
            if ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif", ".svg"):
                ftype = "photo"
            elif ext in (".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v"):
                ftype = "video"
            else:
                ftype = "photo"

            rel = f"media/{ptype}/{pyear}/{safe_folder_name(ptitle)}/{dest.name}"
            thumb_rel = rel
            if ftype == "video":
                thumb_key = f"thumb_{f['name'].split('_', 1)[1]}" if f['name'].startswith('file_') else None
                thumb_source = thumb_parts.get(thumb_key)
                if thumb_source:
                    thumb_name = f"{stem}_thumb.jpg"
                    thumb_dest = sub_dir / thumb_name
                    thumb_counter = 1
                    while thumb_dest.exists():
                        thumb_dest = sub_dir / f"{stem}_thumb_{thumb_counter}.jpg"
                        thumb_counter += 1
                    with open(thumb_dest, "wb") as out:
                        out.write(thumb_source["content"])
                    thumb_rel = f"media/{ptype}/{pyear}/{safe_folder_name(ptitle)}/{thumb_dest.name}"
                elif generate_video_thumbnail(dest, sub_dir / f"{stem}_thumb.jpg", seek_time=3.0):
                    thumb_rel = f"media/{ptype}/{pyear}/{safe_folder_name(ptitle)}/{stem}_thumb.jpg"
                else:
                    thumb_rel = rel

            saved.append({
                "filename": dest.name,
                "rel_path": rel,
                "type": ftype,
                "thumbnail": thumb_rel
            })

        self.send_json({"ok": True, "files": saved})

    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def send_json(self, obj, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()

# ─── EDITOR UI ─────────────────────────────────────────────────────────
EDITOR_HTML = r'''<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Projects Builder</title>
<style>
:root{
  --bg:#0c0c0c;--bg2:#141414;--surface:#1e1e1e;--surface2:#282828;
  --text:#e8e6e3;--muted:#8a8580;--accent:#c4956a;--accent2:#d4a87a;
  --danger:#c45a5a;--ok:#5a9e6e;--r:8px;--gap:12px;
  font-family:'Inter',system-ui,sans-serif;font-size:13px;color:var(--text);
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);min-height:100vh;display:flex;flex-direction:column}

header{
  background:var(--surface);border-bottom:1px solid #333;
  padding:12px 20px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;
}
header h1{font-family:'Bricolage Grotesque',Georgia,serif;font-size:20px;font-weight:400;color:var(--accent)}
header .spacer{flex:1}
.btn{
  background:var(--surface2);border:1px solid #444;color:var(--text);
  padding:7px 14px;border-radius:var(--r);cursor:pointer;font-size:12px;
  transition:all .15s;display:inline-flex;align-items:center;gap:6px;
}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.btn.primary{background:var(--accent);color:#111;border-color:var(--accent);font-weight:600}
.btn.primary:hover{background:var(--accent2)}
.btn.danger{color:var(--danger);border-color:var(--danger)}
.btn.danger:hover{background:rgba(196,90,90,.1)}
.btn:disabled{opacity:.4;cursor:not-allowed}
.status{font-size:11px;color:var(--muted);margin-left:auto}

.wrap{display:flex;flex:1;overflow:hidden}
.sidebar{
  width:300px;background:var(--bg2);border-right:1px solid #333;
  display:flex;flex-direction:column;overflow:hidden;
}
.sidebar .head{
  padding:12px 16px;border-bottom:1px solid #333;
  display:flex;align-items:center;gap:8px;
}
.project-list{flex:1;overflow-y:auto;padding:8px}
.project-item{
  padding:10px 12px;border-radius:var(--r);cursor:pointer;
  border:1px solid transparent;transition:all .15s;
  display:flex;align-items:center;gap:10px;margin-bottom:4px;
}
.project-item:hover{background:var(--surface)}
.project-item.active{background:var(--surface);border-color:var(--accent)}
.project-item .num{color:var(--muted);font-size:11px;min-width:24px}
.project-item .title{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:13px}
.project-item .type{font-size:10px;text-transform:uppercase;color:var(--muted);background:var(--bg2);padding:2px 8px;border-radius:4px}

.main{flex:1;display:flex;flex-direction:column;overflow:hidden}
.form-area{flex:1;overflow-y:auto;padding:24px}
.form-grid{
  display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:var(--gap);max-width:900px;
}
.field{display:flex;flex-direction:column;gap:5px}
.field label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:500}
.field input,.field select,.field textarea{
  background:var(--surface);border:1px solid #444;color:var(--text);
  padding:9px 11px;border-radius:var(--r);font-size:13px;font-family:inherit;
  outline:none;transition:border-color .15s;width:100%;
}
.field input:focus,.field select:focus,.field textarea:focus{border-color:var(--accent)}
.field textarea{resize:vertical;min-height:70px}

.section-title{
  font-size:12px;text-transform:uppercase;letter-spacing:.12em;color:var(--accent);
  margin:28px 0 14px;padding-bottom:8px;border-bottom:1px solid #333;max-width:900px;
}

.media-toolbar{
  display:flex;gap:10px;align-items:center;margin-bottom:14px;flex-wrap:wrap;max-width:900px;
}

.media-list{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;max-width:900px;
}
.media-card{
  background:var(--surface);border:1px solid #444;border-radius:var(--r);
  overflow:hidden;display:flex;flex-direction:column;
}
.media-card .thumb{
  height:140px;background:var(--bg2);position:relative;overflow:hidden;
  display:flex;align-items:center;justify-content:center;
}
.media-card .thumb img,.media-card .thumb video{
  max-width:100%;max-height:100%;object-fit:cover;display:block;
}
.media-card .thumb .badge{
  position:absolute;top:8px;left:8px;background:rgba(0,0,0,.7);
  color:#fff;font-size:10px;text-transform:uppercase;padding:3px 8px;border-radius:4px;
  letter-spacing:.05em;
}
.media-card .body{padding:12px;display:flex;flex-direction:column;gap:8px}
.media-card .body .field{margin:0}
.media-card .body input,.media-card .body select{
  background:var(--bg2);padding:6px 8px;font-size:12px;
}
.media-card .actions{
  display:flex;gap:6px;padding:0 12px 12px;
}
.media-card .actions .btn{font-size:11px;padding:5px 10px;flex:1;justify-content:center}

.empty{color:var(--muted);font-style:italic;padding:20px;text-align:center}

.toast{
  position:fixed;bottom:20px;right:20px;background:var(--surface2);
  border:1px solid var(--accent);color:var(--text);padding:10px 16px;
  border-radius:var(--r);font-size:12px;opacity:0;transform:translateY(10px);
  transition:all .3s;pointer-events:none;z-index:100;
}
.toast.show{opacity:1;transform:translateY(0)}

.drop-zone{
  border:2px dashed #444;border-radius:var(--r);padding:24px;text-align:center;
  color:var(--muted);transition:all .2s;cursor:pointer;margin-bottom:14px;max-width:900px;
}
.drop-zone:hover,.drop-zone.dragover{border-color:var(--accent);color:var(--accent);background:rgba(196,149,106,.05)}
.drop-zone span{display:block;font-size:20px;margin-bottom:8px}

.upload-progress{
  max-width:900px;margin-bottom:14px;display:none;
}
.upload-progress.active{display:block}
.upload-progress-bar{
  height:4px;background:var(--surface);border-radius:var(--r);overflow:hidden;
}
.upload-progress-fill{
  height:100%;background:var(--accent);width:0%;transition:width .3s;
}

/* Gear */
.gear-grid{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;max-width:900px;
}
.gear-cat{
  background:var(--surface);border:1px solid #444;border-radius:var(--r);padding:12px;
}
.gear-cat > label{
  font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--accent);
  display:block;margin-bottom:10px;font-weight:600;
}
.gear-add-row{
  display:flex;gap:6px;margin-bottom:10px;
}
.gear-add-row select{
  flex:1;background:var(--bg2);border:1px solid #444;padding:6px 8px;border-radius:6px;
  color:var(--text);font-size:12px;outline:none;transition:border-color .15s;
}
.gear-add-row select:focus{border-color:var(--accent)}
.gear-row{
  display:flex;gap:6px;margin-bottom:6px;align-items:center;
}
.gear-row input{
  flex:1;background:var(--bg2);border:1px solid #444;padding:6px 8px;border-radius:6px;
  color:var(--text);font-size:12px;outline:none;transition:border-color .15s;
}
.gear-row input:focus{border-color:var(--accent)}
.gear-row .btn{
  padding:4px 8px;font-size:11px;min-width:32px;justify-content:center;
}
</style>
</head>
<body>
<header>
  <h1>Projects Builder</h1>
  <div class="spacer"></div>
  <button class="btn" onclick="addProject()">+ Nový projekt</button>
  <button class="btn danger" onclick="deleteProject()">🗑 Smazat</button>
  <button class="btn" onclick="duplicateProject()">⎘ Duplikovat</button>
  <button class="btn primary" onclick="saveNow()">💾 Uložit</button>
  <span class="status" id="status">Načítání…</span>
</header>
<div class="wrap">
  <aside class="sidebar">
    <div class="head">
      <span style="font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)">Projekty</span>
      <span class="spacer"></span>
      <span id="count" style="font-size:11px;color:var(--muted)">0</span>
    </div>
    <div class="project-list" id="projectList"></div>
  </aside>
  <div class="main">
    <div class="form-area" id="formArea">
      <div class="empty">Vyber projekt vlevo</div>
    </div>
  </div>
</div>
<div class="toast" id="toast">Uloženo</div>

<script>
const GEAR_CATS = ["camera","lenses","gimbal/stabilization","lighting","audio","software","color","drone","filter","tripod","monitor","recorder"];
const GEAR_LABELS = {
  "camera":"Camera",
  "lenses":"Lenses",
  "gimbal/stabilization":"Gimbal / Stabilization",
  "lighting":"Lighting",
  "audio":"Audio",
  "software":"Software",
  "color":"Color",
  "drone":"Drone",
  "filter":"Filter",
  "tripod":"Tripod",
  "monitor":"Monitor",
  "recorder":"Recorder"
};
const GEAR_DROPDOWN_MAP = {
  "camera":"camera",
  "lenses":"lenses",
  "filter":"filter"
};
let projects = [];
let activeIdx = -1;
let techInventory = {};

async function load(){
  const [pr, tr] = await Promise.all([fetch('/api/projects'), fetch('/api/tech')]);
  projects = await pr.json();
  techInventory = await tr.json();
  renderList();
  setStatus('Připraveno');
  if(projects.length) select(0);
}
load();

function setStatus(t){ document.getElementById('status').textContent = t; }
function showToast(t){
  const el = document.getElementById('toast');
  el.textContent = t; el.classList.add('show');
  setTimeout(()=>el.classList.remove('show'),2500);
}

function renderList(){
  const list = document.getElementById('projectList');
  list.innerHTML = '';
  projects.forEach((p,i)=>{
    const div = document.createElement('div');
    div.className = 'project-item' + (i===activeIdx?' active':'');
    div.innerHTML = `<span class="num">${i+1}</span><span class="title">${esc(p.title||'Bez názvu')}</span><span class="type">${p.type||'?'}</span>`;
    div.onclick = ()=>select(i);
    list.appendChild(div);
  });
  document.getElementById('count').textContent = projects.length;
}

function select(i){
  activeIdx = i;
  renderList();
  renderForm();
}

function esc(s){ return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }

function ensureGear(p){
  if(!p.gear) p.gear = {};
  GEAR_CATS.forEach(c=>{ if(!p.gear[c]) p.gear[c] = []; });
}

function renderForm(){
  const area = document.getElementById('formArea');
  if(activeIdx<0){ area.innerHTML='<div class="empty">Vyber projekt</div>'; return; }
  const p = projects[activeIdx];
  ensureGear(p);

  let mediaHtml = '';
  (p.media||[]).forEach((m,mi)=>{
    const thumb = m.thumbnail || m.src || '';
    const isVideo = m.type === 'video';
    const thumbTag = isVideo 
      ? `<video src="${esc(thumb)}" muted preload="metadata"></video>`
      : `<img src="${esc(thumb)}" alt="" onerror="this.style.display='none'">`;
    
    mediaHtml += `
    <div class="media-card">
      <div class="thumb">
        ${thumbTag}
        <span class="badge">${m.type||'?'}</span>
      </div>
      <div class="body">
        <div class="field">
          <label>Typ</label>
          <select onchange="setMedia(${mi},'type',this.value)">
            <option value="photo" ${m.type==='photo'?'selected':''}>Photo</option>
            <option value="video" ${m.type==='video'?'selected':''}>Video</option>
          </select>
        </div>
        <div class="field">
          <label>Src (cesta/URL)</label>
          <input type="text" value="${esc(m.src||'')}" onchange="setMedia(${mi},'src',this.value)">
        </div>
        <div class="field">
          <label>Thumbnail / Poster</label>
          <input type="text" value="${esc(m.thumbnail||m.poster||'')}" onchange="setMedia(${mi},'thumbnail',this.value)">
        </div>
        <div class="field">
          <label>Titulek</label>
          <input type="text" value="${esc(m.title||'')}" onchange="setMedia(${mi},'title',this.value)">
        </div>
        <div class="field">
          <label>Caption</label>
          <input type="text" value="${esc(m.caption||'')}" onchange="setMedia(${mi},'caption',this.value)">
        </div>
      </div>
      <div class="actions">
        <button class="btn" onclick="moveMedia(${mi},-1)">↑</button>
        <button class="btn" onclick="moveMedia(${mi},1)">↓</button>
        <button class="btn danger" onclick="deleteMedia(${mi})">Smazat</button>
      </div>
    </div>`;
  });

  let gearHtml = '';
  GEAR_CATS.forEach(cat=>{
    const items = p.gear[cat] || [];
    const invKey = GEAR_DROPDOWN_MAP[cat];
    const inventory = (invKey && techInventory[invKey]) ? techInventory[invKey] : [];
    
    let addSection = '';
    if(inventory.length){
      let opts = `<option value="">— vyber z inventáře —</option>`;
      inventory.forEach(it=>{
        opts += `<option value="${esc(it)}">${esc(it)}</option>`;
      });
      addSection = `<div class="gear-add-row">
        <select id="gear-add-${cat}">
          ${opts}
        </select>
        <button class="btn" onclick="addGearFromSelect('${cat}')">+ Přidat</button>
      </div>`;
    }
    
    let rows = '';
    items.forEach((item,idx)=>{
      rows += `<div class="gear-row">
        <input type="text" value="${esc(item)}" onchange="updateGear('${cat}',${idx},this.value)">
        <button class="btn danger" onclick="removeGear('${cat}',${idx})">×</button>
      </div>`;
    });
    
    gearHtml += `<div class="gear-cat">
      <label>${GEAR_LABELS[cat]||cat}</label>
      ${addSection}
      ${rows}
      <button class="btn" style="width:100%;margin-top:4px" onclick="addGear('${cat}')">+ Přidat ručně</button>
    </div>`;
  });

  area.innerHTML = `
    <div class="section-title">Projekt: ${esc(p.title||'Bez názvu')}</div>
    <div class="form-grid">
      <div class="field"><label>ID</label><input type="number" value="${p.id||''}" onchange="set('id',parseInt(this.value)||0)"></div>
      <div class="field"><label>Název</label><input type="text" value="${esc(p.title||'')}" onchange="set('title',this.value)"></div>
      <div class="field">
        <label>Typ projektu</label>
        <select onchange="set('type',this.value)">
          <option value="photo" ${p.type==='photo'?'selected':''}>Photo</option>
          <option value="video" ${p.type==='video'?'selected':''}>Video</option>
        </select>
      </div>
      <div class="field"><label>Rok</label><input type="text" value="${esc(p.year||'')}" onchange="set('year',this.value)"></div>
      <div class="field">
        <label>Layout</label>
        <select onchange="set('layout',this.value)">
          <option value="normal" ${p.layout==='normal'?'selected':''}>Normal</option>
          <option value="wide" ${p.layout==='wide'?'selected':''}>Wide</option>
          <option value="tall" ${p.layout==='tall'?'selected':''}>Tall</option>
          <option value="large" ${p.layout==='large'?'selected':''}>Large</option>
        </select>
      </div>
      <div class="field"><label>Thumbnail URL</label><input type="text" value="${esc(p.thumbnail||'')}" onchange="set('thumbnail',this.value)"></div>
      <div class="field"><label>Full URL</label><input type="text" value="${esc(p.full||'')}" onchange="set('full',this.value)"></div>
      <div class="field" style="grid-column:1/-1"><label>Bio</label><textarea onchange="set('bio',this.value)">${esc(p.bio||'')}</textarea></div>
      <div class="field" style="grid-column:1/-1"><label>Techniques (oddělené čárkou)</label><input type="text" value="${esc(Array.isArray(p.techniques)?p.techniques.join(', '):(p.techniques||''))}" onchange="setTech(this.value)"></div>
    </div>

    <div class="section-title">Gear</div>
    <div class="gear-grid">${gearHtml}</div>

    <div class="section-title">Media</div>

    <div class="drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
      <span>📁</span>
      <div>Klikni pro výběr souborů, nebo přetáhni sem</div>
      <div style="font-size:11px;margin-top:4px;opacity:.7">Ctrl+A pro výběr všech souborů ve složce</div>
      <input type="file" id="fileInput" multiple style="display:none" onchange="handleFiles(this.files)">
    </div>

    <div class="upload-progress" id="uploadProgress">
      <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--muted);margin-bottom:6px">
        <span id="uploadLabel">Nahrávání…</span>
        <span id="uploadPercent">0%</span>
      </div>
      <div class="upload-progress-bar"><div class="upload-progress-fill" id="uploadFill"></div></div>
    </div>

    <div class="media-toolbar">
      <button class="btn" onclick="document.getElementById('fileInput').click()">+ Vybrat soubory</button>
      <button class="btn" onclick="document.getElementById('folderInput').click()">+ Vybrat složku</button>
      <button class="btn" onclick="addMediaUrl()">+ Přidat URL</button>
      <input type="file" id="folderInput" webkitdirectory directory style="display:none" onchange="handleFiles(this.files)">
    </div>

    <div class="media-list" id="mediaList">
      ${mediaHtml || '<div class="empty" id="mediaEmpty">Žádná media</div>'}
    </div>
  `;

  const dz = document.getElementById('dropZone');
  if(dz){
    dz.addEventListener('dragover', e=>{e.preventDefault();dz.classList.add('dragover');});
    dz.addEventListener('dragleave', e=>{dz.classList.remove('dragover');});
    dz.addEventListener('drop', e=>{
      e.preventDefault();dz.classList.remove('dragover');
      if(e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
    });
  }
}

function set(key,val){
  if(activeIdx<0) return;
  projects[activeIdx][key] = val;
  if(key==='title'||key==='type') renderList();
  debounceSave();
}
function setTech(val){
  if(activeIdx<0) return;
  const arr = val.split(',').map(s=>s.trim()).filter(Boolean);
  projects[activeIdx].techniques = arr.length?arr:null;
  debounceSave();
}
function setMedia(mi,key,val){
  if(activeIdx<0) return;
  projects[activeIdx].media[mi][key] = val;
  debounceSave();
}

const VIDEO_EXTS = ['.mp4','.mov','.webm','.avi','.mkv','.m4v'];
function isVideoFileName(name){
  if(!name) return false;
  const lower = name.toLowerCase();
  return VIDEO_EXTS.some(ext => lower.endsWith(ext));
}

function createVideoThumbnailFromFile(file){
  return new Promise(resolve => {
    const url = URL.createObjectURL(file);
    const video = document.createElement('video');
    video.src = url;
    video.muted = true;
    video.playsInline = true;
    video.preload = 'metadata';
    video.style.position = 'fixed';
    video.style.left = '-9999px';
    video.style.width = '1px';
    video.style.height = '1px';
    document.body.appendChild(video);

    let done = false;
    let timeoutId = null;
    const cleanup = () => {
      if(done) return;
      done = true;
      video.pause();
      video.remove();
      URL.revokeObjectURL(url);
    };
    const fail = () => {
      clearTimeout(timeoutId);
      cleanup();
      resolve(null);
    };
    const finish = blob => {
      clearTimeout(timeoutId);
      cleanup();
      resolve(blob);
    };

    const queueCapture = () => {
      if (done) return;
      try {
        const w = video.videoWidth || 640;
        const h = video.videoHeight || 360;
        const width = Math.min(640, w);
        const height = Math.max(1, Math.round((width * h) / w));
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, width, height);
        canvas.toBlob(blob => {
          if (blob) finish(blob);
          else fail();
        }, 'image/jpeg', 0.92);
      } catch (e) {
        fail();
      }
    };

    let targetTime = 3;
    video.addEventListener('loadedmetadata', () => {
      if (video.duration && video.duration < 3) {
        targetTime = Math.max(0.1, video.duration / 2);
      }
      if (video.duration && targetTime >= video.duration) {
        targetTime = Math.max(0.1, video.duration - 0.1);
      }
      video.currentTime = targetTime;
    });

    video.addEventListener('seeked', () => {
      if (!done) queueCapture();
    });

    video.addEventListener('loadeddata', () => {
      if (!done && Math.abs(video.currentTime - targetTime) < 0.1) {
        queueCapture();
      }
    });

    video.addEventListener('error', fail);
    video.addEventListener('abort', fail);

    timeoutId = setTimeout(fail, 8000);
    video.load();
  });
}

// Gear
function addGear(cat){
  if(activeIdx<0) return;
  ensureGear(projects[activeIdx]);
  projects[activeIdx].gear[cat].push('');
  renderForm();
}
function addGearFromSelect(cat){
  const sel = document.getElementById('gear-add-'+cat);
  if(!sel || !sel.value) return;
  if(activeIdx<0) return;
  ensureGear(projects[activeIdx]);
  if(!projects[activeIdx].gear[cat].includes(sel.value)){
    projects[activeIdx].gear[cat].push(sel.value);
  }
  renderForm();
  debounceSave();
}
function removeGear(cat,idx){
  if(activeIdx<0) return;
  projects[activeIdx].gear[cat].splice(idx,1);
  renderForm();
  debounceSave();
}
function updateGear(cat,idx,val){
  if(activeIdx<0) return;
  projects[activeIdx].gear[cat][idx] = val;
  debounceSave();
}

// Upload
async function handleFiles(files){
  if(!files.length || activeIdx<0) return;
  const progress = document.getElementById('uploadProgress');
  const fill = document.getElementById('uploadFill');
  const label = document.getElementById('uploadLabel');
  const pct = document.getElementById('uploadPercent');
  progress.classList.add('active');

  const fd = new FormData();
  const fileArray = Array.from(files);
  const thumbTasks = [];

  fileArray.forEach((f, idx) => {
    fd.append(`file_${idx}`, f, f.name);
    if (f.type.startsWith('video/') || isVideoFileName(f.name)) {
      thumbTasks.push((async () => {
        const thumb = await createVideoThumbnailFromFile(f);
        if (thumb) {
          const thumbName = f.name.replace(/\.[^.]+$/, '') + '_thumb.jpg';
          fd.append(`thumb_${idx}`, thumb, thumbName);
        }
      })());
    }
  });

  await Promise.all(thumbTasks);
  fd.append('project_type', projects[activeIdx].type || 'photo');
  fd.append('project_year', projects[activeIdx].year || 'unknown');
  fd.append('project_title', projects[activeIdx].title || 'untitled');

  try{
    const xhr = new XMLHttpRequest();
    xhr.open('POST','/api/upload');
    xhr.upload.onprogress = e=>{
      if(e.lengthComputable){
        const p = Math.round((e.loaded/e.total)*100);
        fill.style.width = p+'%';
        pct.textContent = p+'%';
      }
    };
    const result = await new Promise((res,rej)=>{
      xhr.onload = ()=>res(JSON.parse(xhr.responseText));
      xhr.onerror = rej;
      xhr.send(fd);
    });

    if(result.ok){
      label.textContent = 'Hotovo!';
      pct.textContent = '100%';
      fill.style.width = '100%';

      if(!projects[activeIdx].media) projects[activeIdx].media = [];
      for(const f of result.files){
        projects[activeIdx].media.push({
          type: f.type,
          src: f.rel_path,
          thumbnail: f.thumbnail || f.rel_path,
          title: f.filename.replace(/\.[^.]+$/,''),
          caption: ''
        });
      }
      renderForm();
      debounceSave();
      showToast('Nahráno '+result.files.length+' souborů');
    }else{
      throw new Error(result.error||'Chyba');
    }
  }catch(e){
    label.textContent = 'Chyba: '+e.message;
    pct.textContent = '';
    showToast('Chyba nahrávání');
  }
  setTimeout(()=>progress.classList.remove('active'),1500);
}

function addMediaUrl(){
  if(activeIdx<0) return;
  if(!projects[activeIdx].media) projects[activeIdx].media = [];
  projects[activeIdx].media.push({type:'photo', src:'', thumbnail:'', title:'', caption:''});
  renderForm();
  debounceSave();
}
function deleteMedia(mi){
  if(activeIdx<0) return;
  projects[activeIdx].media.splice(mi,1);
  renderForm();
  debounceSave();
}
function moveMedia(mi,dir){
  if(activeIdx<0) return;
  const arr = projects[activeIdx].media;
  const ni = mi+dir;
  if(ni<0||ni>=arr.length) return;
  [arr[mi],arr[ni]] = [arr[ni],arr[mi]];
  renderForm();
  debounceSave();
}

function addProject(){
  const maxId = projects.reduce((m,p)=>Math.max(m,p.id||0),0);
  const gearDefault = {};
  GEAR_CATS.forEach(c=>gearDefault[c]=[]);
  const np = {
    id: maxId+1,
    title: "Nový projekt",
    type: "photo",
    year: "2025",
    layout: "normal",
    thumbnail: "",
    full: "",
    bio: "",
    techniques: [],
    gear: gearDefault,
    media: []
  };
  projects.push(np);
  renderList();
  select(projects.length-1);
  debounceSave();
}
function deleteProject(){
  if(activeIdx<0||!confirm('Opravdu smazat projekt "'+(projects[activeIdx].title||'')+'"?')) return;
  projects.splice(activeIdx,1);
  activeIdx = Math.min(activeIdx, projects.length-1);
  renderList(); renderForm(); debounceSave();
}
function duplicateProject(){
  if(activeIdx<0) return;
  const clone = JSON.parse(JSON.stringify(projects[activeIdx]));
  const maxId = projects.reduce((m,p)=>Math.max(m,p.id||0),0);
  clone.id = maxId+1;
  clone.title = (clone.title||'') + ' (kopie)';
  projects.splice(activeIdx+1,0,clone);
  renderList();
  select(activeIdx+1);
  debounceSave();
}

let saveTimer;
function debounceSave(){
  clearTimeout(saveTimer);
  saveTimer = setTimeout(saveNow, 800);
}
async function saveNow(){
  setStatus('Ukládání…');
  try{
    const r = await fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(projects)});
    const j = await r.json();
    if(j.ok){ setStatus('Uloženo'); showToast('Uloženo'); }
    else { setStatus('Chyba: '+j.error); }
  }catch(e){ setStatus('Chyba sítě'); }
}
</script>
</body>
</html>
'''

# ─── MAIN ──────────────────────────────────────────────────────────────
def main():
    global tech_inventory
    load_json()
    tech_inventory = load_tech_inventory()
    save_json()

    server = HTTPServer(("0.0.0.0", PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    url = f"http://localhost:{PORT}"
    print("=" * 50)
    print(f"  Projects Builder běží na {url}")
    print(f"  Načteno z Kamera.md: {len(tech_inventory.get('camera', []))} kamer")
    print(f"  Načteno z Optika.md: {len(tech_inventory.get('lenses', []))} objektivů, {len(tech_inventory.get('filter', []))} filtrů")
    print("=" * 50)

    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        while True:
            __import__('time').sleep(1)
    except KeyboardInterrupt:
        print("\nUkončuji…")
        server.shutdown()

if __name__ == "__main__":
    main()