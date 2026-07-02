@echo off
chcp 65001 >nul
title ZeroInsight
echo.
echo  ZeroInsight - Iniciando...
echo.

:: ── Verificar Python ────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python nao encontrado.
    echo.
    echo  Instale o Python 3.10+ com:
    echo    winget install Python.Python.3.12
    echo.
    pause
    exit /b 1
)

:: ── Verificar Node.js / npm ──────────────────────────────────────────────────
npm --version >nul 2>&1
if errorlevel 1 (
    echo  [aviso] Node.js nao encontrado — frontend nao sera iniciado.
    echo.
    echo  Para rodar o frontend tambem, instale o Node.js:
    echo    winget install OpenJS.NodeJS.LTS
    echo.
)

:: ── Criar venv se nao existir ────────────────────────────────────────────────
if not exist ".venv\Scripts\python.exe" (
    echo  [setup] Criando ambiente virtual Python...
    python -m venv .venv
    if errorlevel 1 (
        echo  [ERRO] Falha ao criar o ambiente virtual.
        pause
        exit /b 1
    )
)

:: ── Instalar / atualizar dependencias ────────────────────────────────────────
echo  [setup] Verificando dependencias Python...
.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo  [ERRO] Falha ao instalar dependencias. Verifique requirements.txt.
    pause
    exit /b 1
)

:: ── Iniciar aplicacao ────────────────────────────────────────────────────────
echo.
echo  [start] Iniciando backend e frontend...
echo.
.venv\Scripts\python.exe start.py %*
echo.
if errorlevel 1 (
    echo  Erro ao iniciar. Verifique o terminal acima.
    pause >nul
)
