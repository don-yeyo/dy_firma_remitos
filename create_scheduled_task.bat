@echo off
:: Comprobar privilegios de Administrador
openfiles >nul 2>&1
if %errorlevel% neq 0 (
    echo ====================================================================
    echo [ERROR] Este script requiere permisos de Administrador.
    echo Por favor, haz clic derecho sobre el archivo y selecciona
    echo "Ejecutar como Administrador".
    echo ====================================================================
    pause
    exit /b 1
)

setlocal
:: Detectar la ruta raíz del proyecto dinámicamente
set "PROJECT_DIR=%~dp0"
:: Quitar la barra diagonal final si existe para consistencia
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

set "BATCH_PATH=%PROJECT_DIR%\server\sync_remitos.bat"
set "TASK_NAME=Sincronizador Remitos Don Yeyo"

echo ====================================================================
echo Configurando Tarea Programada de Windows para Sincronizacion
echo Nombre de la tarea: %TASK_NAME%
echo Ruta del script:    %BATCH_PATH%
echo Hora de ejecucion:  03:00 AM diariamente
echo ====================================================================

:: Crear la tarea programada usando schtasks bajo la cuenta SYSTEM
schtasks /create /tn "%TASK_NAME%" /tr "\"%BATCH_PATH%\"" /sc daily /st 03:00 /ru "SYSTEM" /f

if %ERRORLEVEL% equ 0 (
    echo ====================================================================
    echo [OK] Tarea programada creada exitosamente en el Programador de Tareas.
    echo Se ejecutara de fondo diariamente a las 3:00 AM.
    echo ====================================================================
) else (
    echo ====================================================================
    echo [ERROR] No se pudo crear la tarea programada. Codigo: %ERRORLEVEL%
    echo ====================================================================
)

pause
