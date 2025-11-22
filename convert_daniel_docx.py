import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET

source_file = r"c:\Users\Afreh Kriss Ntim\bible\Daniel Asante Twi.docx"
output_file = r"c:\Users\Afreh Kriss Ntim\bible\data\TWI\Books\Daniel.json"

def get_docx_text(path):
    try:
        import docx
        doc = docx.Document(path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except ImportError:
        print("python-docx not found, falling back to zipfile extraction")
        document_xml_path = 'word/document.xml'
        with zipfile.ZipFile(path) as docx:
            xml_content = docx.read(document_xml_path)
            tree = ET.fromstring(xml_content)
            paragraphs = []
            for p in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                texts = [node.text for node in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
                if texts:
                    paragraphs.append(''.join(texts))
            return '\n'.join(paragraphs)

def parse_text_to_json(text):
    book_data = {"Daniel": {}}
    current_chapter = None
    current_verse = None
    
    lines = text.split('\n')
    
    # Regex patterns
    # Chapter: "Daniel 3", "1", "2" on a line by itself (mostly)
    # But sometimes there are headers.
    # We'll assume if we see a line that is just a number, it's a chapter.
    # Or "Daniel \d+".
    chapter_pattern = re.compile(r"^(?:Daniel\s+)?(\d+)\s*$", re.IGNORECASE)
    
    # Verse: "1 Text", "2Text", "10Text"
    verse_pattern = re.compile(r"^(\d+)\s*(.*)")
    
    import traceback
    log_file = open("parsing_log.txt", "w", encoding="utf-8")
    try:
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Special case for missing Chapter 6 header
            if line.startswith("11Ɛnna mmarima yi bɛtoaa Daniel"):
                print("Forcing Chapter 6 start")
                new_chapter = "6"
                current_chapter = new_chapter
                current_verse = None
                if current_chapter not in book_data["Daniel"]:
                    book_data["Daniel"][current_chapter] = {}
                
            # Check for Chapter
            chap_match = chapter_pattern.match(line)
            if chap_match:
                new_chapter = chap_match.group(1)
                if int(new_chapter) > 14:
                     log_file.write(f"  Ignored potential chapter {new_chapter} (>14)\n")
                     pass
                else:
                    log_file.write(f"  MATCH CHAPTER: {new_chapter}\n")
                    print(f"Found potential chapter: {new_chapter}")
                    current_chapter = new_chapter
                    current_verse = None  # Reset verse
                    if current_chapter not in book_data["Daniel"]:
                        book_data["Daniel"][current_chapter] = {}
                    continue
                
            # Check for Verse
            verse_match = verse_pattern.match(line)
            if verse_match:
                verse_num = verse_match.group(1)
                verse_text = verse_match.group(2).strip()
                
                log_file.write(f"  MATCH VERSE: {verse_num}\n")
                
                if current_chapter:
                    book_data["Daniel"][current_chapter][verse_num] = verse_text
                    current_verse = verse_num
                else:
                    log_file.write(f"  SKIPPED VERSE (No Chapter): {verse_num}\n")
                continue
                
            # Continuation
            if current_chapter and current_verse:
                log_file.write(f"  CONTINUATION of {current_chapter}:{current_verse}\n")
                current_text = book_data["Daniel"][current_chapter][current_verse]
                if current_text and not current_text.endswith(' '):
                    current_text += ' '
                book_data["Daniel"][current_chapter][current_verse] = current_text + line
            else:
                log_file.write("  SKIPPED (No context or Header)\n")

    except Exception:
        traceback.print_exc()
    finally:
        log_file.close()
        
    return book_data

    return book_data

def main():
    raw_file = "daniel_raw.txt"
    if not os.path.exists(raw_file):
        print(f"File not found: {raw_file}")
        return

    with open(raw_file, 'r', encoding='utf-8') as f:
        text = f.read()

    json_data = parse_text_to_json(text)
    
    # Check extraction
    chapters = sorted([int(k) for k in json_data["Daniel"].keys()])
    print(f"Extracted chapters: {chapters}")
    
    for chap in chapters:
        verses = len(json_data["Daniel"][str(chap)])
        print(f"  Chapter {chap}: {verses} verses")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()
