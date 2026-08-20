$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$BuildPython = Join-Path $ProjectRoot ".build-venv\Scripts\python.exe"
$Executable = Join-Path $ProjectRoot "dist\Dungeon.exe"
$ReleaseDir = Join-Path $ProjectRoot "release"
$Archive = Join-Path $ReleaseDir "Dungeon-Windows-x64.zip"

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

& $BuildPython -m PyInstaller --clean --noconfirm (Join-Path $ProjectRoot "Dungeon.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller no pudo generar la build." }
if (-not (Test-Path -LiteralPath $Executable)) {
    throw "No se generó dist\Dungeon.exe."
}

New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null
if (Test-Path -LiteralPath $Archive) {
    Remove-Item -LiteralPath $Archive -Force
}
Compress-Archive -LiteralPath $Executable -DestinationPath $Archive
Write-Host "Build para tester: $Archive"
