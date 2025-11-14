import flet as ft
import json
from pathlib import Path
import sys
import os
import traceback

# ===============================
# File paths - works both on desktop and in APK
# ===============================
# On desktop: data is in parent/data
# On APK: data is bundled and accessed via sys.frozen or app data
def resolve_data_folder():
    """Return a Path for the data folder using multiple fallbacks.

    On a packaged/frozen APK the executable's parent may contain a `data` folder.
    When running from source the repository layout places `data` at parent.parent/data.
    Also try __file__/data and the current working directory as fallbacks.
    Return the first candidate that exists; otherwise return the most likely candidate and
    ensure it exists (create it) so save operations won't fail.
    """
    candidates = [
        Path(sys.executable).parent / "data",  # common for frozen executables
        Path(__file__).resolve().parent.parent / "data",  # repo layout: src/ -> parent/data
        Path(__file__).resolve().parent / "data",  # fallback: same folder as module
        Path.cwd() / "data",  # current working dir
    ]
    for c in candidates:
        try:
            if c.exists():
                return c
        except Exception:
            # ignore permissions/IO errors while probing
            pass
    # No existing candidate found; choose the repo-layout one as default and ensure it exists.
    default = candidates[1]
    try:
        default.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Best-effort: ignore if creation fails; caller should handle missing files.
        pass
    return default


DATA_FOLDER = resolve_data_folder()

DEFAULT_DATA_FILE = DATA_FOLDER / "sample_bible.json"
BOOKMARKS_FILE = DATA_FOLDER / "bible_bookmarks.json"
SETTINGS_FILE = DATA_FOLDER / "bible_settings.json"

# ===============================
# Helper functions
# ===============================
def load_data(path: Path = None):
    """Load Bible JSON, supporting both list and dict formats."""
    path = path or DEFAULT_DATA_FILE
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
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
    """List all available Bible translations in /data.
    Works both on desktop (from external files) and APK (from bundled assets).
    """
    translations = {}
    
    # Try to create data folder if it doesn't exist (shouldn't happen in APK but safety first)
    try:
        if not DATA_FOLDER.exists():
            DATA_FOLDER.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    
    # Look for translation files
    try:
        for p in DATA_FOLDER.glob("*.json"):
            # Skip settings/bookmarks files
            if p.stem not in ("bible_bookmarks", "bible_settings", "sample_bible"):
                translations[p.stem] = p
            elif p.stem == "sample_bible":
                translations[p.stem] = p
    except Exception:
        pass
    
    # Look in subdirectories (AMP, KJV, NIV, etc.)
    try:
        for sub in DATA_FOLDER.iterdir():
            if sub.is_dir():
                for p in sub.glob("*_bible.json"):
                    translations[p.stem] = p
    except Exception:
        pass
    
    return translations


