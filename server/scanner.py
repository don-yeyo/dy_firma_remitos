import os
import time
import win32com.client
import pythoncom
import config
import state

import win32print

# Constantes WIA
WIA_DEVICE_TYPE_SCANNER = 1

# Propiedades del Dispositivo (Root)
WIA_DPS_DOCUMENT_HANDLING_SELECT = 3088  # 1 = Feeder (ADF), 2 = Flatbed
WIA_DPS_DOCUMENT_HANDLING_STATUS = 3087  # 1 = Paper Queue (Hay papel en bandeja)

# Propiedades del Item (Configuración del Escaneo)
WIA_IPS_CUR_INTENT = 6146       # Modo de color: 1=Color, 2=Grayscale, 4=B&W
WIA_IPS_XRES = 6147             # DPI Horizontal
WIA_IPS_YRES = 6148             # DPI Vertical
WIA_IPS_XPOS = 6149             # Posición X inicial
WIA_IPS_YPOS = 6150             # Posición Y inicial
WIA_IPS_XEXTENT = 6151          # Ancho del escaneo
WIA_IPS_YEXTENT = 6152          # Alto del escaneo

def get_device_manager():
    """Inicializa y devuelve el Administrador de Dispositivos WIA."""
    pythoncom.CoInitialize()
    try:
        return win32com.client.Dispatch("Wia.DeviceManager")
    except Exception as e:
        raise RuntimeError(f"No se pudo inicializar WIA.DeviceManager. ¿Está en Windows? Error: {e}")

def test_device_connection(device_id, name):
    """Realiza una prueba de conexión al escáner y a la cola de impresión de Windows."""
    print(f"\n--- Probando conexión con {name} ---")
    scanner_ok = False
    printer_ok = False
    
    # 1. Prueba de Escáner (WIA)
    try:
        manager = get_device_manager()
        device_info = None
        for i in range(1, manager.DeviceInfos.Count + 1):
            info = manager.DeviceInfos.Item(i)
            if info.DeviceID == device_id:
                device_info = info
                break
        
        if device_info:
            scanner = device_info.Connect()
            print("[OK] [Escáner (WIA)]: Conexión exitosa. El escáner responde.")
            scanner_ok = True
        else:
            print("[ERROR] [Escáner (WIA)]: Dispositivo no encontrado en WIA.")
    except Exception as e:
        print(f"[ERROR] [Escáner (WIA)]: Error al conectar: {e}")
        
    # 2. Prueba de Impresora (win32print)
    try:
        # Intentar abrir la cola de impresión usando el nombre del escáner
        handle = win32print.OpenPrinter(name)
        info = win32print.GetPrinter(handle, 2)
        print("[OK] [Impresora (Windows)]: Conexión exitosa con la cola de impresión.")
        print(f"   - Puerto: {info['pPortName']}")
        print(f"   - Driver: {info['pDriverName']}")
        print(f"   - Trabajos en cola: {info['cJobs']}")
        win32print.ClosePrinter(handle)
        printer_ok = True
    except Exception as e:
        print(f"[WARN] [Impresora (Windows)]: No se pudo abrir la cola de impresión '{name}' directamente: {e}")
        print("   Nota: Es normal si el nombre del escáner difiere ligeramente del nombre de la impresora mapeada.")
        
    return scanner_ok, printer_ok


def get_system_printers():
    """Obtiene una lista de nombres de todas las impresoras instaladas en Windows."""
    try:
        printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        return [p[2] for p in printers]
    except Exception as e:
        print(f"Error al listar impresoras de Windows: {e}")
        return []

def get_system_printers_info():
    """Obtiene una lista de diccionarios con información detallada de cada impresora."""
    printers_info = []
    try:
        printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        for p in printers:
            name = p[2]
            try:
                handle = win32print.OpenPrinter(name)
                info = win32print.GetPrinter(handle, 2)
                printers_info.append({
                    "name": name,
                    "driver": info["pDriverName"],
                    "port": info["pPortName"],
                    "jobs": info["cJobs"]
                })
                win32print.ClosePrinter(handle)
            except Exception:
                printers_info.append({
                    "name": name,
                    "driver": "Desconocido",
                    "port": "Desconocido",
                    "jobs": 0
                })
    except Exception as e:
        print(f"Error al listar impresoras de Windows: {e}")
    return printers_info

