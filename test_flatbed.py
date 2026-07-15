import win32com.client
import pythoncom

def main():
    pythoncom.CoInitialize()
    manager = win32com.client.Dispatch("Wia.DeviceManager")
    
    target_id = None
    for i in range(1, manager.DeviceInfos.Count + 1):
        if "RICOH IM C300" in manager.DeviceInfos.Item(i).DeviceID or "RICOH IM C300" in manager.DeviceInfos.Item(i).Properties("Name").Value:
            target_id = manager.DeviceInfos.Item(i).DeviceID
            break
            
    if not target_id: return
    scanner = manager.DeviceInfos.Item(target_id).Connect()
    
    # 2 = Flatbed (Cama Plana)
    for prop in scanner.Properties:
        if prop.PropertyID == 3088:
            prop.Value = 2
            print("Seteado a Flatbed (2)")
            
    if scanner.Items.Count > 0:
        item = scanner.Items.Item(1)
        bmp_guid = "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}"
        try:
            image = item.Transfer(bmp_guid)
            print(f"¡Éxito FLATBED! Imagen de {image.Width}x{image.Height}")
        except Exception as e:
            print(f"Error FLATBED: {e}")

if __name__ == "__main__":
    main()
