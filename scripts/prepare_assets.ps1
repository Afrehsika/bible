# PowerShell wrapper to prepare assets before building the APK
# Run from project root (PowerShell):
#   .\scripts\prepare_assets.ps1

python .\scripts\prepare_assets.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "prepare_assets.py failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}
Write-Output "prepare_assets completed. Now run: flet build apk"