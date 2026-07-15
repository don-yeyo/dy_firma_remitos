import os
import shutil
import csv
import sys

# Agregar la ruta local
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import recognition
import config

def main():
    # 1. Limpiar parsed_documents
    if os.path.exists(config.PARSED_DIR):
        for f in os.listdir(config.PARSED_DIR):
            file_path = os.path.join(config.PARSED_DIR, f)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"No se pudo eliminar {f}: {e}")
    else:
        os.makedirs(config.PARSED_DIR)
    print("✔ Carpeta parsed_documents vaciada.")

    # 2. Reiniciar processed_log.csv
    with open(config.CSV_LOG_PATH, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "image_name", "status", "detections_count"])
    print("✔ Log CSV reiniciado.")

    # 3. Correr procesamiento de recognition
    processor = recognition.DocumentProcessor()
    processor.process_all_scans()

    # 4. Mostrar el JSON resultante
    json_files = [f for f in os.listdir(config.PARSED_DIR) if f.endswith(".json")]
    if json_files:
        json_path = os.path.join(config.PARSED_DIR, json_files[0])
        print(f"\n✔ Resultado JSON ({json_files[0]}):")
        with open(json_path, 'r', encoding='utf-8') as jf:
            print(jf.read())
    else:
        print("❌ No se generó ningún JSON.")

if __name__ == "__main__":
    main()
