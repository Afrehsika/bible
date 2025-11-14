import flet as ft
import json
from pathlib import Path
import sys
import os

# ===============================
# File paths - works both on desktop and in APK
# ===============================
def resolve_data_folder():
    candidates = [
        Path(sys.executable).parent / "data",
        Path(__file__).resolve().parent.parent / "data",
        Path(__file__).resolve().parent / "data",
        Path.cwd() / "data",
    ]
    for c in candidates:
        try:
            if c.exists():
                return c
        except Exception:
            pass
    default = candidates[1]
    try:
        default.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return default

DATA_FOLDER = resolve_data_folder()
DEFAULT_DATA_FILE = DATA_FOLDER / "sample_bible.json"
BOOKMARKS_FILE = DATA_FOLDER / "bible_bookmarks.json"
SETTINGS_FILE = DATA_FOLDER / "bible_settings.json"

# ===============================
# Helpers
# ===============================
def load_data(path: Path = None):
    path = path or DEFAULT_DATA_FILE
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # support list-of-objects format
    if isinstance(data, list):
        new_data = {}
        for entry in data:
            book = entry.get("book")
            chapter = str(entry.get("chapter"))
            verse = str(entry.get("verse"))
            text = entry.get("text", "")
            new_data.setdefault(book, {}).setdefault(chapter, {})[verse] = text
        return new_data
    return data

def list_translations():
    translations = {}
    try:
        if not DATA_FOLDER.exists():
            DATA_FOLDER.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    try:
        for p in DATA_FOLDER.glob("*.json"):
            if p.stem not in ("bible_bookmarks", "bible_settings", "sample_bible"):
                translations[p.stem] = p
            elif p.stem == "sample_bible":
                translations[p.stem] = p
    except Exception:
        pass
    # compatibility: nested *_bible.json
    try:
        for sub in DATA_FOLDER.iterdir():
            if sub.is_dir():
                for p in sub.glob("*_bible.json"):
                    translations[p.stem] = p
    except Exception:
        pass
    return translations

def load_json(path):
    if not Path(path).exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===============================
# Canonical orders (exact names)
# ===============================
OT_ORDER = [
    'Genesis','Exodus','Leviticus','Numbers','Deuteronomy','Joshua','Judges','Ruth',
    '1 Samuel','2 Samuel','1 Kings','2 Kings','1 Chronicles','2 Chronicles','Ezra','Nehemiah','Esther',
    'Job','Psalms','Proverbs','Ecclesiastes','Song of Solomon','Isaiah','Jeremiah','Lamentations',
    'Ezekiel','Daniel','Hosea','Joel','Amos','Obadiah','Jonah','Micah','Nahum','Habakkuk','Zephaniah','Haggai','Zechariah','Malachi'
]

NT_ORDER = [
    'Matthew','Mark','Luke','John','Acts','Romans','1 Corinthians','2 Corinthians','Galatians','Ephesians',
    'Philippians','Colossians','1 Thessalonians','2 Thessalonians','1 Timothy','2 Timothy','Titus','Philemon','Hebrews',
    'James','1 Peter','2 Peter','1 John','2 John','3 John','Jude','Revelation'
]

# ===============================
# Themes
# ===============================
THEMES = {
    "Light": {
        "page_bg": "#ffffff",
        "panel_bg": "#f7f7f7",
        "accent": "#8a6d2f",
        "text": "#111111",
        "muted": "#666666",
    },
    "Dark": {
        "page_bg": "#0b1020",
        "panel_bg": "#121827",
        "accent": "#d4af37",
        "text": "#e6eef8",
        "muted": "#9aa2b3",
    },
    "Parchment": {  # Classic A
        "page_bg": "#f3ead6",
        "panel_bg": "#fbf6ec",
        "accent": "#b57a1b",
        "text": "#2b2b2b",
        "muted": "#6b5a45",
    },
    "Gold": {  # Classic C
        "page_bg": "#ffffff",
        "panel_bg": "#f6f6f6",
        "accent": "#d4af37",
        "text": "#111111",
        "muted": "#777777",
    }
}

