# python-agents — setup y atajos vía main.py
# Uso:
#   .\script.ps1              # setup (venv, .env, dependencias)
#   .\script.ps1 -Action fetch
#   .\script.ps1 -Action tui  # launcher visual (Textual)

param(
    [ValidateSet("setup", "fetch", "index", "monitor", "all", "simple", "rag", "memory", "skills", "tui")]
    [string]$Action = "setup"
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

$VenvPython = @(
    (Join-Path $Root "env\Scripts\python.exe"),
    (Join-Path $Root ".venv\Scripts\python.exe")
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $VenvPython) {
    $VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
}

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Ensure-Setup {
    Write-Step "Comprobando archivos de configuración"

    if (-not (Test-Path (Join-Path $Root ".env"))) {
        Copy-Item (Join-Path $Root ".env.example") (Join-Path $Root ".env")
        Write-Host "Creado .env desde .env.example (edítalo con tu OLLAMA_BASE_URL)."
    } else {
        Write-Host ".env ya existe."
    }

    if (-not (Test-Path (Join-Path $Root "urls.txt"))) {
        Copy-Item (Join-Path $Root "urls.example.txt") (Join-Path $Root "urls.txt")
        Write-Host "Creado urls.txt desde plantilla."
    } else {
        Write-Host "urls.txt ya existe."
    }

    Write-Step "Creando entorno virtual"
    if (-not (Test-Path $VenvPython)) {
        python -m venv .venv
        $VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
    } else {
        Write-Host "Entorno virtual ya existe."
    }

    Write-Step "Instalando dependencias"
    & $VenvPython -m pip install -r requirements.txt
    6 $VenvPython -m pip install textual
}

function Invoke-Main {
    param([string[]]$MainArgs)
    & $VenvPython (Join-Path $Root "main.py") @MainArgs
}

Ensure-Setup

switch ($Action) {
    "setup" {
        Write-Step "Setup completado"
        Write-Host @"

Próximos pasos:
  1. Edita .env (OLLAMA_BASE_URL y modelos)
  2. Edita urls.txt con tus URLs
  3. Ejecuta: python main.py fetch   (o .\script.ps1 -Action fetch)
  4. Ejecuta: python main.py tui     (launcher visual)

"@
    }
    default {
        Write-Step "python main.py $Action"
        Invoke-Main @($Action)
    }
}
