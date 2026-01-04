import flet as ft
import json
from pathlib import Path
import sys
import os
try:
    from tts_service import TTSEngine
    HAS_TTS = True
except ImportError:
    HAS_TTS = False


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

# Audio assets (for mobile compatibility)
# This assumes src/main.py -> parent is src -> parent is project root.
# We want project_root/src/assets/audio_cache to be served.
# Flet usually serves 'assets' folder adjacent to main.py or defined in app.
# We will assume 'src/assets' is the dir.
ASSETS_DIR = Path(__file__).parent / "assets"
AUDIO_ASSETS_DIR = ASSETS_DIR / "audio_cache"


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
                name = p.stem
                if name.endswith("_bible"):
                    name = name[:-6]
                translations[name] = p
            elif p.stem == "sample_bible":
                translations[p.stem] = p
    except Exception:
        pass
    # compatibility: nested *_bible.json
    try:
        for sub in DATA_FOLDER.iterdir():
            if sub.is_dir():
                for p in sub.glob("*_bible.json"):
                    name = p.stem
                    if name.endswith("_bible"):
                        name = name[:-6]
                    translations[name] = p
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
    'Job','Psalm','Proverbs','Ecclesiastes','Song of Solomon','Isaiah','Jeremiah','Lamentations',
    'Ezekiel','Daniel','Hosea','Joel','Amos','Obadiah','Jonah','Micah','Nahum','Habakkuk','Zephaniah','Haggai','Zechariah','Malachi'
]

NT_ORDER = [
    'Matthew','Mark','Luke','John','Acts','Romans','1 Corinthians','2 Corinthians','Galatians','Ephesians',
    'Philippians','Colossians','1 Thessalonians','2 Thessalonians','1 Timothy','2 Timothy','Titus','Philemon','Hebrews',
    'James','1 Peter','2 Peter','1 John','2 John','3 John','Jude','Revelation'
]

TWI_OT_ORDER = [
    'Gyenesis','Eksodɔs','Lewitikɔs','Numeri','Deuteronomium','Yosua','Atemmufoɔ','Rut',
    '1 Samuel','2 Samuel','1 Ahemfo','2 Ahemfo','1 Berɛsosɛm','2 Berɛsosɛm','Esra','Nehemia','Ester',
    'Hiob','Nnwom','Mmebusɛm','Ɔsɛnkafoɔ','Nnwom Mu Dwom','Yesaia','Yeremia','Kwadwom',
    'Hesekiel','Daniel','Hosea','Yoel','Amos','Obadia','Yona','Mika','Nahum','Habakuk','Sefania','Hagai','Sakaria','Malaki'
]

TWI_NT_ORDER = [
    'Mateo','Marko','Luka','Yohane','Asomafoɔ','Romafoɔ','1 Korintofoɔ','2 Korintofoɔ','Galatifoɔ','Efesofoɔ',
    'Filipifoɔ','Kolosefoɔ','1 Tesalonikafoɔ','2 Tesalonikafoɔ','1 Timoteo','2 Timoteo','Tito','Filemon','Hebrifoɔ',
    'Yakobo','1 Petro','2 Petro','1 Yohane','2 Yohane','3 Yohane','Yuda','Adiyisɛm'
]

