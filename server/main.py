import os
import sys
import subprocess
import urllib.request
import config
import scanner
import recognition
import driver_manager


def print_menu():
    print("\n" + "=" * 50)
    print("      AUTOMATIZACIÓN DE RECEPCIÓN DE DOCUMENTOS")
    print("=" * 50)
    print(" 1. Instalar controladores (impresora/escáner WIA)")
    print(" 2. Seleccionar escáneres/multifunciones del sistema (WIA)")
    print(" 3. Enviar página de prueba de impresión")
    print(" 4. Iniciar Escaneo Masivo (Paso 1 - Bandeja/ADF)")
    
    # Mostrar el proveedor de IA configurado de forma dinámica
    if config.AI_PROVIDER == "gemini":
        provider_str = "Gemini"
    elif config.AI_PROVIDER == "powerautomate":
        provider_str = "Power Automate"
    else:
        provider_str = f"VLM Local ({config.VLM_MODEL})"
    print(f" 5. Procesar Imágenes Escaneadas (Paso 2 - {provider_str})")
    
    print(" 6. Escanear + Procesar Todo (Flujo Completo)")
    print(" 7. Sincronizar Remitos desde Finnegans (ERP)")
    print(" 8. Mostrar Configuración Actual (.env)")
    print(" 9. Gestionar Servicio Ollama (VLM Local)")
    print(" 10. Salir")
    print("=" * 50)

def manage_ollama():
    """Submenú de gestión local de Ollama."""
    while True:

        print("\n" + "=" * 50)
        print("          GESTIÓN DEL SERVICIO OLLAMA (VLM LOCAL)")
        print("=" * 50)
        print(" 1. Verificar estado de la API local")
        print(" 2. Iniciar servidor de Ollama en segundo plano (PowerShell)")
        print(" 3. Detener servidor de Ollama (liberar RAM/VRAM)")
        print(" 4. Listar modelos de Ollama instalados")
        print(" 5. Eliminar modelo original (qwen2.5vl:7b) para ahorrar espacio")
        print(" 6. Liberar memoria RAM del sistema general (Procesos)")
        print(" 7. Volver al menú principal")
        print("=" * 50)
        
        choice = input("Seleccione una opción (1-7): ").strip()
        
        if choice == "1":
            print("\nVerificando conexión con el servidor Ollama...")
            try:
                response = urllib.request.urlopen("http://localhost:11434", timeout=3)
                if response.status == 200:
                    print("✔ [OLLAMA ACTIVO]: El servidor responde correctamente en http://localhost:11434")
            except Exception:
                print("✘ [OLLAMA INACTIVO]: El servidor no responde. ¿Está apagado?")
                
        elif choice == "2":
            print("\nIniciando servidor de Ollama en segundo plano...")
            try:
                cmd = 'Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden'
                subprocess.run(["powershell", "-Command", cmd], check=True)
                print("✔ Petición de arranque enviada a Windows.")
                print("Nota: Espera unos segundos y vuelve a verificar el estado (Opción 1).")
            except Exception as e:
                print(f"Error al iniciar Ollama: {e}")
                
        elif choice == "3":
            print("\nDeteniendo servidor de Ollama y liberando RAM/VRAM...")
            success = False
            
            # 1. Intentar detener el servicio de Windows (por si estuviera corriendo como servicio del sistema)
            try:
                subprocess.run(
                    ["powershell", "-Command", "Stop-Service -Name ollama -ErrorAction SilentlyContinue"],
                    capture_output=True,
                    text=True
                )
                # Verificar si el servicio realmente se detuvo
                r_check = subprocess.run(
                    ["powershell", "-Command", "(Get-Service -Name ollama -ErrorAction SilentlyContinue).Status"],
                    capture_output=True,
                    text=True
                )
                if "Stopped" in r_check.stdout:
                    success = True
            except Exception:
                pass
            
            # 2. Matar todos los procesos que coincidan con 'ollama*' (ollama.exe, ollama_app.exe, etc.)
            if not success:
                try:
                    r_kill = subprocess.run(["taskkill", "/f", "/im", "ollama*"], capture_output=True, text=True)
                    if r_kill.returncode == 0:
                        success = True
                except Exception:
                    pass
            
            if success:
                print("✔ Petición de detención del servidor procesada.")
                print("Nota: Verifica el estado (Opción 1) para confirmar si se detuvo de forma efectiva.")
            else:
                print("Nota: El servidor no se encontraba en ejecución o no se pudo detener (¿requiere permisos de Administrador?).")
                
        elif choice == "4":
            print("\nModelos actualmente instalados en Ollama:")
            try:
                subprocess.run(["ollama", "list"])
            except Exception as e:
                print(f"Error al listar modelos (¿está Ollama en el PATH?): {e}")
                
        elif choice == "5":
            confirm = input("\n¿Desea eliminar 'qwen2.5vl:7b' para liberar 4.7 GB de disco? (s/n): ").strip().lower()
            if confirm == "s":
                print("\nEliminando modelo original...")
                try:
                    subprocess.run(["ollama", "rm", "qwen2.5vl:7b"])
                    print("✔ Modelo 'qwen2.5vl:7b' eliminado correctamente.")
                except Exception as e:
                    print(f"Error al eliminar el modelo: {e}")
            else:
                print("Operación cancelada.")
                
        elif choice == "6":
            print("\nLiberando memoria RAM del sistema (Compactando Working Sets)...")
            try:
                # Script de PowerShell para compactar la memoria de todos los procesos activos
                cmd = 'Get-Process | ForEach-Object { try { $_.MinWorkingSet = $_.MinWorkingSet } catch {} }'
                # Forzar recolección en .NET
                cmd += '; [System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()'
                
                subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
                print("✔ Procesos compactados. Windows ha liberado la memoria física no utilizada.")
            except Exception as e:
                print(f"Error al intentar liberar memoria RAM: {e}")
                
        elif choice == "7":
            break
        else:
            print("Opción no válida.")
        
        input("\nPresione Enter para continuar...")

