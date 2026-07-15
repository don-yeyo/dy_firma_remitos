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
    
    # Set ADF
    for prop in scanner.Properties:
        if prop.PropertyID == 3088: # Document Handling Select
            prop.Value = 1
        elif prop.PropertyID == 3096: # Pages
            prop.Value = 1
            
    if scanner.Items.Count > 0:
        item = scanner.Items.Item(1)
        # Try to set Format to JPG just in case BMP is failing on ADF
        jpg_guid = "{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}"
        for prop in item.Properties:
            if prop.PropertyID == 4106: # Format
                try:
                    prop.Value = jpg_guid
                except:
                    pass
        try:
            image = item.Transfer(jpg_guid)
            print("Escaneo exitoso con JPG.")
        except Exception as e:
            print(f"Error con JPG: {e}")
            try:
                # Try with BMP
                bmp_guid = "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}"
                image = item.Transfer(bmp_guid)
                print("Escaneo exitoso con BMP.")
            except Exception as e2:
                print(f"Error con BMP: {e2}")

if __name__ == "__main__":
    main()
