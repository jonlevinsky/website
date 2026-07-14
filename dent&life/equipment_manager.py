#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dent&Life — Manager vybaveni a referenci
GUI aplikace pro spravu obsahu webu laborator-dentlife.cz

Pouziti:
    python equipment_manager.py

Funkce:
    • Sprava sekce Vybaveni (equipment)
    • Sprava sekce Reference (portfolio)
    • Drag & drop razeni
    • Auto-save do JSON
    • Primy inject do index.html
    • Nahled obrazku
"""

import json
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

DATA_FILE = "dentlife_data.json"
INDEX_FILE = "index.html"
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=800&h=600&fit=crop&q=80"


class EquipmentItem:
    def __init__(self, data=None):
        if data:
            self.__dict__.update(data)
        else:
            self.id = ""
            self.number = ""
            self.badge_text = ""
            self.title = ""
            self.section_badge = ""
            self.description = ""
            self.tags = []
            self.image = ""
            self.side = "left"

    def to_dict(self):
        return self.__dict__.copy()

    @staticmethod
    def from_dict(d):
        return EquipmentItem(d)

    def __repr__(self):
        return f"Equipment({self.number}: {self.title})"


class ReferenceItem:
    def __init__(self, data=None):
        if data:
            self.__dict__.update(data)
        else:
            self.id = ""
            self.gallery_index = 0
            self.title = ""
            self.description = ""
            self.image = ""

    def to_dict(self):
        return self.__dict__.copy()

    @staticmethod
    def from_dict(d):
        return ReferenceItem(d)

    def __repr__(self):
        return f"Reference({self.gallery_index}: {self.title})"


def generate_equipment_html(items):
    lines = []
    for i, item in enumerate(items):
        side = item.side if hasattr(item, "side") else ("left" if i % 2 == 0 else "right")
        img_block = (
            '        <div class="about-image-wrapper">\n'
            '          <div class="about-image" style="aspect-ratio: 4/3;">\n'
            '            <img src="' + item.image + '" loading="lazy" decoding="async" alt="' + item.title + '">\n'
            '          </div>\n'
            '          <div class="about-badge">\n'
            '            <div class="about-badge-number">' + item.number + '</div>\n'
            '            <div class="about-badge-text">' + item.badge_text + '</div>\n'
            '          </div>\n'
            '        </div>'
        )
        tags_html = "\n              ".join(f'<span class="brand-tag">{tag}</span>' for tag in item.tags)
        content_block = (
            '        <div class="about-content">\n'
            '          <span class="section-badge">' + item.section_badge + '</span>\n'
            '          <h2 class="section-title">' + item.title + '</h2>\n'
            '          <p>' + item.description + '</p>\n'
            '          <div class="about-brands">\n'
            '            <p class="about-brands-title">Klíčové vlastnosti</p>\n'
            '            <div class="brands-list">\n'
            '              ' + tags_html + '\n'
            '            </div>\n'
            '          </div>\n'
            '        </div>'
        )
        if side == "left":
            inner = img_block + "\n" + content_block
        else:
            inner = content_block + "\n" + img_block
        lines.append(
            '      <div class="about-grid equipment-grid-custom" style="margin-top: 0;">\n'
            + inner + '\n'
            '      </div>'
        )
    return "\n".join(lines)


def generate_reference_html(items):
    lines = []
    for item in items:
        lines.append(
            '        <div class="portfolio-item" data-gallery="' + str(item.gallery_index) + '" role="button" tabindex="0" aria-label="Zobrazit detail: ' + item.title + '">\n'
            '          <div class="portfolio-image">\n'
            '            <img src="' + item.image + '" loading="lazy" decoding="async" alt="' + item.title + '">\n'
            '          </div>\n'
            '          <div class="portfolio-overlay"></div>\n'
            '          <div class="portfolio-content">\n'
            '            <div class="portfolio-info">\n'
            '              <div>\n'
            '                <h3>' + item.title + '</h3>\n'
            '                <p>' + item.description + '</p>\n'
            '              </div>\n'
            '              <div class="portfolio-arrow">\n'
            '                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">\n'
            '                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />\n'
            '                </svg>\n'
            '              </div>\n'
            '            </div>\n'
            '          </div>\n'
            '        </div>'
        )
    return "\n".join(lines)


class DragDropListbox(tk.Listbox):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_drop)
        self._drag_index = None

    def _on_click(self, event):
        self._drag_index = self.nearest(event.y)

    def _on_drag(self, event):
        if self._drag_index is None:
            return
        index = self.nearest(event.y)
        if index != self._drag_index and 0 <= index < self.size():
            items = list(self.get(0, tk.END))
            items[self._drag_index], items[index] = items[index], items[self._drag_index]
            self.delete(0, tk.END)
            for item in items:
                self.insert(tk.END, item)
            self._drag_index = index
            self.selection_set(index)
            self.see(index)
            if hasattr(self, "on_reorder"):
                self.on_reorder()

    def _on_drop(self, event):
        self._drag_index = None


class DentLifeManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dent&Life — Manager vybaveni a referenci")
        self.geometry("1200x850")
        self.minsize(900, 650)
        self.equipment = []
        self.references = []
        self.index_path = self._find_index_html()
        self.load_data()
        self._build_ui()
        self._refresh_equipment_list()
        self._refresh_reference_list()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._apply_style()

    def _find_index_html(self):
        """Najde index.html v aktualnim adresari nebo o jednu uroven vys."""
        candidates = [
            INDEX_FILE,
            os.path.join("..", INDEX_FILE),
            os.path.join(os.path.dirname(__file__), INDEX_FILE),
            os.path.join(os.path.dirname(__file__), "..", INDEX_FILE),
        ]
        for path in candidates:
            if os.path.exists(path):
                return os.path.abspath(path)
        return None

    def _apply_style(self):
        self.configure(bg="#ffffff")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#ffffff")
        style.configure("TLabel", background="#ffffff", foreground="#171717", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("TNotebook", background="#ffffff", tabmargins=[2, 5, 2, 0])
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[15, 8])
        style.map("TNotebook.Tab", background=[("selected", "#ffffff")])
        self.option_add("*Listbox.background", "#fafafa")
        self.option_add("*Listbox.foreground", "#171717")
        self.option_add("*Listbox.selectBackground", "#ca4848")
        self.option_add("*Listbox.selectForeground", "#ffffff")
        self.option_add("*Listbox.font", ("Segoe UI", 10))
        self.option_add("*Entry.background", "#fafafa")
        self.option_add("*Entry.foreground", "#171717")
        self.option_add("*Entry.insertBackground", "#ca4848")

    def _build_ui(self):
        # Horni panel s cestou k index.html
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        ttk.Label(top_frame, text="index.html:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.index_label = ttk.Label(top_frame, text=self.index_path or "(nenalezen)", foreground="#737373")
        self.index_label.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(top_frame, text="Vybrat...", command=self._select_index_html).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(top_frame, text="Inject vse", command=self._inject_all).pack(side=tk.RIGHT)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.eq_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.eq_frame, text="  Vybaveni  ")
        self._build_equipment_tab()
        self.ref_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.ref_frame, text="  Reference  ")
        self._build_reference_tab()
        self.status = ttk.Label(self, text="Pripraveno", relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))

    def _build_equipment_tab(self):
        left = ttk.Frame(self.eq_frame, width=300)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)
        ttk.Label(left, text="Seznam vybaveni", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(0, 8))
        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(btn_frame, text="+ Pridat", command=self._add_equipment).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_frame, text="▲ Nahoru", command=lambda: self._move_equipment(-1)).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_frame, text="▼ Dolu", command=lambda: self._move_equipment(1)).pack(side=tk.LEFT)
        self.eq_list = DragDropListbox(left, selectmode=tk.SINGLE, height=20, exportselection=False)
        self.eq_list.pack(fill=tk.BOTH, expand=True)
        self.eq_list.on_reorder = self._on_equipment_reorder
        self.eq_list.bind("<<ListboxSelect>>", self._on_equipment_select)
        ttk.Button(left, text="Smazat", command=self._delete_equipment).pack(fill=tk.X, pady=(8, 0))
        ttk.Button(left, text="Aplikovat do index.html", command=self._inject_equipment).pack(fill=tk.X, pady=(4, 0))
        right = ttk.Frame(self.eq_frame)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(right, text="Editor polozky", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(0, 12))
        form = ttk.Frame(right)
        form.pack(fill=tk.X)
        ttk.Label(form, text="Cislo polozky:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.eq_number = ttk.Entry(form, width=10)
        self.eq_number.grid(row=0, column=1, sticky=tk.W, pady=4, padx=(0, 20))
        ttk.Label(form, text="Badge text:").grid(row=0, column=2, sticky=tk.W, pady=4)
        self.eq_badge = ttk.Entry(form, width=15)
        self.eq_badge.grid(row=0, column=3, sticky=tk.W, pady=4)
        ttk.Label(form, text="Nazev:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.eq_title = ttk.Entry(form, width=50)
        self.eq_title.grid(row=1, column=1, columnspan=3, sticky=tk.EW, pady=4)
        ttk.Label(form, text="Sekce badge:").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.eq_section_badge = ttk.Entry(form, width=30)
        self.eq_section_badge.grid(row=2, column=1, columnspan=3, sticky=tk.W, pady=4)
        ttk.Label(form, text="Popis:").grid(row=3, column=0, sticky=tk.NW, pady=4)
        self.eq_desc = ScrolledText(form, width=60, height=5, wrap=tk.WORD, font=("Segoe UI", 10))
        self.eq_desc.grid(row=3, column=1, columnspan=3, sticky=tk.EW, pady=4)
        ttk.Label(form, text="Tagy (carkou):").grid(row=4, column=0, sticky=tk.W, pady=4)
        self.eq_tags = ttk.Entry(form, width=50)
        self.eq_tags.grid(row=4, column=1, columnspan=3, sticky=tk.EW, pady=4)
        ttk.Label(form, text="Obrazek URL:").grid(row=5, column=0, sticky=tk.W, pady=4)
        img_frame = ttk.Frame(form)
        img_frame.grid(row=5, column=1, columnspan=3, sticky=tk.EW, pady=4)
        self.eq_image = ttk.Entry(img_frame, width=50)
        self.eq_image.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(img_frame, text="Prochazet...", command=self._browse_equipment_image).pack(side=tk.LEFT, padx=(4, 0))
        ttk.Label(form, text="Pozice obrazku:").grid(row=6, column=0, sticky=tk.W, pady=4)
        self.eq_side = ttk.Combobox(form, values=["left", "right"], width=10, state="readonly")
        self.eq_side.set("left")
        self.eq_side.grid(row=6, column=1, sticky=tk.W, pady=4)
        ttk.Label(right, text="Nahled obrazku:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(20, 8))
        self.eq_preview = tk.Label(right, text="(zadny obrazek)", bg="#f5f5f5", fg="#737373", width=60, height=10, relief=tk.RIDGE)
        self.eq_preview.pack(anchor=tk.W)
        ttk.Button(right, text="Ulozit zmeny", command=self._save_equipment).pack(anchor=tk.W, pady=(20, 0))
        help_text = (
            "Napoveda:\n"
            "• Drag & drop v seznamu = zmena poradi\n"
            "• Cislo = poradove cislo v badge (01, 02...)\n"
            "• Badge text = kratky popis pod cislem (CAD/CAM, Keramika...)\n"
            "• Tagy = klicove vlastnosti oddelene carkou\n"
            "• Pozice obrazku = left (vlevo) / right (vpravo)\n"
            "• Aplikovat do index.html = primo zapise sekci Vybaveni do HTML"
        )
        ttk.Label(right, text=help_text, foreground="#737373", justify=tk.LEFT).pack(anchor=tk.W, pady=(20, 0))

    def _build_reference_tab(self):
        left = ttk.Frame(self.ref_frame, width=300)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)
        ttk.Label(left, text="Seznam referenci", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(0, 8))
        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(btn_frame, text="+ Pridat", command=self._add_reference).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_frame, text="▲ Nahoru", command=lambda: self._move_reference(-1)).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_frame, text="▼ Dolu", command=lambda: self._move_reference(1)).pack(side=tk.LEFT)
        self.ref_list = DragDropListbox(left, selectmode=tk.SINGLE, height=20, exportselection=False)
        self.ref_list.pack(fill=tk.BOTH, expand=True)
        self.ref_list.on_reorder = self._on_reference_reorder
        self.ref_list.bind("<<ListboxSelect>>", self._on_reference_select)
        ttk.Button(left, text="Smazat", command=self._delete_reference).pack(fill=tk.X, pady=(8, 0))
        ttk.Button(left, text="Aplikovat do index.html", command=self._inject_references).pack(fill=tk.X, pady=(4, 0))
        right = ttk.Frame(self.ref_frame)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(right, text="Editor reference", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(0, 12))
        form = ttk.Frame(right)
        form.pack(fill=tk.X)
        ttk.Label(form, text="Gallery index:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.ref_index = ttk.Entry(form, width=10)
        self.ref_index.grid(row=0, column=1, sticky=tk.W, pady=4)
        ttk.Label(form, text="(0, 1, 2, 3...)").grid(row=0, column=2, sticky=tk.W, pady=4)
        ttk.Label(form, text="Nazev:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.ref_title = ttk.Entry(form, width=50)
        self.ref_title.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=4)
        ttk.Label(form, text="Popis:").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.ref_desc = ttk.Entry(form, width=50)
        self.ref_desc.grid(row=2, column=1, columnspan=2, sticky=tk.EW, pady=4)
        ttk.Label(form, text="Obrazek:").grid(row=3, column=0, sticky=tk.W, pady=4)
        img_frame = ttk.Frame(form)
        img_frame.grid(row=3, column=1, columnspan=2, sticky=tk.EW, pady=4)
        self.ref_image = ttk.Entry(img_frame, width=50)
        self.ref_image.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(img_frame, text="Prochazet...", command=self._browse_reference_image).pack(side=tk.LEFT, padx=(4, 0))
        ttk.Label(right, text="Nahled:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(20, 8))
        self.ref_preview = tk.Label(right, text="(zadny obrazek)", bg="#f5f5f5", fg="#737373", width=60, height=10, relief=tk.RIDGE)
        self.ref_preview.pack(anchor=tk.W)
        ttk.Button(right, text="Ulozit zmeny", command=self._save_reference).pack(anchor=tk.W, pady=(20, 0))
        help_text = (
            "Napoveda:\n"
            "• Gallery index = cislo pro data-gallery atribut (0, 1, 2...)\n"
            "• Nazev = nadpis pod obrazkem\n"
            "• Popis = kratky text pod nadpisem\n"
            "• Obrazek = cesta k souboru (files/res/reference/ref-01.jpg)\n"
            "• Aplikovat do index.html = primo zapise sekci Reference do HTML"
        )
        ttk.Label(right, text=help_text, foreground="#737373", justify=tk.LEFT).pack(anchor=tk.W, pady=(20, 0))

    # ═══════════════════════════════════════════════════════
    # INJECT LOGIKA
    # ═══════════════════════════════════════════════════════
    def _select_index_html(self):
        path = filedialog.askopenfilename(
            title="Vyberte index.html",
            filetypes=[("HTML soubory", "*.html"), ("Vse", "*.*")]
        )
        if path:
            self.index_path = path
            self.index_label.config(text=path)
            self.status.config(text=f"Vybrano: {path}")

    def _inject_all(self):
        """Injectne obe sekce najednou."""
        ok1 = self._inject_equipment(silent=True)
        ok2 = self._inject_references(silent=True)
        if ok1 and ok2:
            messagebox.showinfo("Hotovo", "Vsechny zmeny byly aplikovany do index.html")
            self.status.config(text="Vse injectnuto do index.html")
        elif ok1:
            messagebox.showwarning("Castecne", "Vybaveni injectnuto, reference selhaly")
        elif ok2:
            messagebox.showwarning("Castecne", "Reference injectnuty, vybaveni selhalo")
        else:
            messagebox.showerror("Chyba", "Nepodarilo se injectnout ani jednu sekci")

    def _inject_equipment(self, silent=False):
        if not self.index_path or not os.path.exists(self.index_path):
            if not silent:
                messagebox.showerror("Chyba", "index.html nebyl nalezen. Vyberte soubor.")
            return False
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                html = f.read()
        except Exception as e:
            if not silent:
                messagebox.showerror("Chyba", f"Nepodarilo se precist index.html: {e}")
            return False

        new_section = generate_equipment_html(self.equipment)

        # Najdeme sekci vybaveni a nahradime ji
        # Hledame: <!-- Equipment Section --> az <!-- Contact Section -->
        pattern = r'(<!--\s*Equipment Section\s*-->)(.*?)(<!--\s*Contact Section\s*-->)'
        match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)

        if match:
            # Zachovame header sekce
            old_content = match.group(0)
            # Vytvorime novou sekci se zachovanim headeru
            header_part = match.group(1)
            footer_part = match.group(3)
            new_html = header_part + "\n" + new_section + "\n\n  " + footer_part
            html = html.replace(old_content, new_html)
        else:
            # Zkusime najit podle id="vybaveni"
            pattern2 = r'(<section[^>]*id=["\']vybaveni["\'][^>]*>)(.*?)(</section>)'
            match2 = re.search(pattern2, html, re.DOTALL | re.IGNORECASE)
            if match2:
                old_content = match2.group(0)
                # Zachovame opening tag
                new_html = match2.group(1) + "\n    <div class=\"container\">\n      <div class=\"section-header\">\n        <span class=\"section-badge\">Vybaveni</span>\n        <h2 class=\"section-title\">Technologie <strong>nasi laboratore</strong></h2>\n        <p class=\"section-text\">Pouzivame spickove pristroje pro maximalni presnost a kvalitu</p>\n      </div>\n" + new_section + "\n    </div>\n  " + match2.group(3)
                html = html.replace(old_content, new_html)
            else:
                if not silent:
                    messagebox.showerror("Chyba", "Sekce Vybaveni nebyla v index.html nalezena.")
                return False

        try:
            with open(self.index_path, "w", encoding="utf-8") as f:
                f.write(html)
            if not silent:
                messagebox.showinfo("Hotovo", "Sekce Vybaveni byla aktualizovana v index.html")
            self.status.config(text="Vybaveni injectnuto do index.html")
            return True
        except Exception as e:
            if not silent:
                messagebox.showerror("Chyba", f"Nepodarilo se zapsat index.html: {e}")
            return False

    def _inject_references(self, silent=False):
        if not self.index_path or not os.path.exists(self.index_path):
            if not silent:
                messagebox.showerror("Chyba", "index.html nebyl nalezen. Vyberte soubor.")
            return False
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                html = f.read()
        except Exception as e:
            if not silent:
                messagebox.showerror("Chyba", f"Nepodarilo se precist index.html: {e}")
            return False

        new_section = generate_reference_html(self.references)

        # Najdeme sekci reference
        # Hledame: <!-- Reference - obrazky --> az <!-- Locations Section -->
        pattern = r'(<!--\s*Reference.*?-->)(.*?)(<!--\s*Locations Section\s*-->)'
        match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)

        if match:
            old_content = match.group(0)
            header_part = match.group(1)
            footer_part = match.group(3)
            new_html = header_part + "\n" + new_section + "\n      </div>\n    </div>\n  " + footer_part
            html = html.replace(old_content, new_html)
        else:
            # Zkusime podle id="reference"
            pattern2 = r'(<section[^>]*id=["\']reference["\'][^>]*>)(.*?)(</section>)'
            match2 = re.search(pattern2, html, re.DOTALL | re.IGNORECASE)
            if match2:
                old_content = match2.group(0)
                new_html = match2.group(1) + "\n    <div class=\"container\">\n      <div class=\"section-header\">\n        <span class=\"section-badge\">Reference</span>\n        <h2 class=\"section-title\">Ukazky nasej <strong>prace</strong></h2>\n        <p class=\"section-text\">Precizni zpracovani a kvalita v kazdem detailu</p>\n      </div>\n      <div class=\"portfolio-grid\">\n" + new_section + "\n      </div>\n    </div>\n  " + match2.group(3)
                html = html.replace(old_content, new_html)
            else:
                if not silent:
                    messagebox.showerror("Chyba", "Sekce Reference nebyla v index.html nalezena.")
                return False

        try:
            with open(self.index_path, "w", encoding="utf-8") as f:
                f.write(html)
            if not silent:
                messagebox.showinfo("Hotovo", "Sekce Reference byla aktualizovana v index.html")
            self.status.config(text="Reference injectnuty do index.html")
            return True
        except Exception as e:
            if not silent:
                messagebox.showerror("Chyba", f"Nepodarilo se zapsat index.html: {e}")
            return False

    # ═══════════════════════════════════════════════════════
    # LOGIKA VYBAVENI
    # ═══════════════════════════════════════════════════════
    def _refresh_equipment_list(self):
        self.eq_list.delete(0, tk.END)
        for item in self.equipment:
            display = f"{item.number}: {item.title}" if item.title else "(nova polozka)"
            self.eq_list.insert(tk.END, display)

    def _on_equipment_select(self, event=None):
        idx = self.eq_list.curselection()
        if not idx:
            return
        item = self.equipment[idx[0]]
        self._fill_equipment_form(item)
        self.status.config(text=f"Vybrano: {item.title}")

    def _fill_equipment_form(self, item):
        self.eq_number.delete(0, tk.END)
        self.eq_number.insert(0, item.number)
        self.eq_badge.delete(0, tk.END)
        self.eq_badge.insert(0, item.badge_text)
        self.eq_title.delete(0, tk.END)
        self.eq_title.insert(0, item.title)
        self.eq_section_badge.delete(0, tk.END)
        self.eq_section_badge.insert(0, item.section_badge)
        self.eq_desc.delete("1.0", tk.END)
        self.eq_desc.insert("1.0", item.description)
        self.eq_tags.delete(0, tk.END)
        self.eq_tags.insert(0, ", ".join(item.tags) if isinstance(item.tags, list) else str(item.tags))
        self.eq_image.delete(0, tk.END)
        self.eq_image.insert(0, item.image)
        self.eq_side.set(getattr(item, "side", "left"))
        self._update_equipment_preview(item.image)

    def _update_equipment_preview(self, url):
        if not url:
            self.eq_preview.config(text="(zadny obrazek)", image="")
            return
        try:
            from PIL import Image, ImageTk
            import io, urllib.request
            if url.startswith("http"):
                with urllib.request.urlopen(url, timeout=5) as response:
                    img_data = response.read()
                img = Image.open(io.BytesIO(img_data))
            else:
                if os.path.exists(url):
                    img = Image.open(url)
                else:
                    self.eq_preview.config(text=f"(soubor nenalezen: {url})", image="")
                    return
            img.thumbnail((400, 200), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.eq_preview.config(image=photo, text="")
            self.eq_preview.image = photo
        except Exception as e:
            self.eq_preview.config(text=f"(nahled nedostupny: {str(e)[:50]})", image="")

    def _browse_equipment_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")])
        if path:
            self.eq_image.delete(0, tk.END)
            self.eq_image.insert(0, path)
            self._update_equipment_preview(path)

    def _add_equipment(self):
        new_item = EquipmentItem()
        new_item.id = f"eq-{len(self.equipment)+1}"
        new_item.number = f"{len(self.equipment)+1:02d}"
        new_item.badge_text = "Nove"
        new_item.title = "Nove vybaveni"
        new_item.section_badge = "Kategorie"
        new_item.description = "Popis vybaveni..."
        new_item.tags = ["Vlastnost 1", "Vlastnost 2"]
        new_item.image = DEFAULT_IMAGE
        new_item.side = "left" if len(self.equipment) % 2 == 0 else "right"
        self.equipment.append(new_item)
        self._refresh_equipment_list()
        self.eq_list.selection_set(tk.END)
        self._on_equipment_select()
        self.status.config(text="Pridano nove vybaveni")

    def _delete_equipment(self):
        idx = self.eq_list.curselection()
        if not idx:
            messagebox.showwarning("Varovani", "Nejprve vyberte polozku ke smazani.")
            return
        if messagebox.askyesno("Potvrdit", "Opravdu chcete smazat tuto polozku?"):
            del self.equipment[idx[0]]
            self._refresh_equipment_list()
            self.status.config(text="Polozka smazana")

    def _move_equipment(self, direction):
        idx = self.eq_list.curselection()
        if not idx:
            return
        i = idx[0]
        j = i + direction
        if 0 <= j < len(self.equipment):
            self.equipment[i], self.equipment[j] = self.equipment[j], self.equipment[i]
            self._refresh_equipment_list()
            self.eq_list.selection_set(j)
            self.eq_list.see(j)
            self._on_equipment_select()

    def _on_equipment_reorder(self):
        self._refresh_equipment_list()

    def _save_equipment(self):
        idx = self.eq_list.curselection()
        if not idx:
            messagebox.showwarning("Varovani", "Nejprve vyberte polozku.")
            return
        item = self.equipment[idx[0]]
        item.number = self.eq_number.get()
        item.badge_text = self.eq_badge.get()
        item.title = self.eq_title.get()
        item.section_badge = self.eq_section_badge.get()
        item.description = self.eq_desc.get("1.0", tk.END).strip()
        tags_raw = self.eq_tags.get()
        item.tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        item.image = self.eq_image.get()
        item.side = self.eq_side.get()
        self._refresh_equipment_list()
        self.eq_list.selection_set(idx[0])
        self.save_data()
        self.status.config(text="Vybaveni ulozeno")

    # ═══════════════════════════════════════════════════════
    # LOGIKA REFERENCÍ
    # ═══════════════════════════════════════════════════════
    def _refresh_reference_list(self):
        self.ref_list.delete(0, tk.END)
        for item in self.references:
            display = f"[{item.gallery_index}] {item.title}" if item.title else f"[{item.gallery_index}] (nova)"
            self.ref_list.insert(tk.END, display)

    def _on_reference_select(self, event=None):
        idx = self.ref_list.curselection()
        if not idx:
            return
        item = self.references[idx[0]]
        self._fill_reference_form(item)
        self.status.config(text=f"Vybrano: {item.title}")

    def _fill_reference_form(self, item):
        self.ref_index.delete(0, tk.END)
        self.ref_index.insert(0, str(item.gallery_index))
        self.ref_title.delete(0, tk.END)
        self.ref_title.insert(0, item.title)
        self.ref_desc.delete(0, tk.END)
        self.ref_desc.insert(0, item.description)
        self.ref_image.delete(0, tk.END)
        self.ref_image.insert(0, item.image)
        self._update_reference_preview(item.image)

    def _update_reference_preview(self, url):
        if not url:
            self.ref_preview.config(text="(zadny obrazek)", image="")
            return
        try:
            from PIL import Image, ImageTk
            import io, urllib.request
            if url.startswith("http"):
                with urllib.request.urlopen(url, timeout=5) as response:
                    img_data = response.read()
                img = Image.open(io.BytesIO(img_data))
            else:
                if os.path.exists(url):
                    img = Image.open(url)
                else:
                    self.ref_preview.config(text=f"(soubor nenalezen: {url})", image="")
                    return
            img.thumbnail((400, 200), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.ref_preview.config(image=photo, text="")
            self.ref_preview.image = photo
        except Exception as e:
            self.ref_preview.config(text=f"(nahled nedostupny: {str(e)[:50]})", image="")

    def _browse_reference_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")])
        if path:
            self.ref_image.delete(0, tk.END)
            self.ref_image.insert(0, path)
            self._update_reference_preview(path)

    def _add_reference(self):
        new_item = ReferenceItem()
        new_item.id = f"ref-{len(self.references)+1}"
        new_item.gallery_index = len(self.references)
        new_item.title = "Nova reference"
        new_item.description = "Popis reference..."
        new_item.image = "files/res/reference/ref-01.jpg"
        self.references.append(new_item)
        self._refresh_reference_list()
        self.ref_list.selection_set(tk.END)
        self._on_reference_select()
        self.status.config(text="Pridana nova reference")

    def _delete_reference(self):
        idx = self.ref_list.curselection()
        if not idx:
            messagebox.showwarning("Varovani", "Nejprve vyberte polozku ke smazani.")
            return
        if messagebox.askyesno("Potvrdit", "Opravdu chcete smazat tuto referenci?"):
            del self.references[idx[0]]
            for i, item in enumerate(self.references):
                item.gallery_index = i
            self._refresh_reference_list()
            self.status.config(text="Reference smazana")

    def _move_reference(self, direction):
        idx = self.ref_list.curselection()
        if not idx:
            return
        i = idx[0]
        j = i + direction
        if 0 <= j < len(self.references):
            self.references[i], self.references[j] = self.references[j], self.references[i]
            for k, item in enumerate(self.references):
                item.gallery_index = k
            self._refresh_reference_list()
            self.ref_list.selection_set(j)
            self.ref_list.see(j)
            self._on_reference_select()

    def _on_reference_reorder(self):
        self._refresh_reference_list()

    def _save_reference(self):
        idx = self.ref_list.curselection()
        if not idx:
            messagebox.showwarning("Varovani", "Nejprve vyberte polozku.")
            return
        item = self.references[idx[0]]
        try:
            item.gallery_index = int(self.ref_index.get())
        except ValueError:
            item.gallery_index = idx[0]
        item.title = self.ref_title.get()
        item.description = self.ref_desc.get()
        item.image = self.ref_image.get()
        self._refresh_reference_list()
        self.ref_list.selection_set(idx[0])
        self.save_data()
        self.status.config(text="Reference ulozena")

    # ═══════════════════════════════════════════════════════
    # PERSISTENCE
    # ═══════════════════════════════════════════════════════
    def load_data(self):
        if not os.path.exists(DATA_FILE):
            self.equipment = [
                EquipmentItem.from_dict({
                    "id": "eq-1", "number": "01", "badge_text": "CAD/CAM",
                    "title": "CAD/CAM system", "section_badge": "Precizni vyroba",
                    "description": "Digitalizace a presna vyroba pomoci nejmodernejsiho softwaru pro navrh a frezovani zubnich nahrad. Digitalni workflow zajistuje maximalni presnost a opakovatelnost vysledku.",
                    "tags": ["5-ose frezovani", "Wet & Dry", "Exocad"],
                    "image": "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=800&h=600&fit=crop&q=80",
                    "side": "left"
                }),
                EquipmentItem.from_dict({
                    "id": "eq-2", "number": "02", "badge_text": "Keramika",
                    "title": "Keramicka pec", "section_badge": "Vypalovani",
                    "description": "Vakuumova pec pro vypalovani celokeramiky s programovatelnymi teplotnimi krivkami a vakuovym cerpadlem. Zajistuje dokonalou estetiku a pevnost kazde restaurovane nahrad.",
                    "tags": ["Programovatelne krivky", "Vakuove cerpadlo", "Ivoclar"],
                    "image": "https://images.unsplash.com/photo-1579154204601-01588f351e67?w=800&h=600&fit=crop&q=80",
                    "side": "right"
                }),
                EquipmentItem.from_dict({
                    "id": "eq-3", "number": "03", "badge_text": "Kontrola",
                    "title": "Stereomikroskop", "section_badge": "Detailni kontrola",
                    "description": "Zvetseni az 40x pro detailni kontrolu povrchu, okrajovych presahu a estetickeho zpracovani. Kazda prace prochazi dkladnou mikroskopickou kontrolou kvality.",
                    "tags": ["40x zvetseni", "LED osvetleni", "Kamera"],
                    "image": "https://images.unsplash.com/photo-1582719471384-894fbb16e074?w=800&h=600&fit=crop&q=80",
                    "side": "left"
                }),
                EquipmentItem.from_dict({
                    "id": "eq-4", "number": "04", "badge_text": "Skenovani",
                    "title": "3D skener", "section_badge": "Digitalizace",
                    "description": "Bezdotykove skenovani modelu s rozlisenim 5 um pro maximalni presnost digitalniho otisku. Rychle a presne zachyceni geometrie pro naslednou digitalni vyrobu.",
                    "tags": ["5 um rozliseni", "Modely i otisky", "AutoScan"],
                    "image": "https://images.unsplash.com/photo-1581093458791-9f3c3900df4b?w=800&h=600&fit=crop&q=80",
                    "side": "right"
                }),
            ]
            self.references = [
                ReferenceItem.from_dict({
                    "id": "ref-1", "gallery_index": 0,
                    "title": "Metalokeramicke korunky",
                    "description": "Precizni zpracovani s perfektnim barevnym prechodem",
                    "image": "files/res/reference/ref-01.jpg"
                }),
                ReferenceItem.from_dict({
                    "id": "ref-2", "gallery_index": 1,
                    "title": "Celokeramicke mustky",
                    "description": "Esteticke reseni s maximalni prirozenosti",
                    "image": "files/res/reference/ref-02.jpg"
                }),
                ReferenceItem.from_dict({
                    "id": "ref-3", "gallery_index": 2,
                    "title": "Implantatove prace",
                    "description": "Moderni technologie pro dlouhodoba reseni",
                    "image": "files/res/reference/ref-03.jpg"
                }),
                ReferenceItem.from_dict({
                    "id": "ref-4", "gallery_index": 3,
                    "title": "Snimatelne protezy",
                    "description": "Komfortni a esteticky zpracovane nahrad",
                    "image": "files/res/reference/ref-04.jpg"
                }),
            ]
            self.save_data()
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.equipment = [EquipmentItem.from_dict(d) for d in data.get("equipment", [])]
            self.references = [ReferenceItem.from_dict(d) for d in data.get("references", [])]
        except Exception as e:
            messagebox.showerror("Chyba", f"Nepodarilo se nacist data: {e}")

    def save_data(self):
        data = {
            "equipment": [item.to_dict() for item in self.equipment],
            "references": [item.to_dict() for item in self.references]
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _on_close(self):
        self.save_data()
        self.destroy()


if __name__ == "__main__":
    app = DentLifeManager()
    app.mainloop()