def main():
    # Asegurar que se cargue la configuración e imprima al inicio
    config.print_config()
    
    import importlib
    while True:
        # Recargar en caliente config y scanner por si se editó el .env de fondo
        importlib.reload(config)
        importlib.reload(scanner)
        
        print_menu()
        choice = input("Seleccione una opción (1-8): ").strip()
        
        if choice == "1":
            driver_manager.show_install_menu()
            
        elif choice == "2":
            print("\nBuscando dispositivos WIA instalados...")
            devices = scanner.list_devices()
            if not devices:
                print("No se encontraron dispositivos escáner compatibles con WIA.")
                print("Nota: Asegúrese de tener el driver WIA del fabricante (RICOH u otro) instalado.")
            else:
                print(f"Se encontraron {len(devices)} dispositivos:")
                for i, dev in enumerate(devices, 1):
                    print(f"  {i}. Nombre: {dev['name']}")
                    print(f"     ID de Dispositivo: {dev['id']}")
                    print(f"     Descripción: {dev['description']}")
                    print("-" * 30)
                
                sel_choice = input(f"Seleccione un dispositivo (1-{len(devices)}) o presione Enter para cancelar: ").strip()
                if sel_choice.isdigit():
                    idx = int(sel_choice) - 1
                    if 0 <= idx < len(devices):
                        selected = devices[idx]
                        selected_name = selected["name"]
                        selected_id = selected["id"]
                        
                        # Actualizar en el archivo .env
                        config.update_env_scanner_name(selected_name)
                        
                        # Ejecutar prueba de conexión
                        scanner.test_device_connection(selected_id, selected_name)
                    else:
                        print("Selección fuera de rango.")
                else:
                    print("Operación cancelada.")
 
        elif choice == "3":
            if not config.SCANNER_NAME:
                print("\nDebe seleccionar una impresora/escáner primero (Opción 2).")
            else:
                scanner.send_test_print_page(config.SCANNER_NAME)
            
        elif choice == "4":
            print("\n" + "-" * 50)
            print(" EJECUTANDO PASO 1: ESCANEO MASIVO")
            print("-" * 50)
            scanned_files = scanner.trigger_scan()
            if scanned_files:
                print(f"\n¡Éxito! Se han guardado {len(scanned_files)} imágenes en:")
                print(f"  {os.path.abspath(config.SCAN_OUTPUT_DIR)}")
            else:
                print("\nNo se pudo escanear ninguna página.")
                print("Verifique que el dispositivo esté encendido, conectado a la red y el driver WIA esté configurado.")
                
        elif choice == "5":
            if config.AI_PROVIDER == "gemini":
                provider_str = "GEMINI AI"
            elif config.AI_PROVIDER == "powerautomate":
                provider_str = "POWER AUTOMATE"
            else:
                provider_str = f"VLM LOCAL ({config.VLM_MODEL})"
            print("\n" + "-" * 50)
            print(f" EJECUTANDO PASO 2: PROCESAMIENTO DE IMÁGENES ({provider_str})")
            print("-" * 50)
            try:
                processor = recognition.DocumentProcessor()
                processor.process_all_scans()
            except Exception as e:
                print(f"Error durante el reconocimiento de imágenes: {e}")
                
        elif choice == "6":
            print("\n" + "-" * 50)
            print(" EJECUTANDO FLUJO COMPLETO: ESCANEO + PROCESAMIENTO MASIVO")
            print("-" * 50)
            
            # Paso 1: Escaneo
            scanned_files = scanner.trigger_scan()
            
            if scanned_files:
                print(f"\n[OK] Paso 1 finalizado: Se escanearon {len(scanned_files)} páginas con éxito.")
                print(f"Iniciando Paso 2: Procesamiento automático de las imágenes...")
                
                # Paso 2: Procesamiento de imágenes
                if config.AI_PROVIDER == "gemini":
                    provider_str = "GEMINI AI"
                elif config.AI_PROVIDER == "powerautomate":
                    provider_str = "POWER AUTOMATE"
                else:
                    provider_str = f"VLM LOCAL ({config.VLM_MODEL})"
                
                print("\n" + "-" * 50)
                print(f" EJECUTANDO PASO 2: PROCESAMIENTO DE IMÁGENES ({provider_str})")
                print("-" * 50)
                try:
                    processor = recognition.DocumentProcessor()
                    processor.process_all_scans()
                except Exception as e:
                    print(f"Error durante el reconocimiento de imágenes: {e}")
            else:
                print("\n[!] El escaneo no generó archivos. Se cancela el procesamiento automático.")
                
        elif choice == "7":
            print("\n" + "-" * 50)
            print(" EJECUTANDO SINCRONIZACIÓN DE REMITOS DESDE FINNEGANS")
            print("-" * 50)
            try:
                # Ejecutar el script sync_remitos.py en su propio proceso de Python
                subprocess.run([sys.executable, "sync_remitos.py"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"\nError al ejecutar la sincronización: {e}")
            except Exception as e:
                print(f"\nError inesperado: {e}")
                
        elif choice == "8":
            config.print_config()
            
        elif choice == "9":
            manage_ollama()
            
        elif choice == "10":
            print("\nSaliendo del programa. ¡Hasta pronto!")
            sys.exit(0)
        else:
            print("\nOpción no válida. Por favor, ingrese un número del 1 al 10.")
            
        input("\nPresione Enter para volver al menú...")



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario. Saliendo...")
        sys.exit(0)


