import json
import os

input_file = r"c:\Users\Afreh Kriss Ntim\bible\philippians_niv.json"
output_file = r"c:\Users\Afreh Kriss Ntim\bible\data\TWI\Books\Filipifo.json"

try:
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    content = data.get("Philippians")
    if content:
        new_data = {"Filipifo": content}
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
        print(f"Created {output_file}")
    else:
        print("Philippians key not found in input.")

except Exception as e:
    print(f"Error: {e}")
