@echo off
setlocal
cd /d "%~dp0"

echo ======================================================================
echo Iniciando Sincronizacion de Remitos de Finnegans
echo Fecha y hora: %date% %time%
echo ======================================================================

set "VENV_PATH=.venv"
if not exist "%VENV_PATH%\Scripts\python.exe" (
    set "VENV_PATH=..\.venv"
)

if not exist "%VENV_PATH%\Scripts\python.exe" (
    echo [ERROR] No se encontro el entorno virtual en '.venv\Scripts\python.exe' ni en '..\.venv\Scripts\python.exe'.
    echo Por favor, ejecuta 'uv venv' e instala las dependencias.
    exit /b 1
)

"%VENV_PATH%\Scripts\python.exe" sync_remitos.py

if %ERRORLEVEL% EQU 0 (
    echo [OK] Sincronizacion completada con exito.
) else (
    echo [ERROR] El proceso fallo con codigo de salida: %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
