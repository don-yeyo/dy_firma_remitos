import os
import sys
import time
import threading
from datetime import datetime
import pymysql
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Asegurar que el directorio server/ esté en el path para que los imports locales funcionen bien
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar y crear directorios de salida si no existen al iniciar
    import config
    os.makedirs(config.SCAN_OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.PARSED_DIR, exist_ok=True)
    print(f"[SYSTEM] Servidor API iniciado con éxito.")
    print(f"[SYSTEM] Directorio de escaneo: {os.path.abspath(config.SCAN_OUTPUT_DIR)}")
    print(f"[SYSTEM] Directorio de parseo: {os.path.abspath(config.PARSED_DIR)}")
    config.print_config()
    yield

app = FastAPI(
    title="Don Yeyo - Servidor de Escaneo y Procesamiento de Remitos",
    version="1.0.0",
    lifespan=lifespan
)

# Configuración de CORS para permitir solicitudes desde el frontend de Netlify
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Buffer de logs en memoria
class LogBuffer:
    def __init__(self):
        self.logs = []
        self._lock = threading.Lock()
        
    def add(self, msg: str):
        # Separar múltiples líneas si vienen juntas
        for line in msg.splitlines():
            clean = line.strip()
            if clean:
                timestamp = datetime.now().strftime("%H:%M:%S")
                with self._lock:
                    self.logs.append(f"[{timestamp}] {clean}")
                    # Mantener últimos 250 mensajes de log
                    if len(self.logs) > 250:
                        self.logs.pop(0)
                        
    def clear(self):
        with self._lock:
            self.logs.clear()
            
    def get(self):
        with self._lock:
            return list(self.logs)

log_buffer = LogBuffer()

# Interceptar la consola estándar stdout/stderr y enviarla al buffer de logs de la API
class APIStreamLogger:
    def __init__(self, original_stream, callback):
        self.original_stream = original_stream
        self.callback = callback
        
    def write(self, data):
        self.original_stream.write(data)
        self.original_stream.flush()
        self.callback(data)
        
    def flush(self):
        self.original_stream.flush()
        
    def isatty(self):
        if hasattr(self.original_stream, 'isatty'):
            return self.original_stream.isatty()
        return False

# Redirigir salidas
sys.stdout = APIStreamLogger(sys.stdout, log_buffer.add)
sys.stderr = APIStreamLogger(sys.stderr, log_buffer.add)

# Estado global de tareas activas
active_process = {
    "status": "idle",  # idle, scanning, processing, scanning-and-processing, syncing
}
process_lock = threading.Lock()

@app.get("/api/status")
def get_status():
    """Devuelve el estado del proceso actual y la lista de logs acumulados."""
    return {
        "status": active_process["status"],
        "logs": log_buffer.get()
    }

@app.post("/api/clear-logs")
def clear_logs():
    """Limpia el buffer de logs en pantalla."""
    log_buffer.clear()
    return {"message": "Logs limpiados en el servidor"}

@app.post("/api/scan")
def start_scan():
    """Dispara el proceso de escaneo masivo (Paso 1)."""
    global active_process
    with process_lock:
        if active_process["status"] != "idle":
            return {"status": "error", "message": f"Servidor ocupado. Proceso actual: {active_process['status']}"}
        active_process["status"] = "scanning"
        
    def run_scan():
        try:
            import scanner
            scanner.trigger_scan()
        except Exception as e:
            print(f"[API ERROR] Error en trigger_scan: {e}")
        finally:
            with process_lock:
                active_process["status"] = "idle"
                
    threading.Thread(target=run_scan, daemon=True).start()
    return {"status": "started", "message": "Proceso de escaneo masivo iniciado."}

@app.post("/api/process")
def start_process():
    """Dispara el proceso de análisis por IA (Paso 2)."""
    global active_process
    with process_lock:
        if active_process["status"] != "idle":
            return {"status": "error", "message": f"Servidor ocupado. Proceso actual: {active_process['status']}"}
        active_process["status"] = "processing"
        
    def run_processing():
        try:
            import recognition
            processor = recognition.DocumentProcessor()
            processor.process_all_scans()
        except Exception as e:
            print(f"[API ERROR] Error en process_all_scans: {e}")
        finally:
            with process_lock:
                active_process["status"] = "idle"
                
    threading.Thread(target=run_processing, daemon=True).start()
    return {"status": "started", "message": "Proceso de análisis por IA de imágenes iniciado."}

