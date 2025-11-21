import json
from pathlib import Path

twi_file = Path("data/TWI/TWI_bible.json")

def verify():
    if not twi_file.exists():
        print("FAILURE: TWI_bible.json not found.")
        return

    with open(twi_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "Genesis" in data and "1" in data["Genesis"]:
        chapter = data["Genesis"]["1"]
        print(f"Genesis 1 has {len(chapter)} verses.")
        print(f"Verse 1: {chapter.get('1')}")
        print(f"Verse 31: {chapter.get('31')}")
        
        if len(chapter) >= 31:
             print("SUCCESS: Genesis 1 appears to be fully populated.")
        else:
             print("WARNING: Genesis 1 might be incomplete.")
    else:
        print("FAILURE: Genesis 1 not found in data.")

if __name__ == "__main__":
    verify()
