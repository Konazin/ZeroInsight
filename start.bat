@echo off
chcp 65001 >nul
title ZeroInsight
echo.
echo  ZeroInsight - Iniciando backend e frontend...
echo.
python start.py %*
echo.
if errorlevel 1 (
    echo  Erro ao iniciar. Verifique o terminal acima.
    pause >nul
)
