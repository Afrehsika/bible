"""
Prepare app assets for packaging.

This script copies the top-level `data/` folder into `src/data` so the Flet packager
(which zips the `src` folder into `app.zip`) will include the JSON files inside the
final APK.

Usage (from project root):
    python scripts/prepare_assets.py

It will:
 - create or replace `src/data` with a copy of the top-level `data/` folder
 - print a short summary of files copied
"""
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
SRC_DATA = ROOT / "src" / "data"
TOP_DATA = ROOT / "data"

if not TOP_DATA.exists():
    print(f"Source data folder not found: {TOP_DATA}")
    sys.exit(2)

# Remove existing src/data if present, then copy
try:
    if SRC_DATA.exists():
        print(f"Removing existing \"{SRC_DATA}\"...")
        shutil.rmtree(SRC_DATA)
    print(f"Copying {TOP_DATA} -> {SRC_DATA} ...")
    shutil.copytree(TOP_DATA, SRC_DATA)

    # summary
    total = 0
    for p in SRC_DATA.rglob("*.json"):
        total += 1
    print(f"Copied data into src/data. JSON files copied: {total}")
    print("Ready for: flet build apk")
except Exception as e:
    print("Error while preparing assets:", e)
    raise
