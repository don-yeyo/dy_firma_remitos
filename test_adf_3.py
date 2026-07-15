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
    
    for prop in scanner.Properties:
        if prop.PropertyID == 3088: prop.Value = 1 # ADF
        elif prop.PropertyID == 3096: prop.Value = 0 # Pages = ALL
        elif prop.PropertyID == 3097: 
            try: prop.Value = 1 # 1=Letter, 0=A4
            except: pass
            
    if scanner.Items.Count > 0:
        item = scanner.Items.Item(1)
        bmp_guid = "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}"
        try:
            image = item.Transfer(bmp_guid)
            print(f"¡Éxito ADF Avanzado! Imagen recibida: {image.Width}x{image.Height}")
        except Exception as e:
            print(f"Error ADF Avanzado: {e}")

if __name__ == "__main__":
    main()
