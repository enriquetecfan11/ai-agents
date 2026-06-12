# ai-agents - Configuración y ejecución del proyecto
# Uso:
#   .\script.ps1              # Solo setup (venv, .env, dependencias)
#   .\script.ps1 -Action fetch
#   .\script.ps1 -Action index
#   .\script.ps1 -Action rag
#   .\script.ps1 -Action monitor
#   .\script.ps1 -Action all  # fetch + rag (flujo completo tras setup)

param(
    [ValidateSet("setup", "fetch", "index", "rag", "monitor", "all")]
    [string]$Action = "setup"
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$VenvPip = Join-Path $Root ".venv\Scripts\pip.exe"

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

    if (-not (Test-Path (Join-Path $Root "config\urls.txt"))) {
        Copy-Item (Join-Path $Root "config\urls.example.txt") (Join-Path $Root "config\urls.txt")
        Write-Host "Creado config\urls.txt desde plantilla."
    } else {
        Write-Host "config\urls.txt ya existe."
    }

    Write-Step "Creando entorno virtual"
    if (-not (Test-Path $VenvPython)) {
        python -m venv .venv
    } else {
        Write-Host ".venv ya existe."
    }

    Write-Step "Instalando dependencias"
    & $VenvPip install -r requirements.txt
}

function Invoke-PythonScript {
    param([string]$ScriptPath)
    & $VenvPython $ScriptPath
}

Ensure-Setup

switch ($Action) {
    "setup" {
        Write-Step "Setup completado"
        Write-Host @"

Próximos pasos:
  1. Edita .env (OLLAMA_BASE_URL y modelos)
  2. Edita config\urls.txt con tus URLs
  3. Ejecuta: .\script.ps1 -Action fetch
  4. Ejecuta: .\script.ps1 -Action rag

"@
    }
    "fetch" {
        Write-Step "Descargando URLs e indexando en Chroma"
        Invoke-PythonScript "scripts\fetch_and_index.py"
    }
    "index" {
        Write-Step "Indexando documentos existentes"
        Invoke-PythonScript "scripts\index_documents.py"
    }
    "rag" {
        Write-Step "Iniciando chatbot RAG"
        Invoke-PythonScript "scripts\chatbot_rag.py"
    }
    "monitor" {
        Write-Step "Inspeccionando ChromaDB"
        Invoke-PythonScript "scripts\monitor_chroma.py"
    }
    "all" {
        Write-Step "Flujo completo: fetch + chat RAG"
        Invoke-PythonScript "scripts\fetch_and_index.py"
        Invoke-PythonScript "scripts\chatbot_rag.py"
    }
}
