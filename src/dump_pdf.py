from pypdf import PdfReader
import sys

def dump_pdf_text(pdf_path, output_path, pages=50):
    try:
        reader = PdfReader(pdf_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            for i in range(min(pages, len(reader.pages))):
                page = reader.pages[i]
                text = page.extract_text()
                f.write(f"--- PAGE {i+1} ---\n")
                f.write(text)
                f.write("\n\n")
        print(f"Dumped {pages} pages to {output_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    pdf_path = "Twi-New-Revised-Asante-All-Bible.pdf"
    output_path = "pdf_dump.txt"
    dump_pdf_text(pdf_path, output_path)
