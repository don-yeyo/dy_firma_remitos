import win32com.client
import pythoncom

def get_prop_type_name(prop):
    try:
        return str(prop.Name)
    except:
        return "Unknown"

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
    
    print("\n--- PROPIEDADES DEL DISPOSITIVO RAIZ ---")
    for prop in scanner.Properties:
        try:
            print(f"[{prop.PropertyID}] {get_prop_type_name(prop)} = {prop.Value}")
        except Exception as e:
            print(f"[{prop.PropertyID}] {get_prop_type_name(prop)} = <Error al leer: {e}>")
            
    if scanner.Items.Count > 0:
        item = scanner.Items.Item(1)
        print("\n--- PROPIEDADES DEL ITEM 1 (ESCÁNER) ---")
        for prop in item.Properties:
            try:
                print(f"[{prop.PropertyID}] {get_prop_type_name(prop)} = {prop.Value}")
            except Exception as e:
                print(f"[{prop.PropertyID}] {get_prop_type_name(prop)} = <Error al leer: {e}>")
    else:
        print("\nEl escáner no tiene Items.")

if __name__ == "__main__":
    main()
