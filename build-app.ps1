# build-app.ps1 — Cria o instalador Windows do ZeroInsight.
#
# Pré-requisitos:
#   - Python 3.10+ no PATH  (winget install Python.Python.3.12)
#   - Node.js 18+ no PATH   (winget install OpenJS.NodeJS.LTS)
#   - PyInstaller instalado  (feito automaticamente abaixo)
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

# ── Pré-verificações ──────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[pre] Verificando pré-requisitos…" -ForegroundColor Cyan

$pythonOk = $null; try { $pythonOk = python --version 2>&1 } catch {}
if (-not $pythonOk -or $LASTEXITCODE -ne 0) {
    Write-Error "Python nao encontrado. Instale com: winget install Python.Python.3.12"
    exit 1
}

$nodeOk = $null; try { $nodeOk = node --version 2>&1 } catch {}
if (-not $nodeOk -or $LASTEXITCODE -ne 0) {
    Write-Error "Node.js nao encontrado. Instale com: winget install OpenJS.NodeJS.LTS"
    exit 1
}
Write-Host "   OK — $pythonOk | Node $nodeOk" -ForegroundColor Green

# ── 1. Build React frontend ────────────────────────────────────────────────────
Step 1 5 "Compilando frontend React…"
Set-Location "$Root\frontend"
npm ci --silent
npm run build
if ($LASTEXITCODE -ne 0) { Write-Error "npm run build falhou"; exit 1 }
Set-Location $Root
if (-not (Test-Path "$Root\frontend\dist\index.html")) {
    Write-Error "frontend/dist/index.html nao encontrado apos build — verifique o Vite"
    exit 1
}
Write-Host "   OK — frontend/dist pronto" -ForegroundColor Green

# ── 2. Instalar dependencias Python + PyInstaller ──────────────────────────────
Step 2 5 "Instalando dependencias Python e PyInstaller…"
pip install -r "$Root\requirements.txt" --quiet --disable-pip-version-check
if ($LASTEXITCODE -ne 0) { Write-Error "pip install requirements.txt falhou"; exit 1 }
$pi = python -m PyInstaller --version 2>$null
if (-not $?) {
    Write-Host "   Instalando PyInstaller…"
    pip install pyinstaller --quiet
}
Write-Host "   OK — PyInstaller $(python -m PyInstaller --version)" -ForegroundColor Green

# ── 3. Build Python backend ────────────────────────────────────────────────────
Step 3 5 "Compilando backend Python com PyInstaller…"
Set-Location $Root
python -m PyInstaller backend.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller falhou"; exit 1 }

$backendExe = "$Root\dist\backend\backend.exe"
if (-not (Test-Path $backendExe)) {
    Write-Error "backend.exe nao encontrado em dist\backend\ apos PyInstaller. Verifique os hidden imports no backend.spec."
    exit 1
}
Write-Host "   OK — dist/backend/backend.exe gerado ($([Math]::Round((Get-Item $backendExe).Length / 1MB, 1)) MB)" -ForegroundColor Green

# ── 4. Build Electron installer ────────────────────────────────────────────────
Step 4 5 "Instalando dependencias Electron…"
Set-Location "$Root\electron"
npm ci --silent
if ($LASTEXITCODE -ne 0) { Write-Error "npm ci (electron) falhou"; exit 1 }
Write-Host "   OK" -ForegroundColor Green

Step 5 5 "Gerando instalador Windows (electron-builder)…"
npm run dist
if ($LASTEXITCODE -ne 0) { Write-Error "electron-builder falhou"; exit 1 }
Set-Location $Root

$installer = Get-ChildItem "$Root\dist-electron\*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $installer) {
    Write-Error "Instalador .exe nao encontrado em dist-electron\ — electron-builder pode ter falhado silenciosamente."
    exit 1
}

Write-Host ""
Write-Host "=============================" -ForegroundColor Magenta
Write-Host "  Build concluído com sucesso" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Magenta
Write-Host ""
Write-Host "  Instalador:" -NoNewline
Write-Host " $($installer.Name)" -ForegroundColor Yellow
Write-Host ""
