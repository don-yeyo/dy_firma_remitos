import os
import subprocess
import sys

DRIVERS_DIR = "drivers_win"

def get_installer_files():
    """Escanea la carpeta drivers_win en busca de ejecutables e instaladores .inf."""
    installers = []
    
    if not os.path.exists(DRIVERS_DIR):
        return installers
        
    # Buscar archivos .exe e .inf recursivamente
    for root, dirs, files in os.walk(DRIVERS_DIR):
        for file in files:
            file_lower = file.lower()
            # Omitir archivos zip y firmwares
            if file_lower.endswith(".exe") or file_lower.endswith(".inf"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, DRIVERS_DIR)
                
                # Clasificar tipo
                if "tesseract" in file_lower:
                    desc = "Motor de Reconocimiento OCR Tesseract (Requerido para Texto)"
                elif "wia" in file_lower:
                    desc = "Driver de Escaneo WIA (Red)"
                elif "twain" in file_lower:
                    desc = "Driver de Escaneo TWAIN (Red)"
                elif "universal" in file_lower:
                    desc = "Driver de Impresión Universal PCL6"
                elif "printer" in file_lower or "pcl" in file_lower:
                    desc = "Driver de Impresión PCL6 Estándar"
                elif "utility" in file_lower or "web_installer" in file_lower:
                    desc = "Instalador Web de Utilidades Ricoh"
                elif file_lower == "setup.inf":
                    desc = f"Controlador INF de Dispositivo ({os.path.basename(root)})"
                else:
                    desc = "Instalador General/Utilidad"

                    
                installers.append({
                    "name": file,
                    "path": full_path,
                    "rel_path": rel_path,
                    "desc": desc,
                    "is_inf": file_lower.endswith(".inf")
                })
    return installers

def run_installer(installer):
    """Ejecuta el instalador seleccionado. Lanza procesos con privilegios nativos."""
    path = os.path.abspath(installer["path"])
    print(f"\nIniciando instalador: {installer['name']}")
    print(f"Tipo: {installer['desc']}")
    
    try:
        if installer["is_inf"]:
            print("\n[INFO] Instalando driver INF con pnputil (requiere permisos de Administrador)...")
            print(f"Archivo: {path}")
            
            # Paso 1: Instalar el driver en el almacén de Windows con elevación UAC
            pnputil_cmd = f'pnputil /add-driver "{path}" /install'
            print(f"\n-> Ejecutando: {pnputil_cmd}")
            print("   (Se solicitará permiso de Administrador si es necesario)\n")
            
            try:
                # Intentar con elevación UAC automática a través de PowerShell
                elevated_cmd = (
                    f'Start-Process powershell -Verb RunAs -Wait -ArgumentList '
                    f"'-NoProfile -Command \"{pnputil_cmd}; Write-Host \\\"\\n[Presione una tecla para cerrar...]\\\"; pause\"'"
                )
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", elevated_cmd],
                    capture_output=True, text=True
                )
                
                if result.returncode == 0:
                    print("✔ Driver INF agregado al almacén de controladores de Windows.")
                else:
                    # Fallback: intentar sin elevación (por si ya somos admin)
                    result_direct = subprocess.run(
                        ["powershell", "-NoProfile", "-Command", pnputil_cmd],
                        capture_output=True, text=True
                    )
                    if "correctamente" in result_direct.stdout.lower() or "already exists" in result_direct.stdout.lower():
                        print("✔ Driver INF agregado al almacén de controladores de Windows.")
                        print(f"   Detalle: {result_direct.stdout.strip()}")
                    else:
                        print(f"⚠ pnputil reportó: {result_direct.stdout.strip()}")
                        print(f"   Puede requerir ejecución manual como Administrador:")
                        print(f'   {pnputil_cmd}')
            except Exception as e:
                print(f"⚠ No se pudo ejecutar pnputil automáticamente: {e}")
                print(f"   Ejecute manualmente como Administrador:")
                print(f'   {pnputil_cmd}')
            
            # Paso 2: Abrir el applet de Escáneres y Cámaras para agregar el dispositivo
            print("\n-> Abriendo el panel de 'Escáneres y Cámaras' de Windows...")
            print("   Para completar la instalación del escáner de red:")
            print("   1. Haga clic en 'Agregar' (Add)")
            print("   2. Seleccione 'Type Generic Scanner(Network) WIA'")
            print("   3. Ingrese la IP del escáner cuando se le solicite")
            
            try:
                subprocess.Popen(
                    ["rundll32", "shell32.dll,Control_RunDLL", "sticpl.cpl"],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                print("✔ Panel de Escáneres y Cámaras abierto.")
            except Exception as e:
                print(f"⚠ No se pudo abrir automáticamente: {e}")
                print("   Ejecute manualmente: rundll32 shell32.dll,Control_RunDLL sticpl.cpl")

        else:
            # Ejecutar el instalador .exe usando el programa predeterminado del sistema (UAC se disparará si es necesario)
            os.startfile(path)
            print("✔ Ejecutable lanzado con éxito. Por favor, siga las instrucciones del asistente en pantalla.")
        return True
    except Exception as e:
        print(f"❌ Error al iniciar el instalador: {e}")
        return False


def show_install_menu():
    """Presenta el menú para instalar controladores al usuario."""
    print("\n" + "=" * 50)
    print("           INSTALADOR DE CONTROLADORES RICOH")
    print("=" * 50)
    
    installers = get_installer_files()
    if not installers:
        print(f"No se encontraron instaladores en la carpeta '{DRIVERS_DIR}/'.")
        print("Asegúrese de haber descargado o extraído los archivos allí.")
        return
        
    for i, inst in enumerate(installers, 1):
        print(f"  {i}. [{inst['desc']}]")
        print(f"     Archivo: {inst['rel_path']}")
        print("-" * 30)
        
    choice = input(f"Seleccione el controlador a instalar (1-{len(installers)}) o Enter para salir: ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(installers):
            run_installer(installers[idx])
        else:
            print("Selección fuera de rango.")
    else:
        print("Volviendo al menú principal.")
