$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$BuildPython = Join-Path $ProjectRoot ".build-venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $BuildPython)) {
    throw "Falta .build-venv. Ejecuta .\setup-build-env.ps1 una sola vez."
}
try {
    & $BuildPython --version | Out-Null
} catch {
    throw "El entorno de build está dañado. Ejecuta .\setup-build-env.ps1 para repararlo."
}
if ($LASTEXITCODE -ne 0) {
    throw "El entorno de build está dañado. Ejecuta .\setup-build-env.ps1 para repararlo."
}

& $BuildPython -m PyInstaller --clean --noconfirm --distpath dist-development --workpath build-development (Join-Path $ProjectRoot "Dungeon.development.spec")
if ($LASTEXITCODE -ne 0) { throw "No se pudo generar la build de desarrollo." }
Write-Host "Build de desarrollo: dist-development\Dungeon-Developer.exe"