def purge_printer_queue(printer_name):
    """Intenta eliminar todos los trabajos acumulados en la cola de impresión."""
    print(f"-> Detectados trabajos atascados en '{printer_name}'. Intentando vaciar la cola...")
    try:
        # Intentar purgar usando la API win32print (requiere permisos administrativos)
        handle = win32print.OpenPrinter(printer_name, {"DesiredAccess": win32print.PRINTER_ACCESS_ADMINISTER})
        win32print.SetPrinter(handle, 0, None, win32print.PRINTER_CONTROL_PURGE)
        win32print.ClosePrinter(handle)
        print(f"✔ Cola de impresión '{printer_name}' vaciada con éxito mediante API Windows.")
        return True
    except Exception as e:
        # Método alternativo con PowerShell si la API falla por permisos restringidos del handle
        import subprocess
        try:
            cmd = f'powershell.exe -Command "Get-PrintJob -PrinterName \\"{printer_name}\\" | Remove-PrintJob"'
            subprocess.run(cmd, shell=True, check=True)
            print(f"✔ Cola de impresión '{printer_name}' vaciada con éxito mediante PowerShell.")
            return True
        except Exception as pe:
            print(f"⚠ No se pudo vaciar la cola automáticamente: {pe}")
            print("   Para solucionarlo manualmente, abre la cola de impresión en Windows, haz clic en 'Impresora' -> 'Cancelar todos los documentos'.")
            return False

def send_test_print_page(printer_name):
    """
    Lista las impresoras instaladas en Windows mostrando su estado (trabajos en cola)
    y permite seleccionar explícitamente cuál probar para evitar colas bloqueadas.
    """
    import subprocess
    
    printers_info = get_system_printers_info()
    if not printers_info:
        print("❌ No se encontraron impresoras instaladas en Windows.")
        return False
        
    print("\nImpresoras detectadas en Windows:")
    clean_name = printer_name.lower().replace("wia", "").replace("scanner", "").replace("escáner", "").strip()
    sug_idx = -1
    
    for idx, p in enumerate(printers_info):
        is_match = clean_name in p["name"].lower()
        match_str = " (Sugerida)" if is_match else ""
        if is_match and sug_idx == -1:
            sug_idx = idx
        print(f"  {idx + 1}. {p['name']}{match_str}")
        print(f"     Driver: {p['driver']}")
        print(f"     Puerto: {p['port']} | Trabajos en cola: {p['jobs']}")
        print("-" * 40)
        
    prompt = f"Seleccione la impresora para enviar la página de prueba (1-{len(printers_info)})"
    if sug_idx != -1:
        prompt += f" [Enter para {printers_info[sug_idx]['name']}]: "
    else:
        prompt += " o Enter para cancelar: "
        
    sel = input(prompt).strip()
    
    target_printer = None
    target_jobs = 0
    if not sel:
        if sug_idx != -1:
            target_printer = printers_info[sug_idx]["name"]
            target_jobs = printers_info[sug_idx]["jobs"]
        else:
            print("Operación cancelada.")
            return False
    elif sel.isdigit():
        i = int(sel) - 1
        if 0 <= i < len(printers_info):
            target_printer = printers_info[i]["name"]
            target_jobs = printers_info[i]["jobs"]
        else:
            print("Selección fuera de rango.")
            return False
    else:
        print("Operación cancelada.")
        return False
        
    # Purga automática si hay trabajos en cola
    if target_jobs > 0:
        purge_printer_queue(target_printer)
        # Dar tiempo a Windows para limpiar los trabajos
        time.sleep(1.5)
        
    print(f"\n--- Enviando página de prueba oficial a: '{target_printer}' ---")
    try:
        # Comando oficial de Windows para mandar la página de prueba del driver
        cmd = f'rundll32.exe printui.dll,PrintUIEntry /k /n "{target_printer}"'
        subprocess.run(cmd, shell=True, check=True)
        print(f"✔ Comando enviado con éxito. La página de prueba oficial se envió a '{target_printer}'.")
        return True
    except Exception as e:
        print(f"❌ Error al enviar la página de prueba a '{target_printer}': {e}")
        return False







def list_devices():
    """Retorna una lista de diccionarios con información de los escáneres disponibles."""
    devices = []
    try:
        manager = get_device_manager()
        for i in range(1, manager.DeviceInfos.Count + 1):
            info = manager.DeviceInfos.Item(i)
            # Solo escáneres
            if info.Type == WIA_DEVICE_TYPE_SCANNER:
                device_details = {
                    "id": info.DeviceID,
                    "name": "",
                    "description": ""
                }
                for prop in info.Properties:
                    if prop.Name == "Name":
                        device_details["name"] = prop.Value
                    elif prop.Name == "Description":
                        device_details["description"] = prop.Value
                
                # Si el nombre quedó vacío, usar la descripción o el ID
                if not device_details["name"]:
                    device_details["name"] = device_details["description"] or info.DeviceID
                devices.append(device_details)
    except Exception as e:
        print(f"Error al listar dispositivos WIA: {e}")
    return devices

