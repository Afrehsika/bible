import json

input_file = r"c:\Users\Afreh Kriss Ntim\bible\data\NIV\NIV_bible.json"
output_file = r"c:\Users\Afreh Kriss Ntim\bible\philippians_niv.json"

try:
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Check if data is list or dict
    philippians = None
    if isinstance(data, dict):
        philippians = data.get("Philippians")
    elif isinstance(data, list):
        # If list, search for book
        pass # The main.py load_data handles list, but let's assume dict for now based on populate script
    
    if philippians:
        print("Found Philippians")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({"Philippians": philippians}, f, indent=2)
    else:
        print("Philippians not found in dict keys:", list(data.keys())[:10])

except Exception as e:
    print(f"Error: {e}")