# ===============================
# Utility: create highlighted snippet as a row of Text spans
# ===============================
def make_highlighted_snippet(text: str, query: str, accent_color: str, muted_color: str):
    """Return a ft.Row with parts; matched pieces are emphasized (bold + accent color)."""
    if not query:
        return ft.Text(text, size=12, color=muted_color)
    low = text.lower()
    q = query.lower()
    parts = []
    idx = 0
    while True:
        pos = low.find(q, idx)
        if pos == -1:
            remainder = text[idx:]
            if remainder:
                parts.append(("text", remainder))
            break
        # before
        if pos > idx:
            parts.append(("text", text[idx:pos]))
        # match
        parts.append(("match", text[pos:pos+len(q)]))
        idx = pos + len(q)
    spans = []
    for kind, piece in parts:
        if kind == "text":
            spans.append(ft.Text(piece, size=12))
        else:
            spans.append(ft.Text(piece, size=12, weight=ft.FontWeight.BOLD, color=accent_color))
    return ft.Row(spans, wrap=True)

# ===============================
# Main App
# ===============================
class BibleApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.translations = list_translations()
        self.settings = load_json(SETTINGS_FILE)

        # bookmarks
        bm_data = load_json(BOOKMARKS_FILE)
        if isinstance(bm_data, list):
            self.bookmarks = bm_data
        else:
            self.bookmarks = bm_data.get("bookmarks", [])

        # defaults
        self.font_size = self.settings.get("font_size", 16)
        self.current_tab = "read"
        self.selected_translation = (
            self.settings.get("translation")
            if self.settings.get("translation") in self.translations
            else list(self.translations.keys())[0] if self.translations else None
        )
        self.selected_theme = self.settings.get("theme", "Dark")
        if self.selected_theme not in THEMES:
            self.selected_theme = "Dark"

        # load data
        self.data = load_data(self.translations[self.selected_translation]) if self.selected_translation else {}

        # set current position defensively
        self.current_book = list(self.data.keys())[0] if self.data else None
        self.current_chapter = None
        if self.current_book:
            chs = list(self.data[self.current_book].keys())
            self.current_chapter = "1" if "1" in chs else (chs[0] if chs else None)

        # page setup
        page.title = "Bible"
        page.padding = 0
        page.scroll = "adaptive"
        self.apply_theme_to_page()

        # placeholders
        self.book_search = None
        self.search_input = None
        self.search_results = None
        self.verse_input = None

        # build UI
        try:
            page.on_resize = self.on_page_resize
        except Exception:
            pass

        self.build_ui()
        self.current_view = "library"
        self.show_current_view()

    # ===============================
    # Theme helpers
    # ===============================
    def apply_theme_to_page(self):
        t = THEMES.get(self.selected_theme, THEMES["Dark"])
        if self.selected_theme == "Dark":
            self.page.theme_mode = ft.ThemeMode.DARK
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = t["page_bg"]
        self._theme_accent = t["accent"]
        self._theme_panel = t["panel_bg"]
        self._theme_text = t["text"]
        self._theme_muted = t["muted"]

    # ===============================
    # UI Builder
    # ===============================
    def build_ui(self):
        self.header = self.build_topbar()
        self.bottom_nav = self.build_bottom_nav()
        self.content_area = ft.Container(expand=True)

        self.layout = ft.Column(
            [
                self.header,
                ft.Divider(height=1, color="#333" if self.selected_theme == "Dark" else "#ddd"),
                ft.Container(content=self.content_area, expand=True, padding=10, bgcolor=self._theme_panel),
                ft.Divider(height=1, color="#333" if self.selected_theme == "Dark" else "#ddd"),
                self.bottom_nav,
            ],
            expand=True,
            spacing=0,
        )

        self.page.controls.clear()
        self.page.add(ft.SafeArea(content=self.layout, top=True, bottom=True, left=True, right=True))

    def build_topbar(self):
        # translation dropdown
        self.translation_select = ft.Dropdown(
            width=140,
            options=[ft.dropdown.Option(k) for k in self.translations.keys()],
            value=self.selected_translation,
            on_change=self.change_translation,
        )

        # book dropdown
        book_options = [ft.dropdown.Option(b) for b in (self.data.keys() if self.data else [])]
        self.book_select = ft.Dropdown(
            width=160,
            options=book_options,
            value=self.current_book,
            on_change=self.change_book,
        )

        # chapter dropdown
        chapters = []
        if self.current_book and self.current_book in self.data:
            chapters = list(self.data[self.current_book].keys())
            try:
                chapters = sorted(chapters, key=lambda x: int(x) if str(x).isdigit() else x)
            except Exception:
                pass
        self.chapter_select = ft.Dropdown(
            width=80,
            options=[ft.dropdown.Option(c) for c in chapters],
            value=self.current_chapter,
            on_change=self.change_chapter,
        )

        back_btn = ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self.back(), visible=(getattr(self, "current_view", "library") != "library"))
        title = ft.Text("📖 Bible", size=20, weight=ft.FontWeight.BOLD, color=self._theme_text)

        search_btn = ft.IconButton(ft.Icons.SEARCH, on_click=lambda e: self.open_search())

        controls = [title, ft.Container(expand=True), search_btn, self.translation_select]
        if getattr(self, "current_view", "library") != "library":
            controls.insert(0, back_btn)

        return ft.Container(
            ft.Row(controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=self._theme_panel,
            padding=10,
        )

    def build_bottom_nav(self):
        return ft.Container(
            ft.Row(
                [
                    ft.IconButton(ft.Icons.MENU_BOOK, icon_color=self._theme_accent if self.current_tab == "read" else None, on_click=lambda e: self.switch_tab("read")),
                    ft.IconButton(ft.Icons.BOOKMARK, icon_color=self._theme_accent if self.current_tab == "bookmarks" else None, on_click=lambda e: self.switch_tab("bookmarks")),
                    ft.IconButton(ft.Icons.SETTINGS, icon_color=self._theme_accent if self.current_tab == "settings" else None, on_click=lambda e: self.switch_tab("settings")),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            ),
            padding=8,
            bgcolor=self._theme_panel,
        )

    # ===============================
    # View routing
    # ===============================
    def show_current_view(self):
        v = getattr(self, "current_view", "library")
        if v == "library":
            self.show_library_page()
        elif v == "chapters":
            self.show_chapters_page()
        elif v in ("verses", "read"):
            self.show_read_page()
        elif v == "search":
            if hasattr(self, "search_input") and self.search_input:
                self.open_search()
            else:
                self.show_library_page()

    # ===============================
    # Library (books) - NO "Other" section
    # ===============================
    def show_library_page(self):
        if not self.data:
            self.content_area.content = ft.Text("No Bible data available.", size=14, italic=True, color=self._theme_muted)
            self.page.update()
            return

        books = list(self.data.keys())
        ot_books = [b for b in OT_ORDER if b in books]
        nt_books = [b for b in NT_ORDER if b in books]

        grouped = []
        if ot_books:
            grouped.append(("Old Testament", ot_books))
        if nt_books:
            grouped.append(("New Testament", nt_books))

        # search box for books
        if not hasattr(self, "book_search") or self.book_search is None:
            self.book_search = ft.TextField(width=300, hint_text="Search books...", on_change=self.on_search_books)

        query = (self.book_search.value or "").strip().lower()
        def book_matches(bname):
            if not query:
                return True
            return query in bname.lower()

        sections = []
        for heading, blist in grouped:
            filtered = [b for b in blist if book_matches(b)]
            if not filtered:
                continue
            tiles = []
            for b in filtered:
                chap_count = len(self.data.get(b, {}))
                tile = ft.Container(
                    ft.Column([
                        ft.Text(b, size=16, weight=ft.FontWeight.NORMAL, color=self._theme_text),
                        ft.Text(f"{chap_count} chapters", size=12, color=self._theme_muted),
                    ], tight=True, alignment=ft.CrossAxisAlignment.CENTER),
                    width=140,
                    height=76,
                    padding=12,
                    margin=ft.margin.only(4,4,4,4),
                    bgcolor=self._theme_panel,
                    border_radius=8,
                    border=ft.border.all(1, color=self._theme_muted),
                    alignment=ft.alignment.center,
                    on_click=lambda e, book=b: self.open_chapters(book),
                )
                tiles.append(tile)
            sections.append((heading, tiles))

        def columns_for_width():
            try:
                w = int(self.page.width or 0)
            except Exception:
                w = 0
            tile_total_width = 160
            if w <= 0:
                return 3
            cols = max(1, int(w / tile_total_width))
            return min(cols, 6)
        cols = columns_for_width()

        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i+n]

        content_cols = []
        for heading, tiles in sections:
            content_cols.append(ft.Container(ft.Text(heading, size=14, weight=ft.FontWeight.BOLD, color=self._theme_text), padding=6))
            for group in list(chunks(tiles, cols)):
                content_cols.append(ft.Row(group, spacing=8, alignment=ft.MainAxisAlignment.CENTER))

        if query and not content_cols:
            content_cols = [ft.Container(ft.Text("No books found.", color=self._theme_muted), padding=12)]

        body = ft.Column([ft.Row([self.book_search, ft.Container(expand=True)]), ft.Divider(height=1, color="#333" if self.selected_theme == "Dark" else "#ddd"), ft.Column(content_cols, spacing=8, expand=True)], spacing=8, expand=True)

        self.current_view = "library"
        self.header = self.build_topbar()
        self.layout.controls[0] = self.header
        self.content_area.content = body
        self.page.update()

    def on_search_books(self, e):
        try:
            self.book_search.value = (e.control.value or "")
        except Exception:
            pass
        self.show_library_page()

    # ===============================
    # Chapters & verses navigation
    # ===============================
    def open_chapters(self, book):
        self.current_book = book
        chapters = list(self.data.get(book, {}).keys())
        try:
            chapters = sorted(chapters, key=lambda x: int(x) if str(x).isdigit() else x)
        except Exception:
            pass
        self.chapters_current = chapters
        self.current_view = "chapters"
        self.show_chapters_page()

    def show_chapters_page(self):
        if not self.current_book:
            self.show_library_page()
            return
        title = ft.Container(ft.Text(self.current_book, size=18, weight=ft.FontWeight.BOLD, color=self._theme_text), alignment=ft.alignment.center, padding=8)
        tiles = []
        for c in self.chapters_current:
            tile = ft.Container(
                ft.Column([ft.Text(f"Chapter {c}", size=16, color=self._theme_text)], alignment=ft.CrossAxisAlignment.CENTER),
                width=120, height=64, padding=10, margin=ft.margin.only(4,4,4,4),
                bgcolor=self._theme_panel, border_radius=8, border=ft.border.all(1, color=self._theme_muted),
                alignment=ft.alignment.center, on_click=lambda e, ch=c: self.open_verses(self.current_book, ch)
            )
            tiles.append(tile)
        try:
            w = int(self.page.width or 0)
        except Exception:
            w = 0
        tile_total_width = 140
        cols = max(1, int(w / tile_total_width)) if w > 0 else 3
        cols = min(cols, 6)
        rows = []
        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i+n]
        for group in chunks(tiles, cols):
            rows.append(ft.Row(group, spacing=8, alignment=ft.MainAxisAlignment.CENTER))
        body = ft.Column([title, ft.Divider(), ft.Column(rows, expand=True)], spacing=8, expand=True)
        self.header = self.build_topbar()
        self.layout.controls[0] = self.header
        self.content_area.content = body
        self.page.update()

    def open_verses(self, book, chapter):
        self.current_book = book
        self.current_chapter = chapter
        self.current_view = "verses"
        self.header = self.build_topbar()
        self.layout.controls[0] = self.header
        self.show_read_page()

    def back(self):
        cv = getattr(self, "current_view", "library")
        if cv == "search":
            self.current_view = "library"
            self.show_library_page()
        elif cv == "verses":
            self.current_view = "chapters"
            self.show_chapters_page()
        elif cv == "chapters":
            self.current_view = "library"
            self.show_library_page()
        else:
            # on library -> request close
            try:
                # Flet supports window_close in many versions
                self.page.window_close()
            except Exception:
                try:
                    self.page.close()
                except Exception:
                    pass

    # ===============================
    # Read page (verses)
    # ===============================
    def show_read_page(self):
        if not self.data or not self.current_book or not self.current_chapter:
            self.content_area.content = ft.Text("No Bible content available.", size=14, italic=True, color=self._theme_muted)
            self.page.update()
            return

        verses = self.data.get(self.current_book, {}).get(self.current_chapter, {})
        items = list(verses.items())
        try:
            items = sorted(items, key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else kv[0])
        except Exception:
            pass

        start_v = None
        try:
            sv = str(self.verse_input.value).strip() if hasattr(self, 'verse_input') and self.verse_input and getattr(self.verse_input, "value", None) is not None else ""
            if sv:
                start_v = sv
        except Exception:
            start_v = None

        start_idx = 0
        if start_v:
            for i, (vn, _) in enumerate(items):
                try:
                    if int(vn) >= int(start_v):
                        start_idx = i
                        break
                except Exception:
                    if str(vn) >= str(start_v):
                        start_idx = i
                        break

        header_title = ft.Container(
            ft.Row([
                ft.Text(f"{self.current_book} {self.current_chapter}", size=18, weight=ft.FontWeight.BOLD, color=self._theme_text),
                ft.Container(expand=True),
                ft.TextField(width=80, hint_text="verse", on_submit=self.on_goto_verse, value=(str(start_v) if start_v else "")),
            ], alignment=ft.MainAxisAlignment.START),
            alignment=ft.alignment.center,
            padding=8,
        )

        verse_list = ft.ListView(spacing=6, expand=True)
        for vnum, text in items[start_idx:]:
            verse_bg = self._theme_panel
            textfield = ft.TextField(value=str(text), read_only=True, multiline=True, expand=True, text_style=ft.TextStyle(size=self.font_size), bgcolor=verse_bg, border_color=verse_bg)
            def make_copy_handler(book, chapter, vn, t):
                def _copy(e):
                    try:
                        copy_text = f"{book} {chapter}:{vn} — {t}"
                        self.page.set_clipboard(copy_text)
                        self.page.snack_bar = ft.SnackBar(ft.Text("Copied to clipboard"))
                        self.page.snack_bar.open = True
                        self.page.update()
                    except Exception:
                        pass
                return _copy
            verse_row = ft.Row([
                ft.Container(ft.Text(str(vnum), size=self.font_size, color=self._theme_text), width=48, alignment=ft.alignment.center_left),
                textfield,
                ft.IconButton(ft.Icons.CONTENT_COPY, on_click=make_copy_handler(self.current_book, self.current_chapter, vnum, text))
            ], alignment=ft.MainAxisAlignment.START)
            verse_list.controls.append(ft.Container(verse_row, bgcolor=verse_bg, border_radius=8, padding=10, on_click=lambda e, b=self.current_book, c=self.current_chapter, v=vnum: self.add_bookmark(b,c,v)))

        self.content_area.content = ft.Column([header_title, ft.Divider(), verse_list], spacing=8, expand=True)
        self.page.update()

    def on_goto_verse(self, e):
        try:
            val = str(e.control.value).strip()
            if val:
                self.verse_input = ft.TextField(value=val)
                self.show_read_page()
        except Exception:
            pass

    # ===============================
    # Bookmarks & Settings
    # ===============================
    def show_bookmarks_page(self):
        if not self.bookmarks:
            self.content_area.content = ft.Text("No bookmarks yet.", size=14, italic=True, color=self._theme_muted)
            self.page.update()
            return
        items = ft.Column([ft.Container(ft.Row([ft.Text(f"{b['book']} {b['chapter']}:{b['verse']}", size=16, color=self._theme_text), ft.Container(expand=True), ft.IconButton(ft.Icons.OPEN_IN_NEW, on_click=lambda e, b=b: self.open_verses(b['book'], b['chapter']))]), bgcolor=self._theme_panel, padding=8, border_radius=6) for b in self.bookmarks], spacing=8)
        self.content_area.content = items
        self.page.update()

    def show_settings_page(self):
        theme_options = [ft.dropdown.Option(k) for k in THEMES.keys()]
        self.theme_select = ft.Dropdown(width=160, options=theme_options, value=self.selected_theme, on_change=self.change_theme)

        body = ft.Column([
            ft.Text("Settings", size=20, weight=ft.FontWeight.BOLD, color=self._theme_text),
            ft.Divider(),
            ft.Row([ft.Text("Font Size:", color=self._theme_text), ft.IconButton(ft.Icons.REMOVE, on_click=lambda e: self.adjust_font(-1)), ft.Text(str(self.font_size), color=self._theme_text), ft.IconButton(ft.Icons.ADD, on_click=lambda e: self.adjust_font(1))]),
            ft.Row([ft.Text("Theme:", color=self._theme_text), self.theme_select]),
            ft.Row([ft.Text("Translation:", color=self._theme_text), ft.Text(self.selected_translation or "None", color=self._theme_muted)]),
        ], spacing=16)
        self.content_area.content = body
        self.page.update()

    def change_theme(self, e):
        try:
            val = e.control.value
            if val and val in THEMES:
                self.selected_theme = val
                self.apply_theme_to_page()
                self.save_settings()
                self.build_ui()
                # refresh view
                if self.current_tab == "read":
                    self.show_read_page()
                elif self.current_tab == "bookmarks":
                    self.show_bookmarks_page()
                elif self.current_tab == "settings":
                    self.show_settings_page()
        except Exception:
            pass

    def switch_tab(self, tab):
        self.current_tab = tab
        self.header = self.build_topbar()
        self.layout.controls[0] = self.header
        if tab == "read":
            self.show_read_page()
        elif tab == "bookmarks":
            self.show_bookmarks_page()
        elif tab == "settings":
            self.show_settings_page()
        self.bottom_nav = self.build_bottom_nav()
        self.layout.controls[-1] = self.bottom_nav
        self.page.update()

    def add_bookmark(self, book, chapter, verse):
        bm = {"book": book, "chapter": chapter, "verse": verse}
        if bm not in self.bookmarks:
            self.bookmarks.append(bm)
            save_json(BOOKMARKS_FILE, {"bookmarks": self.bookmarks})
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Added {book} {chapter}:{verse} to bookmarks"))
            self.page.snack_bar.open = True
            self.page.update()

    def save_settings(self):
        save_json(SETTINGS_FILE, {"font_size": self.font_size, "translation": self.selected_translation, "theme": self.selected_theme})

    # ===============================
    # Font adjust (fixed)
    # ===============================
    def adjust_font(self, delta):
        new_size = self.font_size + delta
        if new_size < 10:
            new_size = 10
        if new_size > 40:
            new_size = 40
        self.font_size = new_size
        self.save_settings()
        # refresh read page if active
        if self.current_tab == "read" and getattr(self, "current_view", "") in ("verses","read"):
            self.show_read_page()
        else:
            # refresh settings page text
            if getattr(self, "current_view", "") == "settings":
                self.show_settings_page()
        self.page.update()

    # ===============================
    # Translation handlers (preserve book/chapter)
    # ===============================
    def change_translation(self, e):
        val = e.control.value
        if val and val in self.translations:
            self.selected_translation = val
            new_data = load_data(self.translations[val]) or {}
            old_book = self.current_book
            old_chapter = self.current_chapter

            self.data = new_data
            books = list(self.data.keys())
            self.book_select.options = [ft.dropdown.Option(b) for b in books]

            # restore old book/chapter when available
            if old_book in books:
                self.current_book = old_book
                self.book_select.value = old_book
            else:
                self.current_book = books[0] if books else None
                self.book_select.value = self.current_book

            if self.current_book and self.current_book in self.data:
                chapters = list(self.data[self.current_book].keys())
                try:
                    chapters = sorted(chapters, key=lambda x: int(x) if str(x).isdigit() else x)
                except Exception:
                    pass
                self.chapter_select.options = [ft.dropdown.Option(c) for c in chapters]
                if old_chapter in chapters:
                    self.current_chapter = old_chapter
                    self.chapter_select.value = old_chapter
                else:
                    self.current_chapter = chapters[0] if chapters else None
                    self.chapter_select.value = self.current_chapter
            else:
                self.chapter_select.options = []
                self.chapter_select.value = None
                self.current_chapter = None

            self.save_settings()
            if getattr(self, "current_view", "library") in ("read", "verses") and self.current_book and self.current_chapter:
                self.header = self.build_topbar()
                self.layout.controls[0] = self.header
                self.show_read_page()
            else:
                if getattr(self, "current_view", "library") == "chapters" and self.current_book:
                    self.open_chapters(self.current_book)
                else:
                    self.show_library_page()

    def change_book(self, e):
        new_book = self.book_select.value
        if not new_book:
            return
        self.current_book = new_book
        chapters = list(self.data.get(self.current_book, {}).keys())
        try:
            chapters = sorted(chapters, key=lambda x: int(x) if str(x).isdigit() else x)
        except Exception:
            pass
        self.chapter_select.options = [ft.dropdown.Option(c) for c in chapters]
        if self.current_chapter in chapters:
            self.chapter_select.value = self.current_chapter
        else:
            self.current_chapter = chapters[0] if chapters else None
            self.chapter_select.value = self.current_chapter
        if getattr(self, "current_view", "library") == "chapters":
            self.show_chapters_page()
        else:
            self.show_read_page()

    def change_chapter(self, e):
        self.current_chapter = e.control.value
        self.show_read_page()

    # ===============================
    # Search (improved)
    # ===============================
    def open_search(self):
        self.search_input = ft.TextField(hint_text="Search scripture (words, book, or reference)...", expand=True, on_submit=self.run_search)
        self.search_results = ft.Column(spacing=8, expand=True)
        body = ft.Column([ft.Row([self.search_input]), ft.Divider(), self.search_results], spacing=8, expand=True)
        self.current_view = "search"
        self.header = self.build_topbar()
        self.layout.controls[0] = self.header
        self.content_area.content = body
        self.page.update()

    def run_search(self, e):
        query = (self.search_input.value or "").strip()
        qlow = query.lower()
        self.search_results.controls.clear()
        if not query:
            self.search_results.controls.append(ft.Text("Type a search term and press Enter.", color=self._theme_muted))
            self.page.update()
            return

        results = 0
        max_results = 500
        for book, chaps in self.data.items():
            book_low = book.lower()
            for chap, verses in chaps.items():
                for vnum, text in verses.items():
                    if results >= max_results:
                        break
                    text_str = str(text)
                    text_low = text_str.lower()
                    matched = False
                    if qlow == f"{book_low} {chap}:{vnum}".lower() or qlow == f"{book_low} {chap}".lower():
                        matched = True
                    elif qlow in book_low:
                        matched = True
                    elif qlow in text_low:
                        matched = True

                    if matched:
                        if qlow in text_low:
                            idx = text_low.find(qlow)
                            start = max(0, idx - 30)
                            end = min(len(text_str), idx + len(query) + 60)
                            snippet = text_str[start:end].strip()
                            if start > 0:
                                snippet = "..." + snippet
                            if end < len(text_str):
                                snippet = snippet + "..."
                        else:
                            snippet = text_str[:140] + ("..." if len(text_str) > 140 else "")

                        snippet_row = make_highlighted_snippet(snippet, query, self._theme_accent, self._theme_muted)

                        result_item = ft.Container(
                            ft.Column([
                                ft.Row([ft.Text(f"{book} {chap}:{vnum}", weight=ft.FontWeight.BOLD, color=self._theme_text), ft.Container(expand=True), ft.IconButton(ft.Icons.OPEN_IN_NEW, on_click=lambda e, b=book, c=chap: self.open_verses(b, c))]),
                                snippet_row
                            ]),
                            bgcolor=self._theme_panel,
                            padding=8,
                            border_radius=6,
                            on_click=lambda e, b=book, c=chap, v=vnum: self.open_verse_from_search(b, c, v)
                        )
                        self.search_results.controls.append(result_item)
                        results += 1
                if results >= max_results:
                    break
            if results >= max_results:
                break

        if results == 0:
            self.search_results.controls.append(ft.Text("No results found.", color=self._theme_muted))
        else:
            self.search_results.controls.insert(0, ft.Text(f"{results} result(s)", color=self._theme_muted))

        self.page.update()

    def open_verse_from_search(self, book, chapter, verse):
        try:
            self.current_book = book
            self.current_chapter = chapter
            self.verse_input = ft.TextField(value=str(verse))
            self.current_view = "verses"
            self.header = self.build_topbar()
            self.layout.controls[0] = self.header
            self.show_read_page()
        except Exception:
            try:
                self.current_book = book
                self.current_chapter = chapter
                self.current_view = "verses"
                self.header = self.build_topbar()
                self.layout.controls[0] = self.header
                self.show_read_page()
            except Exception:
                pass

    # ===============================
    # Misc
    # ===============================
    def on_page_resize(self, e):
        try:
            if getattr(self, "current_view", "library") == "library":
                self.show_library_page()
            elif getattr(self, "current_view", "chapters") == "chapters":
                self.show_chapters_page()
        except Exception:
            pass

# ===============================
# Run
# ===============================
def main(page: ft.Page):
    app = BibleApp(page)

    # Handle Android / hardware back button and window events
    def on_window_event(e):
        try:
            # e.data can be "back", "close", "popRoute" depending on platform/version
            if getattr(e, "data", None) in ("back", "close", "popRoute"):
                app.back()
                # return True to signal we've handled the event where supported
                return True
        except Exception:
            pass
        return None

    try:
        page.on_window_event = on_window_event
    except Exception:
        # older/newer flet versions may not support on_window_event assignment; ignore safely
        pass

if __name__ == "__main__":
    ft.app(target=main)