def configure_scanner_properties(scanner_item, root_device):
    """Establece los parámetros configurados en el .env en el escáner."""
    
    # 1. Configurar Origen del Papel en el dispositivo raíz
    if str(config.SCAN_SOURCE).isdigit():
        source_val = int(config.SCAN_SOURCE)
    else:
        source_val = 1 if config.SCAN_SOURCE == "ADF" else 2
        
    try:
        # Configurar Document Handling Select (3088)
        for prop in root_device.Properties:
            if prop.PropertyID == 3088: # WIA_DPS_DOCUMENT_HANDLING_SELECT
                try:
                    subtype = prop.SubType
                    if subtype == 2: # List
                        allowed_vals = list(prop.SubTypeValues)
                        print(f"   [WIA] Valores de origen (3088) permitidos por el driver: {allowed_vals}")
                    elif subtype == 3: # Flag/Bitmask
                        print(f"   [WIA] Máscara de bits de origen (3088) permitida: {prop.SubTypeValues}")
                except:
                    pass
                prop.Value = source_val
                print(f"-> Origen del papel configurado como: {config.SCAN_SOURCE} (Valor: {source_val})")
            
            # Configurar Pages (3096) - 1 para que devuelva una por una en cualquier modo de alimentador (1=Feeder, 4=Duplex, 5=Feeder+Duplex)
            if prop.PropertyID == 3096 and source_val in (1, 4, 5):
                try:
                    prop.Value = 1
                except:
                    pass
    except Exception as e:
        print(f"Advertencia: No se pudo configurar el origen del papel ({config.SCAN_SOURCE}). Error: {e}")

    # 2. Configurar Propiedades de Calidad en el Item de Escaneo (DPI, Color) y origen si está expuesto
    for prop in scanner_item.Properties:
        if prop.PropertyID == 6146: # WIA_IPS_CUR_INTENT
            try: prop.Value = config.SCAN_COLOR_MODE
            except: pass
        elif prop.PropertyID == 6147: # WIA_IPS_XRES
            try: prop.Value = config.SCAN_DPI
            except: pass
        elif prop.PropertyID == 6148: # WIA_IPS_YRES
            try: prop.Value = config.SCAN_DPI
            except: pass
        elif prop.PropertyID in (3088, 4103): # Configurar origen en el ítem si el driver lo expone
            try: prop.Value = source_val
            except: pass

def has_paper_in_feeder(root_device):
    """Verifica si queda papel en la bandeja del ADF."""
    if config.SCAN_SOURCE != "ADF":
        return True # Flatbed no tiene "bandeja"
    
    try:
        for prop in root_device.Properties:
            if prop.PropertyID == 3087: # WIA_DPS_DOCUMENT_HANDLING_STATUS
                return (prop.Value & 1) == 1
    except Exception:
        pass
    return True

