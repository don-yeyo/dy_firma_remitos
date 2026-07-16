@echo off
echo ==================================================
echo   COMPILANDO SERVIDOR DE REMITOS A EJECUTABLE .EXE
echo ==================================================
echo.

:: Asegurar que estamos en el directorio del batch
cd /d "%~dp0"

:: Verificar si existe el entorno virtual de Python
if not exist "..\.venv\Scripts\activate.bat" (
    echo [ERROR] No se detecto el entorno virtual en ..\.venv
    echo Por favor, cree el entorno e instale requirements.txt antes de compilar.
    pause
    exit /b 1
)

echo [1/3] Activando entorno virtual de Python...
call "..\.venv\Scripts\activate.bat"

echo.
echo [2/3] Ejecutando PyInstaller para compilar server.py...
echo Esto puede demorar unos minutos debido a la indexacion de dependencias (FastAPI, OpenCV, PIL, WIA)...
echo.

pyinstaller --name="dy_remitos_server" ^
            --onefile ^
            --clean ^
            --hidden-import="uvicorn.protocols.http.h11_impl" ^
            --hidden-import="uvicorn.loops.auto" ^
            --hidden-import="uvicorn.loops.select" ^
            --hidden-import="uvicorn.logging" ^
            --hidden-import="win32com.client" ^
            --hidden-import="win32com" ^
            --hidden-import="pymysql" ^
            --hidden-import="cv2" ^
            --hidden-import="PIL" ^
            --hidden-import="google.genai" ^
            --collect-all="fastapi" ^
            --collect-all="uvicorn" ^
            server.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Ocurrio un fallo durante la compilacion con PyInstaller.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3/3] Reubicando ejecutable compilado...
if not exist "..\dist_server" mkdir "..\dist_server"
move /y "dist\dy_remitos_server.exe" "..\dist_server\"

:: Limpiar archivos temporales de compilacion
echo Limpiando archivos temporales de build...
rmdir /s /q build
rmdir /s /q dist
del /f /q dy_remitos_server.spec

echo.
echo ==================================================
echo   COMPILACION EXITOSA
echo ==================================================
echo El ejecutable autocontenido ha sido creado en:
echo   ..\dist_server\dy_remitos_server.exe
echo.
echo Recuerde colocar su archivo .env en el mismo 
echo directorio antes de ejecutar el servidor.
echo ==================================================
pause
