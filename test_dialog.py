import win32com.client
import pythoncom

def main():
    pythoncom.CoInitialize()
    manager = win32com.client.Dispatch("Wia.DeviceManager")
    dialog = win32com.client.Dispatch("Wia.CommonDialog")
    
    target_id = None
    for i in range(1, manager.DeviceInfos.Count + 1):
        if "RICOH IM C300" in manager.DeviceInfos.Item(i).DeviceID or "RICOH IM C300" in manager.DeviceInfos.Item(i).Properties("Name").Value:
            target_id = manager.DeviceInfos.Item(i).DeviceID
            break
            
    if not target_id: return
    scanner = manager.DeviceInfos.Item(target_id).Connect()
    
    for prop in scanner.Properties:
        if prop.PropertyID == 3088: # Document Handling Select
            prop.Value = 1
            
    if scanner.Items.Count > 0:
        item = scanner.Items.Item(1)
        bmp_guid = "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}"
        try:
            print("Escaneando con CommonDialog (verás una barra de progreso de Windows)...")
            image = dialog.ShowTransfer(item, bmp_guid, False)
            print("¡Éxito! Imagen recibida.")
        except Exception as e:
            print(f"Error con CommonDialog: {e}")

if __name__ == "__main__":
    main()