def trigger_scan():
    """Busca el escáner configurado y dispara el escaneo masivo."""
    target_name = config.SCANNER_NAME.lower()
    print(f"Buscando escáner compatible con el nombre: '{config.SCANNER_NAME}'...")
    
    devices = list_devices()
    if not devices:
        print("No se encontraron escáneres WIA conectados o instalados en el sistema.")
        return []
        
    selected_device_id = None
    for dev in devices:
        print(f"  Encontrado: [ID: {dev['id']}] - Nombre: {dev['name']}")
        if target_name in dev['name'].lower() or target_name in dev['id'].lower():
            selected_device_id = dev['id']
            print(f"  -> Coincidencia encontrada: {dev['name']}")
            break
            
    if not selected_device_id:
        selected_device_id = devices[0]['id']
        print(f"  -> Seleccionado por defecto: {devices[0]['name']}")

    scanned_files = []
    scan_source = config.SCAN_SOURCE  # "ADF" o "FLATBED"
    if str(scan_source).isdigit():
        source_val = int(scan_source)
    else:
        source_val = 1 if scan_source == "ADF" else 2
    max_retries = 3
    
    def connect_scanner():
        """Crea una conexión WIA fresca al escáner."""
        mgr = get_device_manager()
        dev_info = None
        for i in range(1, mgr.DeviceInfos.Count + 1):
            if mgr.DeviceInfos.Item(i).DeviceID == selected_device_id:
                dev_info = mgr.DeviceInfos.Item(i)
                break
        if not dev_info:
            raise RuntimeError("No se pudo obtener la información de conexión del dispositivo.")
        return dev_info.Connect()

    def select_scanner_item(scanner_device, source):
        """Busca el sub-ítem WIA correspondiente a ADF o Flatbed usando categorías WIA 2.0."""
        WIA_CATEGORY_FLATBED = "{DEB50B54-3501-452A-B948-ABF0D151240F}"
        WIA_CATEGORY_FEEDER = "{FE179EF7-22B2-4139-9FA4-FB0F167AF730}"
        
        if scanner_device.Items.Count <= 1:
            return scanner_device.Items.Item(1)
            
        for i in range(1, scanner_device.Items.Count + 1):
            item = scanner_device.Items.Item(i)
            category = ""
            try:
                for prop in item.Properties:
                    if prop.PropertyID == 4098: # WIA_IPA_ITEM_CATEGORY
                        category = str(prop.Value).upper()
                        break
            except Exception:
                pass
            
            if source == "ADF" and WIA_CATEGORY_FEEDER in category:
                print(f"  -> Seleccionado sub-ítem {i} correspondiente a Alimentador ADF (Categoría WIA).")
                return item
            elif source == "FLATBED" and WIA_CATEGORY_FLATBED in category:
                print(f"  -> Seleccionado sub-ítem {i} correspondiente a Vidrio/Flatbed (Categoría WIA).")
                return item
                
        # Fallback al Item 1
        print("  -> No se encontró sub-ítem por categoría. Utilizando sub-ítem 1 por defecto.")
        return scanner_device.Items.Item(1)

    try:
        print("Estableciendo conexión con el escáner...")
        scanner = connect_scanner()
        print("Conexión establecida con éxito.")
        
        if scanner.Items.Count == 0:
            raise RuntimeError("El escáner no contiene ítems de escaneo.")
            
        scanner_item = select_scanner_item(scanner, scan_source)
        configure_scanner_properties(scanner_item, scanner)
        
        page_num = 1
        print("\nIniciando secuencia de escaneo masivo...")
        
        while True:
            if state.is_cancel_requested():
                print("[WARN] Escaneo cancelado por solicitud del usuario.")
                raise state.ProcessCancelledException("Escaneo cancelado por el usuario.")
                
            state.update_progress(f"Escaneando página {page_num}...", page_num, 0)
            
            if page_num > 1:
                # Darle tiempo al alimentador (ADF) físico de la Ricoh para terminar de acomodar
                # la siguiente hoja antes de volver a solicitar la transferencia de red.
                print(f"  Esperando {config.SCAN_ADF_DELAY}s para la transición de página...")
                time.sleep(config.SCAN_ADF_DELAY)
                
            # Se elimina la comprobación anticipada del sensor físico (has_paper_in_feeder),
            # ya que muchos controladores WIA de red (incluyendo el de Ricoh) reportan valores imprecisos
            # para la propiedad 3087, arrojando falsos negativos. Dejamos que el primer intento de Transfer()
            # intente jalar el papel físicamente y, si está vacío, se gestione a través de su excepción de red WIA.
            print(f"Escaneando página {page_num}...")
            
            image = None
            last_err = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    guids_to_try = [
                        "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}", # BMP (Recomendado para compatibilidad WIA/WSD)
                        "{B96B3CB1-0728-11D3-9D7B-0000F81EF32E}", # TIFF
                        "{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}"  # JPG
                    ]
                    
                    for guid in guids_to_try:
                        try:
                            image = scanner_item.Transfer(guid)
                            break
                        except Exception as trans_e:
                            last_err = trans_e
                    
                    if image:
                        break  # Éxito, salimos del loop de reintentos
                    
                    raise Exception(f"Fallo en la transferencia WIA: {last_err}")
                    
                except Exception as retry_err:
                    last_err = retry_err
                    err_str = str(retry_err).lower()
                    is_efail = "2147467259" in err_str or "e_fail" in err_str or "no especificado" in err_str
                    
                    if is_efail and attempt < max_retries:
                        if page_num == 1:
                            print(f"  [WARN] Intento {attempt}/{max_retries} falló (E_FAIL). Reconectando al escáner...")
                        else:
                            print(f"  Verificando si restan hojas en el alimentador (Intento {attempt}/{max_retries})...")
                        time.sleep(2)
                        try:
                            scanner = connect_scanner()
                            if scanner.Items.Count > 0:
                                scanner_item = select_scanner_item(scanner, scan_source)
                                configure_scanner_properties(scanner_item, scanner)
                        except Exception:
                            pass
                    elif is_efail and attempt == max_retries:
                        # Ya agotamos los reintentos con E_FAIL
                        break
                    else:
                        break  # Otro tipo de error, salimos
            
            if image:
                # Éxito: guardar la imagen
                timestamp = int(time.time() * 1000)
                ext = image.FileExtension.lower()
                temp_filename = f"temp_scan_{timestamp}.{ext}"
                temp_path = os.path.abspath(os.path.join(config.SCAN_OUTPUT_DIR, temp_filename))
                
                filename = f"scan_{timestamp}_pag_{page_num}.{config.SCAN_FORMAT.lower()}"
                filepath = os.path.join(config.SCAN_OUTPUT_DIR, filename)
                abspath = os.path.abspath(filepath)
                
                if os.path.exists(temp_path): os.remove(temp_path)
                image.SaveFile(temp_path)
                
                # Pausa breve para asegurar que el sistema operativo libere el descriptor de escritura del archivo
                time.sleep(config.SCAN_FILE_WRITE_DELAY)
                
                import cv2
                img_data = cv2.imread(temp_path)
                if img_data is not None:
                    cv2.imwrite(abspath, img_data)
                    print(f"  Página {page_num} procesada y guardada en: {filepath}")
                    scanned_files.append(abspath)
                else:
                    try:
                        # Fallback con PIL para decodificar y convertir el BMP a JPEG real en lugar de copiarlo crudo
                        from PIL import Image
                        with Image.open(temp_path) as img:
                            img.convert("RGB").save(abspath, "JPEG")
                        print(f"  Página {page_num} convertida y guardada en: {filepath} (PIL fallback)")
                        scanned_files.append(abspath)
                    except Exception as pil_err:
                        import shutil
                        shutil.copy(temp_path, abspath)
                        print(f"  Página {page_num} guardada directamente en: {filepath} (shutil fallback): {pil_err}")
                        scanned_files.append(abspath)
                
                if os.path.exists(temp_path): os.remove(temp_path)
                page_num += 1
                
                if scan_source == "FLATBED" or source_val == 2:
                    # En modo Flatbed interactivo, preguntar si quiere seguir
                    cont = input("¿Colocar otra hoja en el vidrio y escanear? (s/n): ").strip().lower()
                    if cont != "s":
                        break
                    # Reconectar para cada página en Flatbed
                    try:
                        scanner = connect_scanner()
                        scanner_item = select_scanner_item(scanner, scan_source)
                        configure_scanner_properties(scanner_item, scanner)
                    except Exception as rc_err:
                        print(f"Error al reconectar para la siguiente página: {rc_err}")
                        break
                else:
                    time.sleep(0.5)
                
            else:
                # Error: analizar qué pasó
                err_str = str(last_err).lower()
                if "conflicto (409)" in err_str and page_num > 1:
                    print("El ADF se ha quedado sin páginas (Escaneo masivo finalizado).")
                elif "2147467259" in err_str or "e_fail" in err_str or "no especificado" in err_str:
                    print(f"\n[!] ERROR DE RED/DRIVER E_FAIL (-2147467259) DESPUÉS DE {max_retries} REINTENTOS [!]")
                    print("El escáner Ricoh rechazó la petición de Pull Scan desde el ADF.")
                    raise Exception("El escáner Ricoh rechazó la petición de Pull Scan desde el ADF (Error de red o hardware E_FAIL).")
                elif any(x in err_str for x in ["80210015", "vacio", "paper empty", "2145320957", "alimentador", "2145320946", "8021000e"]):
                    if page_num > 1:
                        print("El ADF se ha quedado sin páginas (Escaneo masivo finalizado).")
                    else:
                        print("\n[!] La bandeja del alimentador automático (ADF) está vacía o el sensor no la detecta.")
                        raise Exception("La bandeja del alimentador automático (ADF) está vacía o no se detectan documentos.")
                elif "conflicto (409)" in err_str and page_num == 1:
                    print("El escáner indica Conflicto (409). Asegúrese de que haya papel en la bandeja ADF.")
                    raise Exception("Conflicto con el escáner (409). Verifique que haya papel en el alimentador ADF.")
                else:
                    print(f"Finalizando o interrupción en el escaneo: {last_err}")
                    raise Exception(f"Fallo durante el escaneo físico: {last_err}")
                break
                
        print(f"\nProceso finalizado. Total de páginas escaneadas: {len(scanned_files)}")
    except Exception as e:
        print(f"Error crítico durante el proceso de escaneo: {e}")
        
    return scanned_files

