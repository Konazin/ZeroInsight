param(
    [string]$VenvPath = ".venv-build"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

Write-Host "ZeroInsight Windows build" -ForegroundColor Cyan

if (-not (Test-Path $VenvPath)) {
    Write-Host "Criando venv em $VenvPath"
    python -m venv $VenvPath
}

$Python = Join-Path $VenvPath "Scripts\python.exe"
$Pip = Join-Path $VenvPath "Scripts\pip.exe"

& $Pip install --upgrade pip
& $Pip install -r requirements.txt
& $Pip install pyinstaller

Write-Host "Rodando checagem de sintaxe"
& $Python -m compileall -q main.py zero_insight

Write-Host "Gerando executavel com PyInstaller"
& $Python -m PyInstaller packaging\pyinstaller\zeroinsight.spec --noconfirm

$Exe = Join-Path $Root "dist\ZeroInsight\ZeroInsight.exe"
if (-not (Test-Path $Exe)) {
    throw "Build falhou: $Exe nao encontrado."
}
Write-Host "Executavel gerado: $Exe" -ForegroundColor Green

$Inno = Get-Command "iscc.exe" -ErrorAction SilentlyContinue
if (-not $Inno) {
    $Common = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if (Test-Path $Common) {
        $Inno = Get-Item $Common
    }
}

if ($Inno) {
    Write-Host "Compilando instalador Inno Setup"
    & $Inno.Source packaging\inno\zeroinsight.iss
    Write-Host "Instalador gerado em dist\ZeroInsightSetup.exe" -ForegroundColor Green
} else {
    Write-Host "Inno Setup nao encontrado. Instale Inno Setup 6 para gerar o instalador." -ForegroundColor Yellow
}