def load_json(file_path):
    """Load any JSON file safely."""
    if not file_path.exists():
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_json(file_path, data):
    """Save data to JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ===============================
# Main App
# ===============================
class BibleApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.translations = list_translations()
        self.settings = load_json(SETTINGS_FILE)

        # ✅ Safe bookmarks loading (handles old and new formats)
        bm_data = load_json(BOOKMARKS_FILE)
        if isinstance(bm_data, list):
            self.bookmarks = bm_data
        else:
            self.bookmarks = bm_data.get("bookmarks", [])

        # Defaults
        self.dark_mode = self.settings.get("dark_mode", True)
        self.font_size = self.settings.get("font_size", 16)
        self.current_tab = "read"

        # Translation
        self.selected_translation = (
            self.settings.get("translation")
            if self.settings.get("translation") in self.translations
            else list(self.translations.keys())[0]
            if self.translations
            else None
        )

        # Bible data
        self.data = load_data(self.translations[self.selected_translation])
        self.current_book = list(self.data.keys())[0]
        self.current_chapter = "1"

        # Page setup
        page.title = "Bible"
        page.theme_mode = ft.ThemeMode.DARK if self.dark_mode else ft.ThemeMode.LIGHT
        page.padding = 0
        page.scroll = "adaptive"
        page.bgcolor = "#0b1020" if self.dark_mode else "#fdfdfd"

        # Register resize handler early so library can reflow when width changes
        try:
            # Flet provides page.on_resize in many versions
            page.on_resize = self.on_page_resize
        except Exception:
            # ignore if not supported
            pass

        self.build_ui()
        # start in library view (list of books)
        self.current_view = "library"  # one of: library, chapters, verses, read
        self.show_current_view()

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
                ft.Divider(height=1, color="#333" if self.dark_mode else "#ccc"),
                ft.Container(content=self.content_area, expand=True, padding=10),
                ft.Divider(height=1, color="#333" if self.dark_mode else "#ccc"),
                self.bottom_nav,
            ],
            expand=True,
            spacing=0,
        )

        # Wrap in SafeArea for mobile devices (avoids system bars, notches, navigation areas)
        self.page.add(
            ft.SafeArea(
                content=self.layout,
                top=True,
                bottom=True,
                left=True,
                right=True
            )
        )

    # ===============================
    # Top Bar
    # ===============================
    def build_topbar(self):
        self.translation_select = ft.Dropdown(
            width=140,
            options=[ft.dropdown.Option(k) for k in self.translations.keys()],
            value=self.selected_translation,
            on_change=self.change_translation,
        )

        self.book_select = ft.Dropdown(
            width=160,
            options=[ft.dropdown.Option(b) for b in (self.data.keys() if self.data else [])],
            value=self.current_book,
            on_change=self.change_book,
        )
        # prepare chapters safely
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
        title = ft.Text("📖 Bible", size=20, weight=ft.FontWeight.BOLD)

        controls = [title, ft.Container(expand=True), self.translation_select]
        # show back button when not on library view
        if getattr(self, "current_view", "library") != "library":
            controls.insert(0, back_btn)

        return ft.Container(
            ft.Row(controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor="#1a1a2e" if self.dark_mode else "#e8e8e8",
            padding=10,
        )

    # ===============================
    # Bottom Navigation
    # ===============================
    def build_bottom_nav(self):
        return ft.Container(
            ft.Row(
                [
                    ft.IconButton(
                        ft.Icons.MENU_BOOK,
                        icon_color="gold" if self.current_tab == "read" else "#888",
                        on_click=lambda e: self.switch_tab("read"),
                    ),
                    ft.IconButton(
                        ft.Icons.BOOKMARK,
                        icon_color="gold" if self.current_tab == "bookmarks" else "#888",
                        on_click=lambda e: self.switch_tab("bookmarks"),
                    ),
                    ft.IconButton(
                        ft.Icons.SETTINGS,
                        icon_color="gold" if self.current_tab == "settings" else "#888",
                        on_click=lambda e: self.switch_tab("settings"),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            ),
            padding=8,
            bgcolor="#1a1a2e" if self.dark_mode else "#e8e8e8",
        )

    # ===============================
    # Navigation screens: Library -> Chapters -> Verses
    # ===============================
    def show_current_view(self):
        v = getattr(self, "current_view", "library")
        if v == "library":
            self.show_library_page()
        elif v == "chapters":
            self.show_chapters_page()
        elif v in ("verses", "read"):
            # reuse existing read page renderer for verses
            self.show_read_page()

    def show_library_page(self):
        # list all books
        if not self.data:
            self.content_area.content = ft.Text("No Bible data available.", size=14, italic=True)
            self.page.update()
            return
        books = list(self.data.keys())
        try:
            # Order books according to canonical Bible order (English/KJV names)
            OT = [
                'Genesis','Exodus','Leviticus','Numbers','Deuteronomy','Joshua','Judges','Ruth',
                '1 Samuel','2 Samuel','1 Kings','2 Kings','1 Chronicles','2 Chronicles','Ezra','Nehemiah','Esther',
                'Job','Psalms','Proverbs','Ecclesiastes','Song of Solomon','Isaiah','Jeremiah','Lamentations',
                'Ezekiel','Daniel','Hosea','Joel','Amos','Obadiah','Jonah','Micah','Nahum','Habakkuk','Zephaniah','Haggai','Zechariah','Malachi'
            ]
            NT = [
                'Matthew','Mark','Luke','John','Acts','Romans','1 Corinthians','2 Corinthians','Galatians','Ephesians',
                'Philippians','Colossians','1 Thessalonians','2 Thessalonians','1 Timothy','2 Timothy','Titus','Philemon','Hebrews',
                'James','1 Peter','2 Peter','1 John','2 John','3 John','Jude','Revelation'
            ]

            canonical = OT + NT
            # Keep books in canonical order when possible; append any unknown/alternate names afterwards
            ordered = [b for b in canonical if b in books]
            remainder = sorted([b for b in books if b not in canonical])
            books = ordered + remainder
        except Exception:
            # fallback to alphabetical
            try:
                books = sorted(books, key=lambda x: x)
            except Exception:
                pass

        # helper to map common variants to canonical English names
        variants_map = {
            "psalm": "Psalms",
            "psalms": "Psalms",
            "song of songs": "Song of Solomon",
            "song of solomon": "Song of Solomon",
            "canticles": "Song of Solomon",
            "songs": "Song of Solomon",
            # numeric prefixes without space variants
            "1samuel": "1 Samuel",
            "2samuel": "2 Samuel",
            "1chronicles": "1 Chronicles",
            "2chronicles": "2 Chronicles",
            "1corinthians": "1 Corinthians",
            "2corinthians": "2 Corinthians",
            "1thessalonians": "1 Thessalonians",
            "2thessalonians": "2 Thessalonians",
            "1timothy": "1 Timothy",
            "2timothy": "2 Timothy",
            "1peter": "1 Peter",
            "2peter": "2 Peter",
            "1john": "1 John",
            "2john": "2 John",
            "3john": "3 John",
        }

        def canonical_name(bname: str) -> str:
            if not bname:
                return bname
            key = ''.join(ch for ch in bname.lower() if ch.isalnum() or ch.isspace()).strip()
            # collapse spaces
            key = ' '.join(key.split())
            # try direct variants map
            if key in variants_map:
                return variants_map[key]
            # try numeric prefix collapse (e.g., '1 samuel' -> '1samuel')
            nocomma = key.replace(' ', '')
            if nocomma in variants_map:
                return variants_map[nocomma]
            # fall back to title-cased original
            return bname

        # Group books into Old / New / Other based on canonical lists
        ot_books = [b for b in books if canonical_name(b) in OT]
        nt_books = [b for b in books if canonical_name(b) in NT]
        other_books = [b for b in books if b not in OT and b not in NT]
        grouped = []
        if ot_books:
            grouped.append(("Old Testament", ot_books))
        if nt_books:
            grouped.append(("New Testament", nt_books))
        if other_books:
            grouped.append(("Other", other_books))
        # -- New UI: searchable, grouped tile grid using Wrap for responsive layout --
        # Create (or reuse) a search box
        if not hasattr(self, "book_search"):
            self.book_search = ft.TextField(
                width=300,
                hint_text="Search books...",
                on_change=self.on_search_books,
            )

        query = (self.book_search.value or "").strip().lower()

        def book_matches(bname: str) -> bool:
            if not query:
                return True
            return query in bname.lower()

        # Build grouped sections with Wrap of tiles for each group
        sections = []
        for heading, blist in grouped:
            # filter by search query
            filtered = [b for b in blist if book_matches(b)]
            if not filtered:
                continue
            # create tiles
            tiles = []
            for b in filtered:
                chap_count = len(self.data.get(b, {})) if isinstance(self.data, dict) else 0
                # tile content: book short name + chapter count
                tile = ft.Container(
                    ft.Column([
                        ft.Text(b, size=16, weight=ft.FontWeight.NORMAL),
                        ft.Text(f"{chap_count} chapters", size=12, color="#bbb" if self.dark_mode else "#666"),
                    ], tight=True, alignment=ft.CrossAxisAlignment.CENTER),
                    width=140,
                    height=76,
                    padding=12,
                    margin=ft.margin.only(4, 4, 4, 4),
                    bgcolor="#2a303f" if self.dark_mode else "#ffffff",
                    border_radius=8,
                    border=ft.border.all(1, color="#3b4254" if self.dark_mode else "#e0e0e0"),
                    alignment=ft.alignment.center,
                    on_click=lambda e, book=b: self.open_chapters(book),
                )
                tiles.append(tile)

            sections.append((heading, tiles))

        content_cols = []
        # Determine number of columns based on page width for responsiveness
        def columns_for_width():
            try:
                w = int(self.page.width or 0)
            except Exception:
                w = 0
            # estimated tile total width including spacing/margin
            tile_total_width = 160
            if w <= 0:
                return 3
            cols = max(1, int(w / tile_total_width))
            return min(cols, 6)  # cap to avoid too many tiny columns

        cols = columns_for_width()

        # Flet version compatibility: not all versions provide Wrap. Use chunked Rows as fallback grid.
        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i : i + n]

        for heading, tiles in sections:
            content_cols.append(ft.Container(ft.Text(heading, size=14, weight=ft.FontWeight.BOLD), padding=6))
            # chunk tiles into rows based on computed cols
            row_groups = list(chunks(tiles, cols)) if tiles else []
            for group in row_groups:
                # ensure alignment and spacing between tiles; center rows
                content_cols.append(ft.Row(group, spacing=8, alignment=ft.MainAxisAlignment.CENTER))

        # If no results found from search, show helpful message
        if query and not content_cols:
            content_cols = [ft.Container(ft.Text("No books found."), padding=12)]

        # Compose final Column: search box + content
        body = ft.Column(
            [
                ft.Row([self.book_search, ft.Container(expand=True)]),
                ft.Divider(height=1, color="#333" if self.dark_mode else "#ddd"),
                ft.Column(content_cols, spacing=8, expand=True),
            ],
            spacing=8,
            expand=True,
        )

        self.current_view = "library"
        # rebuild header so back button hides
        self.header = self.build_topbar()
        self.layout.controls[0] = self.header
        self.content_area.content = body
        self.page.update()

    def on_search_books(self, e):
        # Triggered when the search box changes; re-render library
        try:
            self.book_search.value = (e.control.value or "")
        except Exception:
            pass
        self.show_library_page()

    def open_chapters(self, book):
        self.current_book = book
        # build chapter list
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
        # Show the current book title centered and render chapters as centered tiles
        title = ft.Container(ft.Text(self.current_book, size=18, weight=ft.FontWeight.BOLD), alignment=ft.alignment.center, padding=8)

        # create chapter tiles similar to book tiles
        tiles = []
        for c in self.chapters_current:
            tile = ft.Container(
                ft.Column([
                    ft.Text(f"Chapter {c}", size=16),
                ], alignment=ft.CrossAxisAlignment.CENTER),
                width=120,
                height=64,
                padding=10,
                margin=ft.margin.only(4, 4, 4, 4),
                bgcolor="#2a303f" if self.dark_mode else "#ffffff",
                border_radius=8,
                border=ft.border.all(1, color="#3b4254" if self.dark_mode else "#e0e0e0"),
                alignment=ft.alignment.center,
                on_click=lambda e, ch=c: self.open_verses(self.current_book, ch),
            )
            tiles.append(tile)

        # determine columns responsive to page width
        try:
            w = int(self.page.width or 0)
        except Exception:
            w = 0
        tile_total_width = 140
        cols = max(1, int(w / tile_total_width)) if w > 0 else 3
        cols = min(cols, 6)

        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i : i + n]

        rows = []
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
        # reuse show_read_page for verses rendering
        self.header = self.build_topbar()
        self.layout.controls[0] = self.header
        self.show_read_page()

    def back(self):
        # simple back navigation: verses -> chapters -> library
        if getattr(self, "current_view", "library") == "verses":
            self.current_view = "chapters"
            self.show_chapters_page()
        elif getattr(self, "current_view", "library") == "chapters":
            self.current_view = "library"
            self.show_library_page()
        else:
            # already on library, no-op
            pass


    # ===============================
    # Pages
    # ===============================
    def show_read_page(self):
        # defensive checks
        if not self.data or not self.current_book or not self.current_chapter:
            self.content_area.content = ft.Text("No Bible content available.", size=14, italic=True)
            self.page.update()
            return

        verses = self.data.get(self.current_book, {}).get(self.current_chapter, {})
        # sort verses numerically where possible
        items = list(verses.items())
        try:
            items = sorted(items, key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else kv[0])
        except Exception:
            pass

        # support goto verse: if verse_input has value, start from that verse
        start_v = None
        try:
            sv = str(self.verse_input.value).strip() if hasattr(self, 'verse_input') else ""
            if sv:
                start_v = sv
        except Exception:
            start_v = None

        # find start index
        start_idx = 0
        if start_v:
            for i, (vn, _) in enumerate(items):
                if str(vn) >= str(start_v):
                    start_idx = i
                    break

        # show book + chapter header centered
        header_title = ft.Container(
            ft.Text(f"{self.current_book} {self.current_chapter}", size=18, weight=ft.FontWeight.BOLD),
            alignment=ft.alignment.center,
            padding=8,
        )

        verse_list = ft.ListView(spacing=6, expand=True)
        for vnum, text in items[start_idx:]:
            # nicer verse UI: left small number, right selectable text field (styled to look plain), copy button
            verse_bg = "#21273e" if self.dark_mode else "#f2f2f2"
            textfield = ft.TextField(
                value=str(text),
                read_only=True,
                multiline=True,
                expand=True,
                text_style=ft.TextStyle(size=self.font_size),
                # style to blend with container
                bgcolor=verse_bg,
                border_color=verse_bg,
            )

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
                ft.Container(ft.Text(str(vnum), size=self.font_size), width=48, alignment=ft.alignment.center_left),
                textfield,
                ft.IconButton(ft.Icons.CONTENT_COPY, on_click=make_copy_handler(self.current_book, self.current_chapter, vnum, text)),
            ], alignment=ft.MainAxisAlignment.START)

            verse_list.controls.append(
                ft.Container(
                    verse_row,
                    bgcolor=verse_bg,
                    border_radius=8,
                    padding=10,
                    on_click=lambda e, b=self.current_book, c=self.current_chapter, v=vnum: self.add_bookmark(b, c, v),
                )
            )

        # compose final content with header + verses
        self.content_area.content = ft.Column([header_title, ft.Divider(), verse_list], spacing=8, expand=True)
        self.page.update()

    def show_bookmarks_page(self):
        if not self.bookmarks:
            self.content_area.content = ft.Text("No bookmarks yet.", size=14, italic=True)
            self.page.update()
            return
        items = ft.Column(
            [
                ft.Container(
                    ft.Text(f"{b['book']} {b['chapter']}:{b['verse']}", size=16),
                    bgcolor="#333" if self.dark_mode else "#f2f2f2",
                    padding=8,
                    border_radius=6,
                )
                for b in self.bookmarks
            ],
            spacing=8,
        )
        self.content_area.content = items
        self.page.update()

    def show_settings_page(self):
        self.content_area.content = ft.Column(
            [
                ft.Text("Settings", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row(
                    [
                        ft.Text("Font Size:"),
                        ft.IconButton(ft.Icons.REMOVE, on_click=lambda e: self.adjust_font(-1)),
                        ft.Text(str(self.font_size)),
                        ft.IconButton(ft.Icons.ADD, on_click=lambda e: self.adjust_font(1)),
                    ]
                ),
                ft.Row(
                    [
                        ft.Text("Dark Mode:"),
                        ft.Switch(value=self.dark_mode, on_change=self.toggle_theme),
                    ]
                ),
            ],
            spacing=16,
        )
        self.page.update()

    # ===============================
    # Event Handlers
    # ===============================
    def switch_tab(self, tab):
        self.current_tab = tab
        if tab == "read":
            self.show_read_page()
        elif tab == "bookmarks":
            self.show_bookmarks_page()
        elif tab == "settings":
            self.show_settings_page()
        self.bottom_nav = self.build_bottom_nav()
        self.layout.controls[-1] = self.bottom_nav
        self.page.update()

    def change_translation(self, e):
        val = e.control.value
        if val and val in self.translations:
            self.selected_translation = val
            self.data = load_data(self.translations[val]) or {}
            books = list(self.data.keys())
            self.book_select.options = [ft.dropdown.Option(b) for b in books]
            if books:
                self.book_select.value = books[0]
                self.current_book = books[0]
            else:
                self.book_select.value = None
                self.current_book = None
            # update chapters and current view depending on where the user is
            self._update_chapters_and_verses()
            # refresh the visible screen to reflect the new translation
            if getattr(self, "current_view", "library") == "library":
                self.show_library_page()
            elif getattr(self, "current_view", "library") == "chapters":
                # open chapters for selected book
                if self.current_book:
                    self.open_chapters(self.current_book)
                else:
                    self.show_library_page()
            else:
                # verses/read view
                if self.current_book and self.current_chapter:
                    self.open_verses(self.current_book, self.current_chapter)
                else:
                    self.show_library_page()

            self.save_settings()

    def change_book(self, e):
        self.current_book = self.book_select.value
        self._update_chapters_and_verses()

    def _update_chapters_and_verses(self):
        """Helper to update chapters dropdown and show verses for current book/chapter."""
        chapters = list(self.data[self.current_book].keys())
        self.chapter_select.options = [ft.dropdown.Option(c) for c in chapters]
        self.chapter_select.value = chapters[0]
        self.current_chapter = chapters[0]
        self.show_read_page()

    def change_chapter(self, e):
        self.current_chapter = e.control.value
        self.show_read_page()

    def adjust_font(self, delta):
        self.font_size = max(10, self.font_size + delta)
        self.show_read_page()
        self.save_settings()

    def toggle_theme(self, e):
        self.dark_mode = e.control.value
        self.page.theme_mode = ft.ThemeMode.DARK if self.dark_mode else ft.ThemeMode.LIGHT
        self.page.bgcolor = "#0b1020" if self.dark_mode else "#fdfdfd"
        self.save_settings()
        self.page.controls.clear()
        self.build_ui()
        self.switch_tab(self.current_tab)

    def add_bookmark(self, book, chapter, verse):
        bm = {"book": book, "chapter": chapter, "verse": verse}
        if bm not in self.bookmarks:
            self.bookmarks.append(bm)
            save_json(BOOKMARKS_FILE, {"bookmarks": self.bookmarks})
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Added {book} {chapter}:{verse} to bookmarks"))
            self.page.snack_bar.open = True
            self.page.update()

    def save_settings(self):
        save_json(
            SETTINGS_FILE,
            {
                "dark_mode": self.dark_mode,
                "font_size": self.font_size,
                "translation": self.selected_translation,
            },
        )


# ===============================
# Run app
# ===============================
def main(page: ft.Page):
    BibleApp(page)


if __name__ == "__main__":
    ft.app(target=main)
