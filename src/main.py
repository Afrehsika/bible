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

        self.build_ui()
        self.show_read_page()

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
            options=[ft.dropdown.Option(b) for b in self.data.keys()],
            value=self.current_book,
            on_change=self.change_book,
        )

        chapters = list(self.data[self.current_book].keys())
        self.chapter_select = ft.Dropdown(
            width=80,
            options=[ft.dropdown.Option(c) for c in chapters],
            value=self.current_chapter,
            on_change=self.change_chapter,
        )

        return ft.Container(
            ft.Row(
                [
                    ft.Text("📖 Bible", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    self.translation_select,
                    self.book_select,
                    self.chapter_select,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
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
    # Pages
    # ===============================
    def show_read_page(self):
        verses = self.data[self.current_book][self.current_chapter]
        verse_list = ft.ListView(spacing=6, expand=True)
        for vnum, text in verses.items():
            verse_list.controls.append(
                ft.Container(
                    ft.Text(
                        f"{vnum}. {text}",
                        size=self.font_size,
                        color="white" if self.dark_mode else "black",
                    ),
                    bgcolor="#21273e" if self.dark_mode else "#f2f2f2",
                    border_radius=8,
                    padding=10,
                    on_click=lambda e, b=self.current_book, c=self.current_chapter, v=vnum: self.add_bookmark(b, c, v),
                )
            )
        self.content_area.content = verse_list
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
            self.data = load_data(self.translations[val])
            self.book_select.options = [ft.dropdown.Option(b) for b in self.data.keys()]
            self.book_select.value = list(self.data.keys())[0]
            self.current_book = self.book_select.value
            self._update_chapters_and_verses()
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
