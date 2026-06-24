# build-app.ps1 — Cria o instalador Windows do ZeroInsight.
#
# Pré-requisitos:
#   - Python 3.10+ no PATH
#   - Node.js 18+ no PATH
#   - pip install pyinstaller  (feito automaticamente abaixo se não tiver)
#
# Uso: .\build-app.ps1
# Saída: dist-electron\ZeroInsight Setup *.exe

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

function Step($n, $total, $msg) {
    Write-Host ""
    Write-Host "[$n/$total] $msg" -ForegroundColor Cyan
}

Write-Host "=============================" -ForegroundColor Magenta
Write-Host "  ZeroInsight — Build Script " -ForegroundColor Magenta
Write-Host "=============================" -ForegroundColor Magenta

# ── 1. Build React frontend ────────────────────────────────────────────────────
Step 1 4 "Compilando frontend React…"
Set-Location "$Root\frontend"
npm ci --silent
npm run build
if ($LASTEXITCODE -ne 0) { Write-Error "npm run build falhou"; exit 1 }
Set-Location $Root
Write-Host "   OK — frontend/dist pronto" -ForegroundColor Green

# ── 2. Install PyInstaller ─────────────────────────────────────────────────────
Step 2 4 "Verificando PyInstaller…"
$pi = python -m PyInstaller --version 2>$null
if (-not $?) {
    Write-Host "   Instalando PyInstaller…"
    pip install pyinstaller --quiet
}
Write-Host "   OK — $(python -m PyInstaller --version)" -ForegroundColor Green

# ── 3. Build Python backend ────────────────────────────────────────────────────
Step 3 4 "Compilando backend Python com PyInstaller…"
Set-Location $Root
python -m PyInstaller backend.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller falhou"; exit 1 }
Write-Host "   OK — dist/backend/ pronto" -ForegroundColor Green

# ── 4. Build Electron installer ────────────────────────────────────────────────
Step 4 4 "Gerando instalador Windows (electron-builder)…"
Set-Location "$Root\electron"
npm ci --silent
npm run dist
if ($LASTEXITCODE -ne 0) { Write-Error "electron-builder falhou"; exit 1 }
Set-Location $Root

Write-Host ""
Write-Host "=============================" -ForegroundColor Magenta
Write-Host "  Build concluído com sucesso" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Magenta
Write-Host ""
Write-Host "  Instalador:" -NoNewline
Write-Host " dist-electron\ZeroInsight Setup*.exe" -ForegroundColor Yellow
Write-Host ""
