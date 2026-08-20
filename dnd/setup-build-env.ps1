$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$BuildVenv = Join-Path $ProjectRoot ".build-venv"
$BuildPython = Join-Path $BuildVenv "Scripts\python.exe"
$NeedsCreate = -not (Test-Path -LiteralPath $BuildPython)

if (-not $NeedsCreate) {
    try {
        & $BuildPython --version | Out-Null
        $NeedsCreate = $LASTEXITCODE -ne 0
    } catch {
        $NeedsCreate = $true
    }
}

if ($NeedsCreate) {
    if (Test-Path -LiteralPath $BuildVenv) {
        Remove-Item -LiteralPath $BuildVenv -Recurse -Force
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv $BuildVenv
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv $BuildVenv
    } else {
        throw "Instala Python 3.8-3.15 para preparar el compilador."
    }
    if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el entorno de build." }
}

& $BuildPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Falló la actualización de pip." }
& $BuildPython -m pip install -r (Join-Path $ProjectRoot "requirements-build.txt")
if ($LASTEXITCODE -ne 0) { throw "Falló la instalación de dependencias." }

Write-Host "Entorno preparado. No necesitas ejecutar este script de nuevo."
