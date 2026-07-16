@echo off
setlocal
cd /d "%~dp0"

echo ======================================================================
echo Iniciando Sincronizacion de Remitos de Finnegans
echo Fecha y hora: %date% %time%
echo ======================================================================

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el entorno virtual en '.venv\Scripts\python.exe'.
    echo Por favor, ejecuta 'uv venv' y luego instala las dependencias.
    exit /b 1
)

".venv\Scripts\python.exe" sync_remitos.py

if %ERRORLEVEL% EQU 0 (
    echo [OK] Sincronizacion completada con exito.
) else (
    echo [ERROR] El proceso fallo con codigo de salida: %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