# ===============================
# Book Mapping (English <-> Twi)
# ===============================
ENGLISH_TO_TWI = dict(zip(OT_ORDER, TWI_OT_ORDER))
ENGLISH_TO_TWI.update(dict(zip(NT_ORDER, TWI_NT_ORDER)))
# Invert for Twi -> English
TWI_TO_ENGLISH = {v: k for k, v in ENGLISH_TO_TWI.items()}


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
        "page_bg": "#f5e6c4",
        "panel_bg": "#ebd5a0",
        "accent": "#a67c00",
        "text": "#2b2b2b",
        "muted": "#755d35",
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
        
        # TTS Engine
        self.tts = TTSEngine() if HAS_TTS else None
        
        # Preload models in background
        if self.tts:
            import threading
            def _preload():
                print("Preloading TTS models...")
                self.tts.preload("aka") # Twi
                self.tts.preload("eng")
                print("TTS models preloaded.")
            threading.Thread(target=_preload, daemon=True).start()

        # Defers audio player creation until play
        self.audio_player = None
        self.audio_playlist = []
        self.audio_current_idx = 0
        self.is_generating_audio = False
        self.is_playing = False




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
        page.scroll = None
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
        
        # Handle Android back button
        self.page.on_back_button_pressed = self.on_back_button

    def on_back_button(self, e):
        try:
            # Debug: show we caught the event
            # self.page.snack_bar = ft.SnackBar(ft.Text(f"Back pressed. View: {self.current_view}"))
            # self.page.snack_bar.open = True
            # self.page.update()

            if self.current_view != "library":
                self.back()
                return True
            else:
                return False # Let OS handle library (exit)
        except Exception as ex:
            print(f"Error in back button: {ex}")
            return True # Prevent exit on error



            print(f"Error in back button: {ex}")
            return True # Prevent exit on error

    def update_fab(self):
        if hasattr(self, "current_view") and self.current_view != "library":
            self.page.floating_action_button = ft.FloatingActionButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=lambda e: self.back(),
                bgcolor=self._theme_accent,
                content=ft.Icon(ft.Icons.ARROW_BACK, color=self._theme_panel) # Contrast
            )
        else:
            self.page.floating_action_button = None
        self.page.update()

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
        self.page.add(ft.SafeArea(content=self.layout, top=True, bottom=True, left=True, right=True, expand=True))

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
        self.update_fab()

    # ===============================
    # Library (books) - NO "Other" section
    # ===============================
    def show_library_page(self):
        if not self.data:
            self.content_area.content = ft.Text("No Bible data available.", size=14, italic=True, color=self._theme_muted)
            self.page.update()
            return

        books = list(self.data.keys())
        
        # Determine which order lists to use
        current_trans = getattr(self, "selected_translation", "")
        is_twi = (current_trans == "TWI")
        
        target_ot = TWI_OT_ORDER if is_twi else OT_ORDER
        target_nt = TWI_NT_ORDER if is_twi else NT_ORDER
        
        ot_books = [b for b in target_ot if b in books]
        nt_books = [b for b in target_nt if b in books]

        grouped = []
        if ot_books:
            grouped.append(("Old Testament" if not is_twi else "Apam Dedaw", ot_books))
        if nt_books:
            grouped.append(("New Testament" if not is_twi else "Apam Foforo", nt_books))


        sections = []
        for heading, blist in grouped:
            # filtered = [b for b in blist if book_matches(b)]
            filtered = blist
            if not filtered:
                continue
            tiles = []
            for b in filtered:
                chap_count = len(self.data.get(b, {}))
                tile = ft.Container(
                    ft.Column([
                        ft.Text(b, size=16, weight=ft.FontWeight.NORMAL, color=self._theme_text, text_align=ft.TextAlign.CENTER, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(f"{chap_count} chapters", size=12, color=self._theme_muted),
                    ], tight=True, alignment=ft.CrossAxisAlignment.CENTER),
                    width=140,
                    height=90,
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
                content_cols.append(ft.Row(group, alignment=ft.MainAxisAlignment.CENTER, spacing=0))

        if not content_cols:
            self.content_area.content = ft.Text("No books found.", italic=True, color=self._theme_muted)
        else:
            self.content_area.content = ft.ListView(content_cols, expand=True, padding=10)
        self.header = self.build_topbar()
        self.page.update()

    def open_chapters(self, book):
        self.current_book = book
        self.current_view = "chapters"
        self.show_current_view()

    def show_chapters_page(self):
        if not self.current_book or self.current_book not in self.data:
            self.show_library_page()
            return

        chapters = list(self.data[self.current_book].keys())
        try:
            chapters = sorted(chapters, key=lambda x: int(x) if str(x).isdigit() else x)
        except Exception:
            pass

        tiles = []
        for c in chapters:
            tile = ft.Container(
                ft.Text(c, size=16, weight=ft.FontWeight.BOLD, color=self._theme_text),
                width=60,
                height=60,
                bgcolor=self._theme_panel,
                border_radius=8,
                border=ft.border.all(1, color=self._theme_muted),
                alignment=ft.alignment.center,
                on_click=lambda e, ch=c: self.open_read(ch),
            )
            tiles.append(tile)

        grid = ft.GridView(
            runs_count=5,
            max_extent=70,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
            controls=tiles,
        )
        
        heading = ft.Text(f"{self.current_book}", size=20, weight=ft.FontWeight.BOLD, color=self._theme_text)
        self.content_area.content = ft.Column([heading, ft.Divider(), ft.Container(grid, expand=True)], spacing=10)
        self.header = self.build_topbar()
        self.page.update()

    def open_read(self, chapter):
        self.current_chapter = chapter
        self.current_view = "read"
        self.show_current_view()

    def back(self):
        if self.current_view in ("read", "verses"):
            self.current_view = "chapters"
        elif self.current_view == "chapters":
            self.current_view = "library"
        else:
            self.current_view = "library"
        self.show_current_view()

    def open_verses(self, book, chapter):
        """Helper to jump directly to a chapter's verses."""
        self.current_book = book
        self.current_chapter = chapter
        self.current_view = "read"
        self.show_current_view()

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

        # Navigation Header
        # Books button (Library), Prev Chapter, Title, Next Chapter
        nav_controls = [
            ft.IconButton(ft.Icons.MENU_BOOK, tooltip="Library", icon_size=20, on_click=lambda e: self.show_library_page()),
            ft.VerticalDivider(width=1, color=self._theme_muted),
            ft.IconButton(ft.Icons.CHEVRON_LEFT, tooltip="Previous Chapter", icon_size=24, on_click=lambda e: self.go_to_previous_chapter()),
            ft.Container(
                ft.Text(f"{self.current_book} {self.current_chapter}", size=16, weight=ft.FontWeight.BOLD, color=self._theme_text, text_align=ft.TextAlign.CENTER),
                expand=True, alignment=ft.alignment.center
            ),
            ft.IconButton(ft.Icons.CHEVRON_RIGHT, tooltip="Next Chapter", icon_size=24, on_click=lambda e: self.go_to_next_chapter()),
            ft.VerticalDivider(width=1, color=self._theme_muted),
            ft.Container(
                 ft.TextField(width=70, hint_text="Vs", content_padding=5, text_size=12, on_submit=self.on_goto_verse, value=(str(start_v) if start_v else ""), border_radius=4, text_align=ft.TextAlign.CENTER),
                 padding=ft.padding.only(left=5)
            )
        ]



        if HAS_TTS:
            icon = ft.Icons.PAUSE if self.is_playing else ft.Icons.PLAY_ARROW
            nav_controls.append(
                ft.IconButton(icon, tooltip="Play/Pause Audio", icon_size=24, on_click=lambda e: self.toggle_chapter_audio())
            )

        header_title = ft.Container(
            ft.Row(nav_controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=0),
            padding=ft.padding.symmetric(vertical=4, horizontal=0),
            bgcolor=self._theme_panel,
        )


        verse_list = ft.ListView(spacing=6, expand=True)
        for vnum, text in items[start_idx:]:
            verse_bg = self._theme_panel
            # Use a slightly different bg for textfield to distinguish? No, keep it clean.
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
                ft.Container(ft.Text(str(vnum), size=self.font_size, color=self._theme_text, weight=ft.FontWeight.BOLD), width=40, alignment=ft.alignment.top_right, padding=ft.padding.only(top=10, right=5)),
                textfield,
                ft.IconButton(ft.Icons.CONTENT_COPY, icon_size=16, on_click=make_copy_handler(self.current_book, self.current_chapter, vnum, text))
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START)
            verse_list.controls.append(ft.Container(verse_row, bgcolor=verse_bg, border_radius=8, padding=5, on_click=lambda e, b=self.current_book, c=self.current_chapter, v=vnum: self.add_bookmark(b,c,v)))

        # Swipe Detector
        swipe_detector = ft.GestureDetector(
            content=verse_list,
            on_horizontal_drag_end=self.on_swipe,
            expand=True
        )

        self.content_area.content = ft.Column([header_title, ft.Divider(height=1, thickness=1, color=self._theme_muted), swipe_detector], spacing=0, expand=True)
        self.page.update()

        # Optimistic generation: Start generating the first chunk in background
        if HAS_TTS and self.tts:
            self._optimistic_generate_first_chunk()


    def on_goto_verse(self, e):
        try:
            val = str(e.control.value).strip()
            if val:
                self.verse_input = ft.TextField(value=val)
                self.show_read_page()
        except Exception:
            pass

    # ===============================
    # Navigation Logic
    # ===============================
    def on_swipe(self, e: ft.DragEndEvent):
        # Threshold for swipe velocity
        if e.primary_velocity is None:
            return
        if e.primary_velocity > 400: # Swipe Right -> Previous
             self.go_to_previous_chapter()
        elif e.primary_velocity < -400: # Swipe Left -> Next
             self.go_to_next_chapter()

    def get_ordered_books(self):
        books = list(self.data.keys())
        current_trans = getattr(self, "selected_translation", "")
        is_twi = (current_trans == "TWI")
        target_ot = TWI_OT_ORDER if is_twi else OT_ORDER
        target_nt = TWI_NT_ORDER if is_twi else NT_ORDER
        
        ordered = []
        # Filter and order
        for b in target_ot:
            if b in books: ordered.append(b)
        for b in target_nt:
            if b in books: ordered.append(b)
            
        # Append any unknown books
        known_set = set(ordered)
        for b in books:
            if b not in known_set:
                ordered.append(b)
        return ordered

    def go_to_next_chapter(self):
        if not self.current_book or not self.current_chapter:
            return
        
        chapters = list(self.data.get(self.current_book, {}).keys())
        try:
             chapters = sorted(chapters, key=lambda x: int(x) if str(x).isdigit() else x)
        except:
             pass
        
        try:
            curr_idx = chapters.index(str(self.current_chapter))
        except ValueError:
            curr_idx = -1
        
        # Check if next chapter exists in current book
        if curr_idx != -1 and curr_idx < len(chapters) - 1:
            self.current_chapter = chapters[curr_idx + 1]
            self.show_read_page()
            return

        # Go to next book
        all_books = self.get_ordered_books()
        try:
            b_idx = all_books.index(self.current_book)
        except ValueError:
            return

        if b_idx < len(all_books) - 1:
            next_book = all_books[b_idx + 1]
            nb_chapters = list(self.data.get(next_book, {}).keys())
            try:
                nb_chapters = sorted(nb_chapters, key=lambda x: int(x) if str(x).isdigit() else x)
            except:
                pass
            if nb_chapters:
                self.current_book = next_book
                self.current_chapter = nb_chapters[0]
                self.show_read_page()
            else:
                 # Empty book? Skip
                 pass

    def go_to_previous_chapter(self):
        if not self.current_book or not self.current_chapter:
            return
        
        chapters = list(self.data.get(self.current_book, {}).keys())
        try:
             chapters = sorted(chapters, key=lambda x: int(x) if str(x).isdigit() else x)
        except:
             pass
        
        try:
            curr_idx = chapters.index(str(self.current_chapter))
        except ValueError:
            curr_idx = -1
        
        # Check if prev chapter exists in current book
        if curr_idx > 0:
            self.current_chapter = chapters[curr_idx - 1]
            self.show_read_page()
            return

        # Go to previous book (last chapter)
        all_books = self.get_ordered_books()
        try:
            b_idx = all_books.index(self.current_book)
        except ValueError:
            return
            
        if b_idx > 0:
            prev_book = all_books[b_idx - 1]
            pb_chapters = list(self.data.get(prev_book, {}).keys())
            try:
                pb_chapters = sorted(pb_chapters, key=lambda x: int(x) if str(x).isdigit() else x)
            except:
                pass
            if pb_chapters:
                self.current_book = prev_book
                self.current_chapter = pb_chapters[-1] # Last chapter
                self.show_read_page()

    # ===============================
    # Bookmarks & Settings
    # ===============================
    def show_bookmarks_page(self):
        if not self.bookmarks:
            self.content_area.content = ft.Text("No bookmarks yet.", size=14, italic=True, color=self._theme_muted)
            self.page.update()
            return
        items = ft.ListView([ft.Container(ft.Row([ft.Text(f"{b['book']} {b['chapter']}:{b['verse']}", size=16, color=self._theme_text), ft.Container(expand=True), ft.IconButton(ft.Icons.OPEN_IN_NEW, on_click=lambda e, b=b: self.open_verses(b['book'], b['chapter']))]), bgcolor=self._theme_panel, padding=8, border_radius=6) for b in self.bookmarks], spacing=8, expand=True)
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
        ], spacing=16, scroll="auto", expand=True)
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

            # restore old book/chapter when available, or map it
            new_book_target = None
            if old_book in books:
                new_book_target = old_book
            else:
                # Try English -> Twi
                if old_book in ENGLISH_TO_TWI:
                    mapped = ENGLISH_TO_TWI[old_book]
                    if mapped in books:
                        new_book_target = mapped
                # Try Twi -> English
                if not new_book_target and old_book in TWI_TO_ENGLISH:
                    mapped = TWI_TO_ENGLISH[old_book]
                    if mapped in books:
                        new_book_target = mapped

            if new_book_target:
                self.current_book = new_book_target
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
        self.update_fab()
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
    def toggle_chapter_audio(self):
        if not self.tts:
            self.page.snack_bar = ft.SnackBar(ft.Text("TTS not available."))
            self.page.snack_bar.open = True
            self.page.update()
            return

        # If we have a player, toggle it
        if self.audio_player:
            if self.is_playing:
                print("DEBUG: Pausing...")
                self.audio_player.pause()
                self.is_playing = False
                self.page.snack_bar = ft.SnackBar(ft.Text("Paused"))
            else:
                print("DEBUG: Resuming...")
                self.audio_player.resume()
                self.is_playing = True
                self.page.snack_bar = ft.SnackBar(ft.Text("Resumed"))
            self.page.snack_bar.open = True
            self.page.update()
            # Update icon
            self.show_read_page() 
            return

        # Otherwise start fresh
        self.start_chapter_audio()

    def start_chapter_audio(self):
        if not self.tts:
            self.page.snack_bar = ft.SnackBar(ft.Text("TTS not available (missing libraries?)"))
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        self.is_playing = True
        self.show_read_page() # update icon

        # Stop any existing playback (cleanup)
        if self.audio_player:
            try:
                self.audio_player.pause()
                self.page.overlay.remove(self.audio_player)
                self.audio_player = None
            except Exception:
                pass

        book = self.current_book
        chapter = self.current_chapter
        lang = "aka" if self.selected_translation == "TWI" else "eng"
        
        # Get text
        verses = self.data.get(book, {}).get(chapter, {})
        if not verses:
            return
            
        # Sort verses
        sorted_verses = sorted(verses.items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else x[0])
        
        # Prepare chunks (e.g., 5 verses per chunk)
        chunk_size = 5
        chunks = []
        current_chunk = []
        
        for i, (vnum, text) in enumerate(sorted_verses):
            current_chunk.append(text)
            if len(current_chunk) >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        if not chunks:
            return

        # Reset state
        self.audio_playlist = [None] * len(chunks) # Placeholders
        self.audio_current_idx = 0
        self.is_generating_audio = True
        
        self.page.snack_bar = ft.SnackBar(ft.Text(f"Starting audio for {book} {chapter} ({lang})..."))
        self.page.snack_bar.open = True
        self.page.update()

        # Define Audio Player with on_state_changed
        def on_audio_state_changed(e):
            if e.data == "completed":
                self.play_next_chunk()

        self.audio_player = ft.Audio(
            src="", 
            autoplay=False,
            on_state_changed=on_audio_state_changed
        )
        self.page.overlay.append(self.audio_player)
        self.page.update()

        # Background Playback Manager
        import threading
        
        def generator_thread():
            try:
                AUDIO_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
                
            for i, text_chunk in enumerate(chunks):
                # If user navigated away or stopped (basic check)
                if not self.is_generating_audio:
                    return

                filename = f"{book}_{chapter}_{lang}_chunk_{i}.wav".replace(" ", "_")
                filepath = AUDIO_ASSETS_DIR / filename
                
                if not filepath.exists():
                    # Generate
                    print(f"Generating chunk {i}...")
                    try:
                        success = self.tts.generate_audio(text_chunk, lang, str(filepath))
                        if not success:
                            continue
                    except Exception as e:
                        print(f"Gen Error: {e}")
                        continue
                else:
                    print(f"Chunk {i} cached.")
                
                # Update playlist safely
                if self.is_generating_audio: # Basic flag check
                    # Use relative URL for Flet asset
                    self.audio_playlist[i] = f"/audio_cache/{filename}"
                    
                    # If this is the *first* chunk, start playing immediately
                    if i == 0:
                        self.play_next_chunk()
        
        threading.Thread(target=generator_thread, daemon=True).start()

    def play_next_chunk(self):
        print(f"DEBUG: play_next_chunk called. Index: {self.audio_current_idx}")
        # Find next available chunk to play
        if self.audio_current_idx >= len(self.audio_playlist):
            self.page.snack_bar = ft.SnackBar(ft.Text("Audio finished."))
            self.page.snack_bar.open = True
            self.is_playing = False # Reset state
            self.show_read_page()   # Reset icon
            self.page.update()
            return

        # Check if current chunk is ready
        next_src = self.audio_playlist[self.audio_current_idx]
        print(f"DEBUG: Next src: {next_src}")
        
        if next_src:
            # Play it
            print(f"DEBUG: Playing {next_src}")
            self.is_playing = True # Ensure state
            self.audio_player.src = next_src
            self.audio_player.autoplay = True
            self.audio_player.update()
            self.audio_current_idx += 1
        else:
            # Not ready yet? Wait a bit and retry? 
            print("DEBUG: Chunk not ready, buffering...")
            # Simple polling fallback
            self.page.snack_bar = ft.SnackBar(ft.Text("Buffering..."))
            self.page.snack_bar.open = True
            self.page.update()
            
            def retry_later():
                import time
                for _ in range(10): # Wait up to 5 seconds
                    time.sleep(0.5)
                    if self.audio_current_idx < len(self.audio_playlist) and self.audio_playlist[self.audio_current_idx]:
                        print("DEBUG: Retry found content, playing...")
                        self.play_next_chunk()
                        return
                print("DEBUG: Retry timed out.")
                
            import threading
            threading.Thread(target=retry_later, daemon=True).start()

    def _optimistic_generate_first_chunk(self):
        """Generates the first audio chunk for the current chapter in background."""
        if not self.current_book or not self.current_chapter:
            return
            
        book = self.current_book
        chapter = self.current_chapter
        lang = "aka" if self.selected_translation == "TWI" else "eng"
        
        # 1. Get first chunk text (same logic as play_chapter_audio)
        verses = self.data.get(book, {}).get(chapter, {})
        if not verses:
            return
        
        # Sort
        sorted_verses = sorted(verses.items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else x[0])
        
        chunk_size = 5
        first_chunk_text = ""
        current_chunk = []
        for i, (vnum, text) in enumerate(sorted_verses):
            current_chunk.append(text)
            if len(current_chunk) >= chunk_size:
                first_chunk_text = " ".join(current_chunk)
                break # Only need the first one
        
        if not first_chunk_text and current_chunk:
             first_chunk_text = " ".join(current_chunk)
             
        if not first_chunk_text:
            return

        # 2. Check if file exists
        filename = f"{book}_{chapter}_{lang}_chunk_0.wav".replace(" ", "_")
        filepath = AUDIO_ASSETS_DIR / filename
        
        if filepath.exists():
            return # Already ready

        # 3. Generate in thread
        import threading
        def _gen():
            try:
                # Ensure directory
                AUDIO_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
                # Generate
                if not filepath.exists():
                     self.tts.generate_audio(first_chunk_text, lang, str(filepath))
            except Exception as e:
                print(f"Optimistic gen failed: {e}")
        
        threading.Thread(target=_gen, daemon=True).start()

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

    # Removed conflicting on_window_event handler to allow page.on_back_button_pressed to work correctly
    pass

if __name__ == "__main__":
    # Ensure assets dir exists
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    ft.app(target=main, assets_dir="assets")

