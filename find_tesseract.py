import os

def find_tesseract():
    print("Iniciando búsqueda de tesseract.exe...")
    search_dirs = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        os.path.expanduser("~")
    ]
    
    found_paths = []
    for base_dir in search_dirs:
        if not os.path.exists(base_dir):
            continue
        print(f"Buscando en: {base_dir} (puede demorar unos segundos)...")
        try:
            # Búsqueda superficial en AppData o Program Files
            for root, dirs, files in os.walk(base_dir):
                # Limitar profundidad para que sea rápido
                depth = root.replace(base_dir, '').count(os.sep)
                if depth > 4: # No ir muy profundo en carpetas
                    dirs.clear() # Detener recursión profunda
                    continue
                if "tesseract.exe" in files:
                    full_path = os.path.join(root, "tesseract.exe")
                    found_paths.append(full_path)
                    print(f"¡Encontrado!: {full_path}")
        except Exception as e:
            pass
            
    if found_paths:
        print("\nSe encontraron las siguientes rutas de Tesseract:")
        for p in found_paths:
            print(f"  - {p}")
    else:
        print("\n❌ No se encontró 'tesseract.exe' en ninguna de las ubicaciones comunes.")
        print("Asegúrate de haber descargado e instalado Tesseract OCR desde:")
        print("https://github.com/UB-Mannheim/tesseract/wiki")

if __name__ == "__main__":
    find_tesseract()
