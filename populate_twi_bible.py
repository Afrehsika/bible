import json
import os

# Paths
base_dir = r"c:\Users\Afreh Kriss Ntim\bible\data\TWI"
books_dir = os.path.join(base_dir, "Books")
target_file = os.path.join(base_dir, "TWI_bible.json")

# Mapping from Filename (without extension) to TWI_bible.json Key
# Note: Keys in TWI_bible.json are mostly English/Latinized or Twi.
# Files in Books are mostly Twi.
file_to_key_mapping = {
    "1 Mose": "Genesis",
    "2 Mose": "Exodus",
    "3 Mose": "Lewifo",
    "4 Mose": "Numeri",
    "5 Mose": "Deuteronomium",
    "Yosua": "Yosua",
    "Atemmufo": "Atemmufo",
    "Rut": "Rut",
    "1 Samuel": "1 Samuel",
    "2 Samuel": "2 Samuel",
    "1 Ahemfo": "1 Ahene",
    "2 Ahemfo": "2 Ahene",
    "1 Beresosɛm": "1 Beresosɛm",
    "2 Beresosɛm": "2 Beresosɛm",
    "Ɛsra": "Esra",
    "Nehemia": "Nehemia",
    "Ɛster": "Ester",
    "Hiob": "Hiob",
    "Nnwom": "Nnwom",
    "Mmebusɛm": "Mmbeusɛm",
    "Ɔsɛnkafo": "Ɔsɛnkafo",
    "Nnwom Mu Dwom": "Nnwom Mu Dwom",
    "Yesaia": "Yesaia",
    "Yeremia": "Yeremia",
    "Kwadwom": "Kwadwom",
    "Hesekiel": "Hesekiel",
    # Daniel is missing in files
    "Hosea": "Hosea",
    "Yoɛl": "Yoel",
    "Amos": "Amos",
    "Obadia": "Obadia",
    "Yona": "Yona",
    "Mika": "Mika",
    "Nahum": "Nahum",
    "Habakuk": "Habakuk",
    "Sefania": "Sefania",
    "Hagai": "Hagai",
    "Sakaria": "Sakaria",
    "Malaki": "Malaki",
    "Mateo": "Mateo",
    "Marko": "Marko",
    "Luka": "Luka",
    "Yohane": "Yohane",
    "Asomafo": "Asomafo",
    "Romafo": "Romafo",
    "1 Korintofo": "1 Korintofo",
    "2 Korintofo": "2 Korintofo",
    "Galatifo": "Galatifo",
    "Efesofo": "Efesofo",
    # Filipifo is missing in files
    "Kolosefo": "Kolosefo",
    "1 Tesalonikafo": "1 Tesalonikafo",
    "2 Tesalonikafo": "2 Tesalonikafo",
    "1 Timoteo": "1 Timoteo",
    "2 Timoteo": "2 Timoteo",
    "Tito": "Tito",
    "Filemon": "Filemon",
    "Hebrifo": "Hebrifo",
    "Yakobo": "Yakobo",
    "1 Petro": "1 Petro",
    "2 Petro": "2 Petro",
    "1 Yohane": "1 Yohane",
    "2 Yohane": "2 Yohane",
    "3 Yohane": "3 Yohane",
    "Yuda": "Yuda",
    "Adiyisɛm": "Adiyisɛm"
}

def populate_bible():
    # Load the target JSON
    if not os.path.exists(target_file):
        print(f"Target file not found: {target_file}")
        return

    with open(target_file, 'r', encoding='utf-8') as f:
        try:
            bible_data = json.load(f)
        except json.JSONDecodeError:
            print("Error decoding target JSON. Initializing as empty dict.")
            bible_data = {}

    # Iterate through the files in the Books directory
    for filename in os.listdir(books_dir):
        if not filename.endswith(".json"):
            continue

        file_base_name = os.path.splitext(filename)[0]
        
        if file_base_name in file_to_key_mapping:
            target_key = file_to_key_mapping[file_base_name]
            file_path = os.path.join(books_dir, filename)
            
            print(f"Processing {filename} -> {target_key}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    book_data = json.load(f)
                    # The book data structure is usually { "Book Name": { ... content ... } }
                    # We want the content.
                    # Let's find the root key.
                    if book_data:
                        root_key = list(book_data.keys())[0]
                        content = book_data[root_key]
                        
                        # Update the bible_data
                        bible_data[target_key] = content
                        print(f"  Updated {target_key}.")
                    else:
                        print(f"  Warning: {filename} is empty.")
                except json.JSONDecodeError:
                    print(f"  Error decoding {filename}. Skipping.")
        else:
            print(f"Skipping {filename} (no mapping found).")

    # Save the updated JSON
    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(bible_data, f, ensure_ascii=False, indent=2)
    
    print("Finished populating TWI_bible.json")

if __name__ == "__main__":
    populate_bible()
