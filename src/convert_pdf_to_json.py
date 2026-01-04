import re
import json
import os
from pathlib import Path
from pypdf import PdfReader

# Configuration
PDF_PATH = "Twi-New-Revised-Asante-All-Bible.pdf"
OUTPUT_DIR = Path("data/TWI")
OUTPUT_FILE = OUTPUT_DIR / "TWI_bible.json"
BOOKS_DIR = OUTPUT_DIR / "Books"

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BOOKS_DIR.mkdir(parents=True, exist_ok=True)

# List of books ordered as they appear in the PDF (from TOC analysis)
# Note: I've normalized some spellings and capitalized headers to match expectation.
BOOK_NAMES = [
    "Gyenesis", "Eksodɔs", "Lewitikɔs", "Numeri", "Deuteronomium", "Yosua", "Atemmufoɔ", "Rut",
    "1 Samuel", "2 Samuel", "1 Ahemfo", "2 Ahemfo", "1 Berɛsosɛm", "2 Berɛsosɛm", "Esra", "Nehemia", "Ester",
    "Hiob", "Nnwom", "Mmebusɛm", "Ɔsɛnkafoɔ", "Nnwom Mu Dwom", "Yesaia", "Yeremia", "Kwadwom",
    "Hesekiel", "Daniel", "Hosea", "Yoel", "Amos", "Obadia", "Yona", "Mika", "Nahum", "Habakuk", "Sefania", "Hagai", "Sakaria", "Malaki",
    "Mateo", "Marko", "Luka", "Yohane", "Asomafoɔ", "Romafoɔ", "1 Korintofoɔ", "2 Korintofoɔ", "Galatifoɔ", "Efesofoɔ",
    "Filipifoɔ", "Kolosefoɔ", "1 Tesalonikafoɔ", "2 Tesalonikafoɔ", "1 Timoteo", "2 Timoteo", "Tito", "Filemon", "Hebrifoɔ",
    "Yakobo", "1 Petro", "2 Petro", "1 Yohane", "2 Yohane", "3 Yohane", "Yuda", "Adiyisɛm"
]

# Patterns
# Header to ignore
IGNORE_LINES = [
    "New Revised Asante Twi Bible",
    "© 2012 The Bible Society of Ghana.",
    "Twi - All Bible",
    "(New Revised Asante Twi)",
    "Twi Language",
    "Old Testament",
    "New Testament"
]

def clean_text(text):
    return text.strip()

def parse_pdf():
    reader = PdfReader(PDF_PATH)
    print(f"Total Pages: {len(reader.pages)}")
    
    bible_data = {}
    current_book = None
    current_chapter = None
    current_verse = None
    
    # We'll use a pointer to the book list to know what to expect next
    book_index = 0
    
    # State debug
    processed_pages = 0
    
    for i, page in enumerate(reader.pages):
        # Skip TOC pages (0 and 1 usually)
        if i < 2:
            continue
            
        text = page.extract_text()
        if not text:
            continue
            
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip page numbers (lines that are just digits)
            if line.isdigit():
                continue
                
            # Skip headers
            if any(ign in line for ign in IGNORE_LINES):
                continue
            
            # Detection logic
            
            # 1. Check for Book + Chapter Header (e.g. "Gyenesis 1", "2 Samuel 12")
            # We look for the NEXT book in list or CURRENT book
            # Check current book chapter
            
            matched_header = False
            
            # Try to match a book header
            # We check the current book and the next book in the sequence
            candidates = []
            if current_book:
                candidates.append(current_book)
            if book_index < len(BOOK_NAMES):
                candidates.append(BOOK_NAMES[book_index])
                
            for book in candidates:
                # Regex for "BookName ChapterNum"
                # Need to be careful with books starting with number like "1 Samuel"
                # Pattern: ^{book} (\d+)$
                # Escape book name for regex
                escaped_book = re.escape(book)
                match = re.match(f"^{escaped_book}\s+(\d+)$", line, re.IGNORECASE)
                if match:
                    chap_num = match.group(1)
                    
                    # If this is a new book (from candidates)
                    if book != current_book:
                        current_book = book
                        bible_data[current_book] = {}
                        if book == BOOK_NAMES[book_index]:
                            book_index += 1
                        print(f"Starting Book: {current_book}")
                    
                    current_chapter = chap_num
                    if current_chapter not in bible_data[current_book]:
                        bible_data[current_book][current_chapter] = {}
                    
                    current_verse = None # Reset verse at start of chapter
                    print(f"  Chapter {current_chapter}")
                    matched_header = True
                    break
            
            if matched_header:
                continue
                
            # 2. Check for just Book Name (sometimes appears before Chapter 1)
            if book_index < len(BOOK_NAMES) and line == BOOK_NAMES[book_index]:
                # Just the book title header, ignore or use to verify
                # We'll typically catch "Book 1" next.
                continue
                
            # 3. Check for Verse Number
            # Logic: If we are in a chapter, and line starts with number
            if current_book and current_chapter:
                # Verse pattern: number at start
                # Beware of footnotes or other numbers. 
                # Usually verses are sequential.
                
                # regex: start with number
                v_match = re.match(r"^(\d+)\s*(.*)", line)
                if v_match:
                    v_num = v_match.group(1)
                    v_text = v_match.group(2).strip()
                    
                    # Validate: is it likely a verse?
                    # If current_verse is None, we expect 1.
                    # If current_verse is set, we expect current_verse + 1 (mostly)
                    # But don't be too strict
                    
                    is_new_verse = False
                    if current_verse is None:
                        if v_num == "1":
                            is_new_verse = True
                    else:
                        # Simple check: if it's a number, assume it's a verse
                        # Unless it's vastly different? 
                        # In PDF text, sometimes formatted strangely.
                        # Let's assume any line starting with digit in a chapter is a verse.
                        is_new_verse = True
                        
                    if is_new_verse:
                        current_verse = v_num
                        # If parsed text is empty, it might be on next line? 
                        # But v_match group 2 captures rest of line.
                        bible_data[current_book][current_chapter][current_verse] = v_text
                        continue

            # 4. Continuation Text
            if current_book and current_chapter and current_verse:
                # Provide spacing if needed. 
                # Twi words don't usually end with hyphen for break in these PDFs? 
                # Usually add space.
                prev_text = bible_data[current_book][current_chapter][current_verse]
                if prev_text and not prev_text.endswith(" "):
                     # Heuristic: Add space if previous char is letter
                     bible_data[current_book][current_chapter][current_verse] += " " + line
                else:
                     bible_data[current_book][current_chapter][current_verse] += line
                     
    return bible_data

def save_data(data):
    # Save main file
    print(f"Saving {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    # Save individual books
    print(f"Saving books to {BOOKS_DIR}...")
    for book, chapters in data.items():
        book_file = BOOKS_DIR / f"{book}.json"
        with open(book_file, "w", encoding="utf-8") as f:
            json.dump(chapters, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    data = parse_pdf()
    save_data(data)
    print("Conversion Complete!")
