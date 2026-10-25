# Genera dist\KeyGlow.exe (un solo archivo, sin consola, con icono).
# Uso desde la carpeta del proyecto:  powershell -ExecutionPolicy Bypass -File tools\build_exe.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$py = Join-Path $root ".venv\Scripts\python.exe"

& $py -m pip install -q -e ".[app,hid,build]"
& $py tools\make_icon.py

& $py -m PyInstaller --noconfirm --clean --onefile --windowed `
    --name KeyGlow `
    --icon "$root\assets\keyglow.ico" `
    --add-data "$root\keyglow\app\static;keyglow\app\static" `
    --add-data "$root\keyglow\presets;keyglow\presets" `
    --add-data "$root\keyglow\community;keyglow\community" `
    --add-data "$root\keyglow\layouts;keyglow\layouts" `
    --add-data "$root\keyglow\shortcuts.json;keyglow" `
    --hidden-import pystray._win32 `
    --hidden-import openrgb `
    --hidden-import hid `
    --distpath "$root\dist" --workpath "$root\build" --specpath "$root\build" `
    "$root\tools\launcher.py"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falló" }

Write-Host "Listo: $root\dist\KeyGlow.exe"
