@echo off
setlocal EnableExtensions

REM Inicia o Brave com depuracao remota (CDP) na porta 9222.
REM Mantenha esta janela aberta enquanto usa o automacao-posts.

set "CDP_PORT=9222"
set "BRAVE_EXE="

if exist "%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe" (
    set "BRAVE_EXE=%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"
)
if not defined BRAVE_EXE if exist "%ProgramFiles(x86)%\BraveSoftware\Brave-Browser\Application\brave.exe" (
    set "BRAVE_EXE=%ProgramFiles(x86)%\BraveSoftware\Brave-Browser\Application\brave.exe"
)
if not defined BRAVE_EXE if exist "%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe" (
    set "BRAVE_EXE=%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"
)

if not defined BRAVE_EXE (
    echo [ERRO] Brave nao encontrado. Ajuste BRAVE_EXE neste script.
    pause
    exit /b 1
)

echo.
echo  Brave em modo debug
echo  Porta CDP: %CDP_PORT%
echo  Executavel: %BRAVE_EXE%
echo.
echo  1. Faca login no dashboard Dino neste Brave
echo  2. Em outro terminal: python main.py
echo.

start "" "%BRAVE_EXE%" ^
    --remote-debugging-port=%CDP_PORT% ^
    --user-data-dir="%LOCALAPPDATA%\BraveAutomationDebug" ^
    "https://app.dino.com.br/Gerenciador2/dashboard"

echo Brave iniciado. Feche o navegador para encerrar a sessao de debug.
pause
