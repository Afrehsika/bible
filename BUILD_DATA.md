Include JSON data in APK (offline use)

This project uses Flet which packages the contents of the `src/` folder into
`app.zip`, and the Flutter project bundles `app/app.zip` into the APK. To ensure
your `data/` JSON files are shipped inside the APK and available offline, copy the
project's top-level `data/` into `src/data` before building.

Quick steps (Windows PowerShell)

1. Prepare assets (copy data into src):

   ```powershell
   .\scripts\prepare_assets.ps1
   ```

   or directly with Python:

   ```powershell
   python .\scripts\prepare_assets.py
   ```

2. Build the APK:

   ```powershell
   flet build apk
   ```

3. (Optional) Verify that the built `app.zip` contains the `data/` folder:

   ```powershell
   python -c "import zipfile;print('\n'.join(zipfile.ZipFile(r'build\flutter\app\app.zip').namelist()))"
   ```

Troubleshooting

- If you see no `data/` files inside the APK, ensure `src/data` exists before running
  `flet build apk` and that your build process doesn't remove it.
- If your packaging tool places assets in a different location, tell me which
  packager you use and I can adapt the prepare script to place files where needed.
