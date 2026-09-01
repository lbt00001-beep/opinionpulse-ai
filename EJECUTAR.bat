@echo off
chcp 65001 >nul
title OpinionPulse AI - Radar de Opinión y Sentimiento
cd /d "%~dp0"

echo ================================================================
echo    OPINIONPULSE AI - Radar de Opinión y Sentimiento
echo ================================================================
echo.
echo [1/2] Cerrando procesos y terminales anteriores en puerto 8000...

:: Buscar y cerrar procesos ocupando el puerto 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r ":8000\>"') do (
    if not "%%a"=="" if not "%%a"=="0" (
        echo Cerrando PID %%a...
        taskkill /F /PID %%a >nul 2>&1
    )
)

echo [2/2] Abriendo navegador predeterminado en http://localhost:8000...
start http://localhost:8000

echo.
echo Servidor en ejecucion. Presiona Ctrl+C para detener.
echo ================================================================
echo.

py run.py

if %ERRORLEVEL% NEQ 0 (
    echo [AVISO] Probando con 'python'...
    python run.py
)

pause