@app.post("/api/scan-and-process")
def start_scan_and_process():
    """Dispara el proceso completo unificado: Escaneo + Procesamiento IA (Opción 6)."""
    global active_process
    with process_lock:
        if active_process["status"] != "idle":
            return {"status": "error", "message": f"Servidor ocupado. Proceso actual: {active_process['status']}"}
        active_process["status"] = "scanning-and-processing"
        
    def run_full_flow():
        try:
            import scanner
            import recognition
            scanned_files = scanner.trigger_scan()
            if scanned_files:
                print(f"\n[OK] Paso 1 finalizado: Se escanearon {len(scanned_files)} páginas con éxito.")
                print("Iniciando Paso 2: Procesamiento automático de las imágenes...")
                processor = recognition.DocumentProcessor()
                processor.process_all_scans()
            else:
                print("\n[!] El escaneo no generó archivos. Se cancela el procesamiento automático.")
        except Exception as e:
            print(f"[API ERROR] Error en flujo completo: {e}")
        finally:
            with process_lock:
                active_process["status"] = "idle"
                
    threading.Thread(target=run_full_flow, daemon=True).start()
    return {"status": "started", "message": "Flujo completo (Escaneo + Procesamiento IA) iniciado."}

@app.post("/api/sync-finnegans")
def start_sync():
    """Dispara el proceso de sincronización con el ERP Finnegans (Opción 7)."""
    global active_process
    with process_lock:
        if active_process["status"] != "idle":
            return {"status": "error", "message": f"Servidor ocupado. Proceso actual: {active_process['status']}"}
        active_process["status"] = "syncing"
        
    def run_sync():
        try:
            import subprocess
            # Ejecutar el script local sync_remitos.py
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync_remitos.py")
            subprocess.run([sys.executable, script_path], check=True)
        except Exception as e:
            print(f"[API ERROR] Error en sync_remitos: {e}")
        finally:
            with process_lock:
                active_process["status"] = "idle"
                
    threading.Thread(target=run_sync, daemon=True).start()
    return {"status": "started", "message": "Proceso de sincronización con Finnegans iniciado."}

@app.get("/api/history")
def get_history():
    """Consulta la base de datos MySQL de AWS y devuelve el historial de los últimos 20 remitos procesados."""
    import config
    try:
        connection = pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=6
        )
        with connection.cursor() as cursor:
            # Traer los últimos 20 remitos insertados o actualizados
            sql = """
                SELECT finne_transaccionID as transaccion_id, finne_Numero as numero, 
                       finne_Fecha as fecha, finne_Copias as copias,
                       bot_confirmado_cliente as confirmado_cliente, 
                       bot_confirmado_distribuidor as confirmado_distribuidor,
                       (ocr_original IS NOT NULL) as original, 
                       (ocr_duplicado IS NOT NULL) as duplicado,
                       (ocr_triplicado IS NOT NULL) as triplicado,
                       (ocr_cuatriplcado IS NOT NULL) as cuatriplicado
                FROM remitos
                ORDER BY id DESC
                LIMIT 20
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
        connection.close()
        
        # Formatear adecuadamente para el frontend
        formatted_rows = []
        for r in rows:
            formatted_rows.append({
                "transaccion_id": r["transaccion_id"],
                "numero": r["numero"] if r["numero"] else "Sin número",
                "fecha": r["fecha"].strftime("%Y-%m-%d") if isinstance(r["fecha"], datetime) or hasattr(r["fecha"], "strftime") else str(r["fecha"]),
                "copias": r["copias"] if r["copias"] is not None else 2,
                "confirmado_cliente": bool(r["confirmado_cliente"]),
                "confirmado_distribuidor": bool(r["confirmado_distribuidor"]),
                "copias_escaneadas": {
                    "original": bool(r["original"]),
                    "duplicado": bool(r["duplicado"]),
                    "triplicado": bool(r["triplicado"]),
                    "cuatriplicado": bool(r["cuatriplicado"])
                }
            })
        return formatted_rows
    except Exception as e:
        print(f"[API ERROR] Error leyendo historial SQL: {e}")
        return []

@app.get("/api/config")
def get_config():
    """Devuelve la configuración actual del sistema omitiendo datos sensibles."""
    import config
    return {
        "SCANNER_NAME": config.SCANNER_NAME,
        "SCAN_OUTPUT_DIR": config.SCAN_OUTPUT_DIR,
        "SCAN_DPI": config.SCAN_DPI,
        "SCAN_COLOR_MODE": config.SCAN_COLOR_MODE,
        "SCAN_FORMAT": config.SCAN_FORMAT,
        "SCAN_SOURCE": config.SCAN_SOURCE,
        "SCAN_ADF_DELAY": config.SCAN_ADF_DELAY,
        "SCAN_FILE_WRITE_DELAY": config.SCAN_FILE_WRITE_DELAY,
        "AI_PROVIDER": config.AI_PROVIDER,
        "DB_HOST": config.DB_HOST,
        "DB_NAME": config.DB_NAME,
        "DB_USER": config.DB_USER
    }

if __name__ == "__main__":
    import uvicorn
    # Iniciar localmente escuchando en todas las interfaces de red de la LAN en el puerto 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
