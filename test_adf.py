import win32com.client
import pythoncom
import time

def main():
    pythoncom.CoInitialize()
    manager = win32com.client.Dispatch("Wia.DeviceManager")
    
    target_id = None
    for i in range(1, manager.DeviceInfos.Count + 1):
        info = manager.DeviceInfos.Item(i)
        name = ""
        for p in info.Properties:
            if p.Name == "Name": name = p.Value
        if "RICOH IM C300 [58387958FB4C]" in name or "RICOH IM C300" in name:
            target_id = info.DeviceID
            break
            
    if not target_id:
        print("Escáner no encontrado.")
        return
        
    print(f"Conectando a {target_id}...")
    info = None
    for i in range(1, manager.DeviceInfos.Count + 1):
        if manager.DeviceInfos.Item(i).DeviceID == target_id:
            info = manager.DeviceInfos.Item(i)
            break
            
    scanner = info.Connect()
    
    print("\n[Paso 1] Verificando Document Handling Select (3088)...")
    for prop in scanner.Properties:
        if prop.PropertyID == 3088:
            print(f"  Valor actual: {prop.Value}")
            try:
                print("  Intentando cambiar a 1 (ADF / Feeder)...")
                prop.Value = 1
                print(f"  Nuevo valor: {prop.Value}")
            except Exception as e:
                print(f"  ERROR al cambiar el valor: {e}")
                
    print("\n[Paso 2] Intentando Transferencia...")
    if scanner.Items.Count > 0:
        item = scanner.Items.Item(1)
        bmp_guid = "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}"
        try:
            image = item.Transfer(bmp_guid)
            print(f"¡Éxito! Imagen recibida: {image.Width}x{image.Height}")
        except Exception as e:
            print(f"Error en Transfer: {e}")
    else:
        print("No hay Items.")

if __name__ == "__main__":
    main()
