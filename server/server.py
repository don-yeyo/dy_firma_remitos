import os
import sys
import time
import threading
import glob
import contextlib
from datetime import datetime, timedelta
import pymysql
from fastapi import FastAPI, BackgroundTasks, Body, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Asegurar que el directorio server/ esté en el path para que los imports locales funcionen bien
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from contextlib import asynccontextmanager
import config
import state

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar y crear directorios de salida si no existen al iniciar
    os.makedirs(config.SCAN_OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.PARSED_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
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

# Middleware de Autenticación por Clave Secreta (X-API-Key)
@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    # Solicitudes OPTIONS (CORS Preflight) pasan sin verificar clave
    if request.method == "OPTIONS":
        return await call_next(request)

    # Rutas públicas permitidas (documentación Swagger, esquemas, favicon)
    public_paths = ["/docs", "/redoc", "/openapi.json", "/favicon.ico"]
    if any(request.url.path == path or request.url.path.startswith(path + "/") for path in public_paths):
        return await call_next(request)

    # Verificar clave de API si está configurada
    if config.API_SECRET_KEY:
        incoming_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
        if incoming_key != config.API_SECRET_KEY:
            return JSONResponse(
                status_code=401,
                content={"detail": "Acceso no autorizado. Encabezado X-API-Key ausente o invalido."}
            )

    return await call_next(request)

# Montar carpeta de documentos escaneados físicamente
app.mount("/scanned_documents", StaticFiles(directory=config.SCAN_OUTPUT_DIR), name="scanned_documents")

def rotate_logs():
    """Elimina archivos de log antiguos en la carpeta logs/ con antigüedad mayor a LOG_ROTATION_DAYS."""
    days_to_keep = getattr(config, "LOG_ROTATION_DAYS", 7)
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    log_files = glob.glob(os.path.join("logs", "*.log"))
    deleted_count = 0
    for fpath in log_files:
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
            if mtime < cutoff_date:
                os.remove(fpath)
                deleted_count += 1
        except Exception as ex:
            print(f"[LOG ROTATION ERROR] No se pudo eliminar {fpath}: {ex}")
    if deleted_count > 0:
        print(f"[LOG ROTATION] Se eliminaron {deleted_count} archivos de log con antigüedad superior a {days_to_keep} días.")

class DualStream:
    """Permite escribir en consola y archivo a la vez con protección frente a concurrencia."""
    def __init__(self, file_stream, console_stream):
        self.file_stream = file_stream
        self.console_stream = console_stream
        
    def write(self, data):
        # Escribir en archivo con control de excepciones por cierre de hilo
        if hasattr(self, 'file_stream') and self.file_stream:
            try:
                if not getattr(self.file_stream, 'closed', True):
                    self.file_stream.write(data)
                    self.file_stream.flush()
            except Exception:
                pass
        
        # Escribir siempre en consola original
        if hasattr(self, 'console_stream') and self.console_stream:
            try:
                self.console_stream.write(data)
                self.console_stream.flush()
            except Exception:
                pass
        
    def flush(self):
        if hasattr(self, 'file_stream') and self.file_stream:
            try:
                if not getattr(self.file_stream, 'closed', True):
                    self.file_stream.flush()
            except Exception:
                pass
        if hasattr(self, 'console_stream') and self.console_stream:
            try:
                self.console_stream.flush()
            except Exception:
                pass
        
    def isatty(self):
        if hasattr(self, 'console_stream') and self.console_stream:
            try:
                if hasattr(self.console_stream, 'isatty'):
                    return self.console_stream.isatty()
            except Exception:
                pass
        return False

@contextlib.contextmanager
def action_logging(action_name: str):
    """Context manager para redirigir stdout/stderr a archivo y consola simultáneamente."""
    os.makedirs("logs", exist_ok=True)
    try:
        rotate_logs()
    except Exception as e:
        print(f"[LOG ROTATION ERROR] {e}")
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{action_name}_{timestamp}.log"
    log_filepath = os.path.abspath(os.path.join("logs", log_filename))
    
    print(f"[SYSTEM] Iniciando registro físico en log: {log_filepath}")
    f = open(log_filepath, "w", encoding="utf-8")
    
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = DualStream(f, original_stdout)
    sys.stderr = DualStream(f, original_stderr)
    
    try:
        yield log_filepath
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        f.close()
        print(f"[SYSTEM] Finalizado registro de logs físicos.")

# Función SMTP para notificaciones por email asíncronas
def send_audit_email(action_name: str, log_slice: list):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import re
    import config

    if not config.EMAIL_DESTINATARIOS:
        print("[SMTP] No hay destinatarios definidos en EMAIL_DESTINATARIOS. Se cancela el envío.")
        return

    destinatarios = [email.strip() for email in config.EMAIL_DESTINATARIOS.split(",") if email.strip()]
    if not destinatarios:
        return

    print(f"[SMTP] Preparando envío de reporte de auditoría a {len(destinatarios)} destinatarios...")
    try:
        # Calcular estadísticas de esta corrida
        stats = {
            "escaneados": 0,
            "exitosos_ia": 0,
            "fallidos_ia": 0,
            "bd_actualizados": 0,
            "bd_no_encontrados": 0
        }

        for line in log_slice:
            if "guardada en:" in line or "guardada directamente" in line or "procesada y guardada" in line:
                stats["escaneados"] += 1
            if "Procesado exitosamente" in line:
                stats["exitosos_ia"] += 1
            if "Error durante el análisis" in line or "Excepción en procesamiento" in line:
                stats["fallidos_ia"] += 1
            if "Base de Datos actualizada con éxito" in line or "✔ [BD]" in line:
                stats["bd_actualizados"] += 1
            if "No se encontró ningún registro" in line or "❌ No se encontró en DB" in line:
                stats["bd_no_encontrados"] += 1

        # Intentar leer total de páginas por regex
        scan_text = "\n".join(log_slice)
        scan_match = re.search(r"Total de páginas escaneadas:\s*(\d+)", scan_text, re.IGNORECASE)
        if scan_match:
            stats["escaneados"] = int(scan_match.group(1))

        # Asunto y Cuerpo HTML
        subject = f"🔔 Resumen de Auditoría de Remitos: {action_name}"
        # Limitar las líneas del log en el correo para evitar demoras/bloqueos SMTP
        if len(log_slice) > 100:
            recortado = log_slice[:45] + ["<strong style='color:#ef4444;'>[ ... LOG TRUNCADO POR TAMAÑO (Mostrando primeras y últimas 45 líneas) ... ]</strong>"] + log_slice[-45:]
            logs_html = "<br>".join(recortado)
        else:
            logs_html = "<br>".join(log_slice)

        html = f"""
        <html>
        <head>
          <style>
            body {{ font-family: Arial, sans-serif; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
            .header {{ background-color: #0d2c5c; color: white; padding: 15px; text-align: center; border-radius: 6px 6px 0 0; }}
            .content {{ padding: 20px; }}
            .stats-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            .stats-table td, .stats-table th {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
            .stats-table th {{ background-color: #f8fafc; }}
            .value {{ text-align: right; font-weight: bold; }}
            .footer {{ font-size: 11px; color: #777; text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee; }}
            .logs-box {{ background-color: #f4f6f8; padding: 15px; border-radius: 6px; font-family: monospace; font-size: 11px; max-height: 250px; overflow-y: auto; border: 1px solid #e2e8f0; line-height: 1.4; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h2 style="margin: 0;">Don Yeyo S.A.</h2>
              <p style="margin: 0; font-size: 12px; color: #cbd5e1;">Control y Auditoría de Remitos Firmados</p>
            </div>
            <div class="content">
              <p>Hola,</p>
              <p>Se ha completado la ejecución de <strong>{action_name}</strong> desde el sistema. A continuación, el resumen de resultados:</p>
              
              <table class="stats-table">
                <tr>
                  <th>Métrica</th>
                  <th style="text-align: right;">Cantidad</th>
                </tr>
                <tr>
                  <td>Páginas escaneadas físicamente</td>
                  <td class="value">{stats["escaneados"]}</td>
                </tr>
                <tr>
                  <td>Remitos interpretados por IA (OK)</td>
                  <td class="value" style="color: #10b981;">{stats["exitosos_ia"]}</td>
                </tr>
                {f'<tr><td style="color: #ef4444;">Análisis de IA fallidos</td><td class="value" style="color: #ef4444;">{stats["fallidos_ia"]}</td></tr>' if stats["fallidos_ia"] > 0 else ''}
                <tr>
                  <td>Auditorías registradas en Base de Datos</td>
                  <td class="value" style="color: #0d2c5c;">{stats["bd_actualizados"]}</td>
                </tr>
                {f'<tr><td style="color: #f59e0b;">No encontrados en BD (Sin ERP)</td><td class="value" style="color: #f59e0b;">{stats["bd_no_encontrados"]}</td></tr>' if stats["bd_no_encontrados"] > 0 else ''}
              </table>

              <div style="margin-top: 25px;">
                <strong>Logs de Eventos Generados:</strong>
                <div class="logs-box">{logs_html}</div>
              </div>
            </div>
            <div class="footer">
              Este es un correo automático generado por el sistema de Firma de Remitos Don Yeyo S.A.<br>
              Servidor local: {config.ALERTA_SMTP_NAME}
            </div>
          </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f'"{config.ALERTA_SMTP_NAME}" <{config.ALERTA_SMTP_USER}>'
        msg["To"] = ", ".join(destinatarios)
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(config.ALERTA_SMTP_HOST, config.ALERTA_SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(config.ALERTA_SMTP_USER, config.ALERTA_SMTP_PASSWORD)
            server.sendmail(config.ALERTA_SMTP_USER, destinatarios, msg.as_string())
        print(f"[SMTP] Resumen de auditoría enviado silenciosamente por email a: {', '.join(destinatarios)}")
    except Exception as e:
        print(f"[SMTP ERROR] Falló el envío de notificaciones por email: {e}")

def run_email_async(action_name: str, log_slice: list):
    threading.Thread(target=send_audit_email, args=(action_name, log_slice), daemon=True).start()

# Estado global y candado
process_lock = threading.Lock()

@app.get("/api/status")
def get_status():
    """Devuelve el estado del proceso en ejecución, progreso y resultados finales."""
    return state.get_state()

@app.post("/api/cancel")
async def cancel_process():
    """Solicita la cancelación del proceso activo. Si ya fue solicitada, fuerza el estado a idle para destrabar."""
    current_state = state.get_state()
    if current_state["status"] == "idle":
        return {"status": "error", "message": "No hay ningún proceso activo corriendo."}
        
    if current_state["cancel_requested"]:
        # Segunda solicitud: forzar el destrabe de hilos colgados en el SO
        state.set_idle({
            "success": False,
            "cancelled": True,
            "type": current_state["status"],
            "message": "Proceso forzado a detenerse por el usuario (destrabe de hardware/red).",
            "summary": {}
        })
        print(f"[SYSTEM] Servidor forzado a reposo (idle) de forma manual por el usuario.")
        return {"status": "forced_idle", "message": "Servidor desbloqueado y forzado a reposo."}
    else:
        # Primera solicitud
        state.request_cancel()
        return {"status": "success", "message": "Petición de cancelación enviada de forma limpia."}

def run_action_in_thread(action_name: str, status_type: str, logic_func, action_id: str):
    """Ejecuta una función de negocio en un hilo con log físico y control de excepciones/cancelación."""
    def target():
        last_result = None
        log_filepath = None
        try:
            # 1. Iniciar log físico
            with action_logging(action_name) as filepath:
                log_filepath = filepath
                try:
                    # 2. Ejecutar lógica
                    res_metrics = logic_func()
                    
                    # 3. Registrar éxito
                    last_result = {
                        "success": True,
                        "cancelled": False,
                        "type": status_type,
                        "action_id": action_id,
                        "summary": res_metrics or {}
                    }
                    print(f"[SYSTEM] Proceso '{action_name}' finalizado con éxito.")
                    
                except state.ProcessCancelledException as ce:
                    # 4. Registrar cancelación
                    last_result = {
                        "success": False,
                        "cancelled": True,
                        "type": status_type,
                        "action_id": action_id,
                        "message": "Proceso cancelado voluntariamente por el usuario.",
                        "summary": {}
                    }
                    print(f"[SYSTEM] Proceso '{action_name}' cancelado de forma limpia: {ce}")
                    
                except Exception as e:
                    # 5. Registrar error
                    last_result = {
                        "success": False,
                        "cancelled": False,
                        "type": status_type,
                        "action_id": action_id,
                        "message": str(e),
                        "summary": {}
                    }
                    print(f"[SYSTEM ERROR] Excepción en '{action_name}': {e}")
                    
                finally:
                    # Actualizar progreso a fase final antes de liberar el hilo
                    state.update_progress("Volcando datos y preparando resumen...", 98, 100)
                    time.sleep(1.0)
                    state.update_progress("Enviando reporte de auditoría por email...", 99, 100)
                    time.sleep(1.5)
                    
                    # 6. Devolver a idle y setear resultados si el ID de acción coincide
                    state.set_idle(last_result, action_id)
        except Exception as log_err:
            print(f"[SYSTEM ERROR] Error en el gestor de log de la acción: {log_err}")
            
        # 7. Mandar email de auditoría leyendo el log físico (con el archivo de log ya CERRADO)
        if log_filepath and os.path.exists(log_filepath):
            try:
                with open(log_filepath, "r", encoding="utf-8") as lf:
                    log_lines = lf.readlines()
                run_email_async(action_name, [line.strip() for line in log_lines])
            except Exception as mail_err:
                print(f"[SMTP ERROR] No se pudo enviar el email de auditoría: {mail_err}")
                    
    threading.Thread(target=target, daemon=True).start()

@app.post("/api/scan")
def start_scan():
    """Dispara el proceso de escaneo masivo (Paso 1)."""
    global process_lock
    with process_lock:
        current_state = state.get_state()
        if current_state["status"] != "idle":
            return {"status": "error", "message": f"Servidor ocupado. Proceso actual: {current_state['status']}"}
        action_id = state.reset_state("scanning")
        
    def do_scan():
        import scanner
        scanned = scanner.trigger_scan()
        return {
            "escaneados": len(scanned),
            "exitosasIa": 0,
            "fallidosIa": 0,
            "bdActualizados": 0,
            "bdNoEncontrados": 0
        }
        
    run_action_in_thread("Escaneo_Masivo_Paso_1", "scanning", do_scan, action_id)
    return {"status": "started", "action_id": action_id, "message": "Proceso de escaneo masivo iniciado."}

@app.post("/api/process")
def start_process():
    """Dispara el proceso de análisis por IA (Paso 2)."""
    global process_lock
    with process_lock:
        current_state = state.get_state()
        if current_state["status"] != "idle":
            return {"status": "error", "message": f"Servidor ocupado. Proceso actual: {current_state['status']}"}
        action_id = state.reset_state("processing")
        
    def do_process():
        import recognition
        processor = recognition.DocumentProcessor()
        return processor.process_all_scans()
        
    run_action_in_thread("Procesamiento_IA_Paso_2", "processing", do_process, action_id)
    return {"status": "started", "action_id": action_id, "message": "Proceso de análisis por IA iniciado."}

@app.post("/api/scan-and-process")
def start_scan_and_process():
    """Dispara el proceso unificado: Escaneo + Procesamiento IA."""
    global process_lock
    with process_lock:
        current_state = state.get_state()
        if current_state["status"] != "idle":
            return {"status": "error", "message": f"Servidor ocupado. Proceso actual: {current_state['status']}"}
        action_id = state.reset_state("scanning-and-processing")
        
    def do_full_flow():
        import scanner
        import recognition
        # Paso 1: Escanear
        print("Iniciando Paso 1: Escaneo...")
        scanned_files = scanner.trigger_scan()
        if not scanned_files:
            print("[WARN] El escaneo no generó archivos. Se cancela el análisis.")
            return {
                "escaneados": 0,
                "exitosasIa": 0,
                "fallidosIa": 0,
                "bdActualizados": 0,
                "bdNoEncontrados": 0
            }
            
        # Verificar cancelación entre pasos
        if state.is_cancel_requested():
            raise state.ProcessCancelledException("Cancelado por el usuario entre el escaneo y el procesamiento.")
            
        # Paso 2: Procesar
        print(f"\n[OK] Paso 1 finalizado: {len(scanned_files)} páginas escaneadas. Iniciando Paso 2...")
        processor = recognition.DocumentProcessor()
        res = processor.process_all_scans()
        res["escaneados"] = len(scanned_files)
        return res
        
    run_action_in_thread("Flujo_Completo_Escaneo_e_IA", "scanning-and-processing", do_full_flow, action_id)
    return {"status": "started", "action_id": action_id, "message": "Flujo completo (Escaneo + IA) iniciado."}

@app.post("/api/sync-finnegans")
def start_sync():
    """Dispara la sincronización con el ERP Finnegans."""
    global process_lock
    with process_lock:
        current_state = state.get_state()
        if current_state["status"] != "idle":
            return {"status": "error", "message": f"Servidor ocupado. Proceso actual: {current_state['status']}"}
        action_id = state.reset_state("syncing")
        
    def do_sync():
        import sync_remitos
        hoy = datetime.now()
        try:
            days_back = int(os.getenv("SYNC_DAYS_BACK", "7"))
        except ValueError:
            days_back = 7
        fecha_hasta = hoy.strftime("%Y-%m-%d")
        fecha_desde = (hoy - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        metrics = sync_remitos.sync_remitos(fecha_desde, fecha_hasta)
        return {
            "escaneados": 0,
            "exitosasIa": 0,
            "fallidosIa": 0,
            "bdActualizados": metrics.get("nuevos", 0) + metrics.get("actualizados", 0),
            "bdNoEncontrados": metrics.get("ignorados", 0),
            "erp_encontrados": metrics.get("encontrados", 0),
            "erp_nuevos": metrics.get("nuevos", 0),
            "erp_actualizados": metrics.get("actualizados", 0)
        }
        
    run_action_in_thread("Sincronizacion_ERP_Finnegans", "syncing", do_sync, action_id)
    return {"status": "started", "action_id": action_id, "message": "Proceso de sincronización con Finnegans iniciado."}


@app.get("/api/history")
def get_history(page: int = 1, limit: int = 20, search: str = None, sort_field: str = None, sort_dir: str = None):
    """Consulta la base de datos de AWS y devuelve el historial paginado de remitos ordenados."""
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
        
        offset = (page - 1) * limit
        items = []
        total_items = 0
        
        # Validar y mapear sort_field y sort_dir de forma segura para prevenir inyección SQL
        allowed_sort_fields = {
            "transaccion_id": "finne_transaccionID",
            "numero": "finne_Comprobante",
            "cliente": "finne_Cliente",
            "fecha": "finne_Fecha",
            "copias": "finne_Copias",
            "confirmado_cliente": "bot_confirmado_cliente",
            "confirmado_distribuidor": "bot_confirmado_distribuidor",
            "reclamado": "finne_Reclamado",
            "fecha_ultimo_reclamo": "finne_FechaUltimoReclamo"
        }
        
        db_sort_field = "id"
        if sort_field in allowed_sort_fields:
            db_sort_field = allowed_sort_fields[sort_field]
            
        db_sort_dir = "DESC"
        if sort_dir and sort_dir.lower() == "asc":
            db_sort_dir = "ASC"
            
        with connection.cursor() as cursor:
            # 1. Obtener cantidad total de registros con/sin filtro de búsqueda
            count_sql = "SELECT COUNT(*) as total FROM remitos"
            params = []
            if search:
                count_sql += " WHERE finne_Comprobante LIKE %s OR finne_Cliente LIKE %s OR finne_transaccionID LIKE %s"
                like_search = f"%{search}%"
                params = [like_search, like_search, like_search]
            
            cursor.execute(count_sql, params)
            total_items = cursor.fetchone()["total"]
            
            # 2. Obtener los registros paginados ordenados de más reciente a más antiguo
            sql = """
                SELECT finne_transaccionID as transaccion_id, finne_Comprobante as numero, 
                       finne_Fecha as fecha, finne_Copias as copias, finne_Cliente as cliente,
                       finne_CodigoCliente as codigo_cliente,
                       bot_confirmado_cliente as confirmado_cliente, 
                       bot_confirmado_distribuidor as confirmado_distribuidor,
                       finne_Reclamado as reclamado, finne_FechaUltimoReclamo as fecha_ultimo_reclamo,
                       ocr_original, ocr_duplicado, ocr_triplicado, ocr_cuatriplcado
                FROM remitos
            """
            if search:
                sql += " WHERE finne_Comprobante LIKE %s OR finne_Cliente LIKE %s OR finne_transaccionID LIKE %s"
            sql += f" ORDER BY {db_sort_field} {db_sort_dir} LIMIT %s OFFSET %s"
            
            query_params = params + [limit, offset]
            cursor.execute(sql, query_params)
            rows = cursor.fetchall()
            
            import json
            def extract_file_path(ocr_field):
                if not ocr_field:
                    return None
                try:
                    parsed = json.loads(ocr_field) if isinstance(ocr_field, str) else ocr_field
                    return parsed.get("archivo")
                except Exception:
                    return None

            for r in rows:
                fecha_reclamo_str = None
                if r["fecha_ultimo_reclamo"]:
                    if isinstance(r["fecha_ultimo_reclamo"], datetime) or hasattr(r["fecha_ultimo_reclamo"], "strftime"):
                        fecha_reclamo_str = r["fecha_ultimo_reclamo"].strftime("%Y-%m-%d")
                    else:
                        fecha_reclamo_str = str(r["fecha_ultimo_reclamo"])
                        
                items.append({
                    "transaccion_id": r["transaccion_id"],
                    "numero": r["numero"] if r["numero"] else "Sin número",
                    "cliente": r["cliente"] if r["cliente"] else "Sin cliente",
                    "fecha": r["fecha"].strftime("%Y-%m-%d") if isinstance(r["fecha"], datetime) or hasattr(r["fecha"], "strftime") else str(r["fecha"]),
                    "copias": r["copias"] if r["copias"] is not None else 2,
                    "confirmado_cliente": bool(r["confirmado_cliente"]),
                    "confirmado_distribuidor": bool(r["confirmado_distribuidor"]),
                    "reclamado": bool(r["reclamado"]),
                    "fecha_ultimo_reclamo": fecha_reclamo_str,
                    "copias_escaneadas": {
                        "original": bool(r["ocr_original"]),
                        "original_archivo": extract_file_path(r["ocr_original"]),
                        "duplicado": bool(r["ocr_duplicado"]),
                        "duplicado_archivo": extract_file_path(r["ocr_duplicado"]),
                        "triplicado": bool(r["ocr_triplicado"]),
                        "triplicado_archivo": extract_file_path(r["ocr_triplicado"]),
                        "cuatriplicado": bool(r["ocr_cuatriplcado"]),
                        "cuatriplicado_archivo": extract_file_path(r["ocr_cuatriplcado"])
                    }
                })
        connection.close()
        
        import math
        total_pages = math.ceil(total_items / limit) if total_items > 0 else 1
        
        return {
            "items": items,
            "total": total_items,
            "page": page,
            "pages": total_pages
        }
    except Exception as e:
        print(f"[API ERROR] Error leyendo historial SQL: {e}")
        return {
            "items": [],
            "total": 0,
            "page": page,
            "pages": 1
        }

from pydantic import BaseModel
from typing import List
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_cliente_emails(codigo_cliente: str) -> str:
    if not codigo_cliente:
        return ""
    try:
        from sync_remitos import FinnegansAPI
        api = FinnegansAPI()
        token = api._get_access_token()
        
        # Obtener URL base
        base_url = api.reports_url.split('/reports')[0]
        url = f"{base_url}/cliente/{codigo_cliente}"
        
        print(f"[SMTP API] Consultando emails del cliente {codigo_cliente} en Finnegans: {url}...")
        resp = requests.get(url, params={"ACCESS_TOKEN": token}, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            email_val = data.get("Email", "") or ""
            # Reemplazar puntos y comas por comas y limpiar espacios
            email_val = email_val.replace(";", ",").strip()
            print(f"[SMTP API] Emails encontrados para cliente {codigo_cliente}: {email_val}")
            return email_val
        else:
            print(f"[SMTP API WARNING] Código respuesta Finnegans {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[SMTP API ERROR] No se pudo obtener emails del cliente {codigo_cliente} desde Finnegans: {e}")
    return ""

class PrepareReclaimsPayload(BaseModel):
    transaccion_ids: List[int]

@app.post("/api/prepare-reclaims")
def prepare_reclaims(payload: PrepareReclaimsPayload):
    tx_ids = payload.transaccion_ids
    if not tx_ids:
        return {"status": "error", "message": "No se proporcionaron IDs de transacción."}
        
    connection = pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with connection.cursor() as cursor:
            format_strings = ','.join(['%s'] * len(tx_ids))
            sql = f"""
                SELECT finne_transaccionID, finne_Fecha, finne_CodigoCliente, 
                       finne_Cliente, finne_importe_total, finne_Descripcion, finne_Comprobante
                FROM remitos
                WHERE finne_transaccionID IN ({format_strings})
            """
            cursor.execute(sql, tx_ids)
            remitos = cursor.fetchall()
            
        if not remitos:
            return {"status": "error", "message": "No se encontraron los remitos seleccionados en la base de datos."}
            
        # 1. Leer plantilla base
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        template_path = os.path.join(template_dir, "reclamo_template.html")
        
        os.makedirs(template_dir, exist_ok=True)
        template_content = ""
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as tf:
                template_content = tf.read()
                
        if not template_content:
            template_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; background-color: #f8fafc; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .header { background-color: #0d2c5c; color: white; padding: 24px; text-align: center; }
        .header h2 { margin: 0; font-size: 24px; letter-spacing: 0.5px; }
        .header p { margin: 4px 0 0 0; color: #cbd5e1; font-size: 13px; }
        .content { padding: 32px; line-height: 1.6; }
        .greeting { font-size: 16px; font-weight: 600; color: #0d2c5c; margin-bottom: 16px; }
        .table-info { width: 100%; border-collapse: collapse; margin: 24px 0; }
        .table-info td { padding: 12px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }
        .table-info td.label { font-weight: 600; color: #475569; width: 150px; }
        .table-info td.value { color: #0f172a; }
        .alert-box { background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 4px; margin-bottom: 24px; font-size: 14px; color: #78350f; }
        .footer { background-color: #f8fafc; padding: 16px; text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Don Yeyo S.A.</h2>
            <p>Departamento de Control y Logística de Remitos</p>
        </div>
        <div class="content">
            <div class="greeting">Estimado Cliente,</div>
            <p>Le escribimos para solicitar la firma y devolución del remito correspondiente a la entrega detallada a continuación. Al momento, no registramos la firma de recepción de este comprobante en nuestro sistema de auditoría.</p>
            
            <table class="table-info">
                <tr>
                    <td class="label">Cliente:</td>
                    <td class="value">{{CLIENTE}} (Código: {{CODIGO_CLIENTE}})</td>
                </tr>
                <tr>
                    <td class="label">Nro Remito:</td>
                    <td class="value"><strong>{{NUMERO_REMITO}}</strong></td>
                </tr>
                <tr>
                    <td class="label">Fecha Emisión:</td>
                    <td class="value">{{FECHA}}</td>
                </tr>
                <tr>
                    <td class="label">Transacción ID:</td>
                    <td class="value">{{TRANSACCION_ID}}</td>
                </tr>
                <tr>
                    <td class="label">Descripción:</td>
                    <td class="value">{{DESCRIPCION}}</td>
                </tr>
                <tr>
                    <td class="label">Importe Total:</td>
                    <td class="value">$ {{IMPORTE}}</td>
                </tr>
            </table>

            <div class="alert-box">
                <strong>Importante:</strong> Por favor, si ya procedió con la firma física o digital del duplicado/triplicado de este remito, envíe una copia digitalizada al correo de recepción o responda a este email para regularizar el estado administrativo de su cuenta.
            </div>
            
            <p>Agradecemos desde ya su colaboración para mantener al día nuestros registros de entrega.</p>
        </div>
        <div class="footer">
            Este es un correo automático de control de remitos Don Yeyo S.A.
        </div>
    </div>
</body>
</html>
"""
            
        copias_str = config.EMAIL_DESTINATARIOS or ""
        
        # Diferenciar Envío Único de Envío Masivo (Bulk)
        if len(remitos) == 1:
            r = remitos[0]
            # Obtener emails de Finnegans
            emails_cliente = get_cliente_emails(r["finne_CodigoCliente"])
            
            asunto = f"⚠️ RECLAMO DE FIRMA: Remito Nro {r['finne_Comprobante'] or r['finne_transaccionID']}"
            cuerpo = template_content
            cuerpo = cuerpo.replace("{{CLIENTE}}", str(r["finne_Cliente"] or "Sin Cliente"))
            cuerpo = cuerpo.replace("{{CODIGO_CLIENTE}}", str(r["finne_CodigoCliente"] or "Sin Código"))
            cuerpo = cuerpo.replace("{{NUMERO_REMITO}}", str(r["finne_Comprobante"] or "Sin Número"))
            
            fecha_str = str(r["finne_Fecha"])
            if isinstance(r["finne_Fecha"], datetime) or hasattr(r["finne_Fecha"], "strftime"):
                fecha_str = r["finne_Fecha"].strftime("%Y-%m-%d")
            cuerpo = cuerpo.replace("{{FECHA}}", fecha_str)
            cuerpo = cuerpo.replace("{{TRANSACCION_ID}}", str(r["finne_transaccionID"]))
            cuerpo = cuerpo.replace("{{DESCRIPCION}}", str(r["finne_Descripcion"] or "-"))
            cuerpo = cuerpo.replace("{{IMPORTE}}", f"{float(r['finne_importe_total'] or 0.0):.2f}")
            
            return {
                "status": "success",
                "is_bulk": False,
                "asunto": asunto,
                "destinatarios": emails_cliente,
                "copias": copias_str,
                "cuerpo": cuerpo
            }
        else:
            # Envío Masivo: Retornamos una plantilla genérica con comodines
            asunto = "⚠️ RECLAMO DE FIRMA: Remito Nro {{NUMERO_REMITO}}"
            cuerpo = template_content
            
            return {
                "status": "success",
                "is_bulk": True,
                "asunto": asunto,
                "destinatarios": "{emails_extraidos_del_cliente}",
                "copias": copias_str,
                "cuerpo": cuerpo
            }
            
    except Exception as e:
        print(f"[API ERROR] Error preparando reclamos: {e}")
        return {"status": "error", "message": f"Error al preparar borrador: {e}"}
    finally:
        connection.close()

class SendPreparedReclaimsPayload(BaseModel):
    transaccion_ids: List[int]
    destinatarios: str
    copias: str
    asunto: str
    cuerpo: str
    is_bulk: bool = False

@app.post("/api/send-prepared-reclaims")
def send_prepared_reclaims(payload: SendPreparedReclaimsPayload):
    tx_ids = payload.transaccion_ids
    dest_str = payload.destinatarios
    cc_str = payload.copias
    asunto_base = payload.asunto
    cuerpo_base = payload.cuerpo
    is_bulk = payload.is_bulk or (dest_str == "{emails_extraidos_del_cliente}")
    
    copias = [c.strip() for c in cc_str.split(',') if c.strip()]
    
    connection = pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    
    enviados_ok = 0
    enviados_error = 0
    
    try:
        smtp_server = smtplib.SMTP(config.ALERTA_SMTP_HOST, config.ALERTA_SMTP_PORT, timeout=15)
        smtp_server.starttls()
        smtp_server.login(config.ALERTA_SMTP_USER, config.ALERTA_SMTP_PASSWORD)
    except Exception as conn_err:
        connection.close()
        return {"status": "error", "message": f"Fallo al conectar con el servidor SMTP: {conn_err}"}
        
    try:
        if not is_bulk:
            # 1. Envío único clásico
            destinatarios = [d.strip() for d in dest_str.split(',') if d.strip()]
            if not destinatarios:
                smtp_server.quit()
                connection.close()
                return {"status": "error", "message": "Debe especificar al menos un destinatario principal."}
                
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = asunto_base
                msg["From"] = f'"{config.ALERTA_SMTP_NAME}" <{config.ALERTA_SMTP_USER}>'
                msg["To"] = ", ".join(destinatarios)
                if copias:
                    msg["Cc"] = ", ".join(copias)
                msg.attach(MIMEText(cuerpo_base, "html", "utf-8"))
                
                todos = destinatarios + copias
                smtp_server.sendmail(config.ALERTA_SMTP_USER, todos, msg.as_string())
                
                # Marcar como reclamado
                with connection.cursor() as cursor:
                    sql_update = "UPDATE remitos SET finne_Reclamado = 1, finne_FechaUltimoReclamo = CURRENT_DATE() WHERE finne_transaccionID = %s"
                    cursor.execute(sql_update, (tx_ids[0],))
                connection.commit()
                enviados_ok = 1
            except Exception as e:
                print(f"[SMTP ERROR] Falló envío único: {e}")
                enviados_error = 1
        else:
            # 2. Envío masivo iterativo resolviendo emails y reemplazando comodines
            with connection.cursor() as cursor:
                format_strings = ','.join(['%s'] * len(tx_ids))
                sql = f"""
                    SELECT finne_transaccionID, finne_Fecha, finne_CodigoCliente, 
                           finne_Cliente, finne_importe_total, finne_Descripcion, finne_Comprobante
                    FROM remitos
                    WHERE finne_transaccionID IN ({format_strings})
                """
                cursor.execute(sql, tx_ids)
                remitos = cursor.fetchall()
                
            for r in remitos:
                try:
                    # Resolver emails del cliente
                    emails_cliente = get_cliente_emails(r["finne_CodigoCliente"])
                    destinatarios = [d.strip() for d in emails_cliente.split(',') if d.strip()]
                    
                    if not destinatarios:
                        print(f"[SMTP WARNING] Saltando TransaccionID {r['finne_transaccionID']} porque el cliente {r['finne_CodigoCliente']} no tiene emails en Finnegans.")
                        enviados_error += 1
                        continue
                        
                    # Reemplazar comodines en Asunto y Cuerpo
                    asunto = asunto_base
                    cuerpo = cuerpo_base
                    
                    asunto = asunto.replace("{{NUMERO_REMITO}}", str(r["finne_Comprobante"] or r["finne_transaccionID"]))
                    
                    cuerpo = cuerpo.replace("{{CLIENTE}}", str(r["finne_Cliente"] or "Sin Cliente"))
                    cuerpo = cuerpo.replace("{{CODIGO_CLIENTE}}", str(r["finne_CodigoCliente"] or "Sin Código"))
                    cuerpo = cuerpo.replace("{{NUMERO_REMITO}}", str(r["finne_Comprobante"] or "Sin Número"))
                    
                    fecha_str = str(r["finne_Fecha"])
                    if isinstance(r["finne_Fecha"], datetime) or hasattr(r["finne_Fecha"], "strftime"):
                        fecha_str = r["finne_Fecha"].strftime("%Y-%m-%d")
                    cuerpo = cuerpo.replace("{{FECHA}}", fecha_str)
                    cuerpo = cuerpo.replace("{{TRANSACCION_ID}}", str(r["finne_transaccionID"]))
                    cuerpo = cuerpo.replace("{{DESCRIPCION}}", str(r["finne_Descripcion"] or "-"))
                    cuerpo = cuerpo.replace("{{IMPORTE}}", f"{float(r['finne_importe_total'] or 0.0):.2f}")
                    
                    # Armar y enviar email
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = asunto
                    msg["From"] = f'"{config.ALERTA_SMTP_NAME}" <{config.ALERTA_SMTP_USER}>'
                    msg["To"] = ", ".join(destinatarios)
                    if copias:
                        msg["Cc"] = ", ".join(copias)
                    msg.attach(MIMEText(cuerpo, "html", "utf-8"))
                    
                    todos = destinatarios + copias
                    smtp_server.sendmail(config.ALERTA_SMTP_USER, todos, msg.as_string())
                    
                    # Marcar como reclamado en la base de datos
                    with connection.cursor() as cursor:
                        sql_update = "UPDATE remitos SET finne_Reclamado = 1, finne_FechaUltimoReclamo = CURRENT_DATE() WHERE finne_transaccionID = %s"
                        cursor.execute(sql_update, (r["finne_transaccionID"],))
                    connection.commit()
                    enviados_ok += 1
                except Exception as remito_err:
                    print(f"[SMTP ERROR] Error procesando reclamo masivo para TransaccionID {r['finne_transaccionID']}: {remito_err}")
                    enviados_error += 1
                    
        try:
            smtp_server.quit()
        except Exception:
            pass
            
        return {
            "status": "success",
            "message": f"Envío completado. Exitosos: {enviados_ok}, Omitidos/Errores: {enviados_error}",
            "enviados_ok": enviados_ok,
            "enviados_error": enviados_error
        }
    except Exception as e:
        print(f"[SMTP GENERAL ERROR] {e}")
        return {"status": "error", "message": f"Error general en envío SMTP: {e}"}
    finally:
        connection.close()

@app.post("/api/reclamos")
def send_reclamos(payload: dict):
    """Envía correos electrónicos de reclamo de remitos por SMTP y actualiza su estado en la base de datos."""
    import config
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    tx_ids = payload.get("transaccion_ids", [])
    if not tx_ids:
        return {"status": "error", "message": "No se proporcionaron transacciones para reclamar."}
        
    if not config.EMAIL_DESTINATARIOS:
        return {"status": "error", "message": "No hay destinatarios configurados en EMAIL_DESTINATARIOS."}
        
    destinatarios = [email.strip() for email in config.EMAIL_DESTINATARIOS.split(",") if email.strip()]
    if not destinatarios:
        return {"status": "error", "message": "Lista de destinatarios configurados vacía."}
        
    # 1. Cargar la plantilla HTML
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
    template_path = os.path.join(template_dir, "reclamo_template.html")
    
    os.makedirs(template_dir, exist_ok=True)
    if not os.path.exists(template_path):
        default_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; background-color: #f8fafc; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .header { background-color: #0d2c5c; color: white; padding: 24px; text-align: center; }
        .header h2 { margin: 0; font-size: 24px; letter-spacing: 0.5px; }
        .header p { margin: 4px 0 0 0; color: #cbd5e1; font-size: 13px; }
        .content { padding: 32px; line-height: 1.6; }
        .greeting { font-size: 16px; font-weight: 600; color: #0d2c5c; margin-bottom: 16px; }
        .table-info { width: 100%; border-collapse: collapse; margin: 24px 0; }
        .table-info td { padding: 12px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }
        .table-info td.label { font-weight: 600; color: #475569; width: 150px; }
        .table-info td.value { color: #0f172a; }
        .alert-box { background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 4px; margin-bottom: 24px; font-size: 14px; color: #78350f; }
        .footer { background-color: #f8fafc; padding: 16px; text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Don Yeyo S.A.</h2>
            <p>Departamento de Control y Logística de Remitos</p>
        </div>
        <div class="content">
            <div class="greeting">Estimado Cliente,</div>
            <p>Le escribimos para solicitar la firma y devolución del remito correspondiente a la entrega detallada a continuación. Al momento, no registramos la firma de recepción de este comprobante en nuestro sistema de auditoría.</p>
            
            <table class="table-info">
                <tr>
                    <td class="label">Cliente:</td>
                    <td class="value">{{CLIENTE}} (Código: {{CODIGO_CLIENTE}})</td>
                </tr>
                <tr>
                    <td class="label">Nro Remito:</td>
                    <td class="value"><strong>{{NUMERO_REMITO}}</strong></td>
                </tr>
                <tr>
                    <td class="label">Fecha Emisión:</td>
                    <td class="value">{{FECHA}}</td>
                </tr>
                <tr>
                    <td class="label">Transacción ID:</td>
                    <td class="value">{{TRANSACCION_ID}}</td>
                </tr>
                <tr>
                    <td class="label">Descripción:</td>
                    <td class="value">{{DESCRIPCION}}</td>
                </tr>
                <tr>
                    <td class="label">Importe Total:</td>
                    <td class="value">$ {{IMPORTE}}</td>
                </tr>
            </table>

            <div class="alert-box">
                <strong>Importante:</strong> Por favor, si ya procedió con la firma física o digital del duplicado/triplicado de este remito, envíe una copia digitalizada al correo de recepción o responda a este email para regularizar el estado administrativo de su cuenta.
            </div>
            
            <p>Agradecemos desde ya su colaboración para mantener al día nuestros registros de entrega.</p>
        </div>
        <div class="footer">
            Este es un correo automático de control de remitos Don Yeyo S.A.
        </div>
    </div>
</body>
</html>
"""
        with open(template_path, "w", encoding="utf-8") as tf:
            tf.write(default_html)
            
    with open(template_path, "r", encoding="utf-8") as tf:
        template_content = tf.read()
        
    # 2. Conectarse a la BD para leer los remitos
    connection = pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    
    enviados_ok = 0
    enviados_error = 0
    
    try:
        with connection.cursor() as cursor:
            format_strings = ','.join(['%s'] * len(tx_ids))
            sql = f"""
                SELECT finne_transaccionID, finne_Fecha, finne_CodigoCliente, 
                       finne_Cliente, finne_importe_total, finne_Descripcion, finne_Comprobante
                FROM remitos
                WHERE finne_transaccionID IN ({format_strings})
            """
            cursor.execute(sql, tx_ids)
            remitos = cursor.fetchall()
            
            try:
                smtp_server = smtplib.SMTP(config.ALERTA_SMTP_HOST, config.ALERTA_SMTP_PORT, timeout=12)
                smtp_server.starttls()
                smtp_server.login(config.ALERTA_SMTP_USER, config.ALERTA_SMTP_PASSWORD)
            except Exception as conn_err:
                connection.close()
                return {"status": "error", "message": f"Fallo al conectar con el servidor SMTP: {conn_err}"}
                
            for remito in remitos:
                try:
                    html_cuerpo = template_content
                    html_cuerpo = html_cuerpo.replace("{{CLIENTE}}", str(remito["finne_Cliente"] or "Sin Cliente"))
                    html_cuerpo = html_cuerpo.replace("{{CODIGO_CLIENTE}}", str(remito["finne_CodigoCliente"] or "Sin Código"))
                    html_cuerpo = html_cuerpo.replace("{{NUMERO_REMITO}}", str(remito["finne_Comprobante"] or "Sin Número"))
                    
                    fecha_str = str(remito["finne_Fecha"])
                    if isinstance(remito["finne_Fecha"], datetime) or hasattr(remito["finne_Fecha"], "strftime"):
                        fecha_str = remito["finne_Fecha"].strftime("%Y-%m-%d")
                    html_cuerpo = html_cuerpo.replace("{{FECHA}}", fecha_str)
                    
                    html_cuerpo = html_cuerpo.replace("{{TRANSACCION_ID}}", str(remito["finne_transaccionID"]))
                    html_cuerpo = html_cuerpo.replace("{{DESCRIPCION}}", str(remito["finne_Descripcion"] or "-"))
                    html_cuerpo = html_cuerpo.replace("{{IMPORTE}}", f"{float(remito['finne_importe_total'] or 0.0):.2f}")
                    
                    subject = f"⚠️ RECLAMO DE FIRMA: Remito Nro {remito['finne_Comprobante'] or remito['finne_transaccionID']}"
                    
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = subject
                    msg["From"] = f'"{config.ALERTA_SMTP_NAME}" <{config.ALERTA_SMTP_USER}>'
                    msg["To"] = ", ".join(destinatarios)
                    msg.attach(MIMEText(html_cuerpo, "html", "utf-8"))
                    
                    smtp_server.sendmail(config.ALERTA_SMTP_USER, destinatarios, msg.as_string())
                    
                    update_sql = """
                        UPDATE remitos
                        SET finne_Reclamado = 1,
                            finne_FechaUltimoReclamo = CURRENT_DATE()
                        WHERE finne_transaccionID = %s
                    """
                    cursor.execute(update_sql, (remito["finne_transaccionID"],))
                    connection.commit()
                    enviados_ok += 1
                except Exception as remito_err:
                    print(f"Error procesando envío de reclamo para TransaccionID {remito['finne_transaccionID']}: {remito_err}")
                    enviados_error += 1
            
            try:
                smtp_server.quit()
            except Exception:
                pass
                
    except Exception as e:
        print(f"Error general en endpoint reclamos: {e}")
        return {"status": "error", "message": f"Error general en BD: {e}"}
    finally:
        connection.close()
        
    return {
        "status": "success",
        "message": f"Proceso de reclamo completado. Exitosos: {enviados_ok}, Errores: {enviados_error}",
        "enviados_ok": enviados_ok,
        "enviados_error": enviados_error
    }


@app.get("/api/stats")
def get_dashboard_stats():
    """Calcula y devuelve métricas consolidadas para el Dashboard de estadísticas."""
    connection = pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with connection.cursor() as cursor:
            # 1. Total remitos
            cursor.execute("SELECT COUNT(*) as total FROM remitos")
            total = cursor.fetchone()["total"] or 0
            
            # 2. Confirmados Cliente (Firma OL)
            cursor.execute("SELECT COUNT(*) as cliente_ok FROM remitos WHERE bot_confirmado_cliente = 1")
            cliente_ok = cursor.fetchone()["cliente_ok"] or 0
            
            # 3. Confirmados Distribuidor
            cursor.execute("SELECT COUNT(*) as dist_ok FROM remitos WHERE bot_confirmado_distribuidor = 1")
            dist_ok = cursor.fetchone()["dist_ok"] or 0
            
            # 4. Ambos OK (Auditados Completamente)
            cursor.execute("SELECT COUNT(*) as ambos_ok FROM remitos WHERE bot_confirmado_cliente = 1 AND bot_confirmado_distribuidor = 1")
            ambos_ok = cursor.fetchone()["ambos_ok"] or 0
            
            # 5. Reclamados
            cursor.execute("SELECT COUNT(*) as reclamados FROM remitos WHERE finne_Reclamado = 1")
            reclamados = cursor.fetchone()["reclamados"] or 0
            
            # 6. Recuento de Ejemplares Escaneados (Original, Duplicado, Triplicado, Cuatriplicado)
            cursor.execute("SELECT COUNT(*) as orig FROM remitos WHERE ocr_original IS NOT NULL")
            orig = cursor.fetchone()["orig"] or 0
            
            cursor.execute("SELECT COUNT(*) as dup FROM remitos WHERE ocr_duplicado IS NOT NULL")
            dup = cursor.fetchone()["dup"] or 0
            
            cursor.execute("SELECT COUNT(*) as trip FROM remitos WHERE ocr_triplicado IS NOT NULL")
            trip = cursor.fetchone()["trip"] or 0
            
            cursor.execute("SELECT COUNT(*) as cuat FROM remitos WHERE ocr_cuatriplcado IS NOT NULL")
            cuat = cursor.fetchone()["cuat"] or 0
            
            # 7. Remitos con al menos una copia escaneada (Tasa de digitalización)
            cursor.execute("""
                SELECT COUNT(*) as con_copias 
                FROM remitos 
                WHERE ocr_original IS NOT NULL 
                   OR ocr_duplicado IS NOT NULL 
                   OR ocr_triplicado IS NOT NULL 
                   OR ocr_cuatriplcado IS NOT NULL
            """)
            con_copias = cursor.fetchone()["con_copias"] or 0
            
            # 8. Top 10 deudores de firmas agrupado por los primeros 30 caracteres de la razón social
            deudores_sql = """
                SELECT LEFT(finne_Cliente, 30) as cliente_grupo, COUNT(*) as deudas
                FROM remitos
                WHERE (finne_Copias = 2 AND COALESCE(bot_confirmado_distribuidor, 0) = 0)
                   OR (finne_Copias > 2 AND (COALESCE(bot_confirmado_cliente, 0) = 0 OR COALESCE(bot_confirmado_distribuidor, 0) = 0))
                   OR (finne_Copias IS NULL AND (COALESCE(bot_confirmado_cliente, 0) = 0 OR COALESCE(bot_confirmado_distribuidor, 0) = 0))
                GROUP BY LEFT(finne_Cliente, 30)
                ORDER BY deudas DESC
                LIMIT 10
            """
            cursor.execute(deudores_sql)
            top_deudores = []
            for row in cursor.fetchall():
                top_deudores.append({
                    "cliente": row["cliente_grupo"] if row["cliente_grupo"] else "Sin cliente",
                    "deuda": row["deudas"] or 0
                })
            
        tasa_digitalizacion = (con_copias / total * 100) if total > 0 else 0.0
        
        return {
            "status": "success",
            "metrics": {
                "total_remitos": total,
                "confirmados_cliente": cliente_ok,
                "confirmados_distribuidor": dist_ok,
                "auditoria_completa": ambos_ok,
                "total_reclamados": reclamados,
                "tasa_digitalizacion": round(tasa_digitalizacion, 1),
                "copias": {
                    "original": orig,
                    "duplicado": dup,
                    "triplicado": trip,
                    "cuatriplicado": cuat
                },
                "top_deudores": top_deudores
            }
        }
    except Exception as e:
        print(f"[API ERROR] Error calculando estadísticas: {e}")
        return {"status": "error", "message": f"Error al consultar estadísticas: {e}"}
    finally:
        connection.close()


@app.put("/api/history/{transaccion_id}")
def update_remito_manual(transaccion_id: int, payload: dict = Body(...)):
    """Actualiza de forma manual la conformidad de firmas, ejemplares y reclamos de un remito."""
    import json
    connection = pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    
    confirmado_cliente = payload.get("confirmado_cliente", False)
    confirmado_distribuidor = payload.get("confirmado_distribuidor", False)
    reclamado = payload.get("reclamado", False)
    
    # Manejar la fecha de último reclamo
    fecha_ultimo_reclamo = payload.get("fecha_ultimo_reclamo")
    if reclamado and not fecha_ultimo_reclamo:
        fecha_ultimo_reclamo = datetime.now().strftime("%Y-%m-%d")
    elif not reclamado:
        fecha_ultimo_reclamo = None
        
    # Ejemplares (Original, Duplicado, Triplicado, Cuatriplicado)
    copias_presentes = payload.get("copias_presentes", {})
    copia_orig_present = copias_presentes.get("original", False)
    copia_dup_present = copias_presentes.get("duplicado", False)
    copia_trip_present = copias_presentes.get("triplicado", False)
    copia_cuat_present = copias_presentes.get("cuatriplicado", False)
    
    try:
        with connection.cursor() as cursor:
            # 1. Recuperar remito actual
            cursor.execute("""
                SELECT ocr_original, ocr_duplicado, ocr_triplicado, ocr_cuatriplcado 
                FROM remitos 
                WHERE finne_transaccionID = %s
            """, (transaccion_id,))
            current = cursor.fetchone()
            if not current:
                return {"status": "error", "message": "No se encontró el remito especificado."}
                
            # Helper para resolver el JSON de ejemplar
            def resolve_ocr_value(is_present, current_json):
                if is_present:
                    if current_json:
                        return current_json
                    # Crear JSON mockup si no existía para poder marcarlo como digitalizado
                    return json.dumps({
                        "firmas": [{"confidence": 100}],
                        "sellos": [],
                        "original_filename": "manual_update.jpg",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "confianza": 100,
                        "archivo": ""
                    }, ensure_ascii=False)
                return None
                
            ocr_orig = resolve_ocr_value(copia_orig_present, current["ocr_original"])
            ocr_dup = resolve_ocr_value(copia_dup_present, current["ocr_duplicado"])
            ocr_trip = resolve_ocr_value(copia_trip_present, current["ocr_triplicado"])
            ocr_cuat = resolve_ocr_value(copia_cuat_present, current["ocr_cuatriplcado"])
            
            # 2. Actualizar base de datos
            update_sql = """
                UPDATE remitos
                SET bot_confirmado_cliente = %s,
                    bot_confirmado_distribuidor = %s,
                    finne_Reclamado = %s,
                    finne_FechaUltimoReclamo = %s,
                    ocr_original = %s,
                    ocr_duplicado = %s,
                    ocr_triplicado = %s,
                    ocr_cuatriplcado = %s
                WHERE finne_transaccionID = %s
            """
            cursor.execute(update_sql, (
                1 if confirmado_cliente else 0,
                1 if confirmado_distribuidor else 0,
                1 if reclamado else 0,
                fecha_ultimo_reclamo,
                ocr_orig, ocr_dup, ocr_trip, ocr_cuat,
                transaccion_id
            ))
            connection.commit()
            
        return {"status": "success", "message": "Remito actualizado manualmente con éxito."}
    except Exception as e:
        print(f"[API ERROR] Error en edición manual de remito: {e}")
        return {"status": "error", "message": f"Error al guardar cambios: {e}"}
    finally:
        connection.close()


@app.post("/api/send-remito-email")
def send_individual_remito_email(payload: dict = Body(...)):
    """Reenvía de forma individual la solicitud de remito adjuntando el archivo escaneado por email."""
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.image import MIMEImage
    import smtplib
    
    transaccion_id = payload.get("transaccion_id")
    archivo_ruta = payload.get("archivo_ruta")
    emails_raw = payload.get("emails", "")
    
    if not transaccion_id or not emails_raw:
        return {"status": "error", "message": "Parámetros 'transaccion_id' y 'emails' requeridos."}
        
    destinatarios = [email.strip() for email in emails_raw.split(",") if email.strip()]
    if not destinatarios:
        return {"status": "error", "message": "No se especificaron direcciones de correo electrónico válidas."}
        
    # Leer plantilla de reclamo
    template_path = os.path.join("server", "templates", "reclamo_template.html")
    if not os.path.exists(template_path):
        template_path = os.path.join("templates", "reclamo_template.html")
        
    template_content = ""
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
    else:
        # Fallback inline
        template_content = "<h2>Firma de Remito Pendiente: {{NUMERO_REMITO}}</h2>"
        
    connection = pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with connection.cursor() as cursor:
            # 1. Recuperar información del remito
            sql = """
                SELECT finne_transaccionID, finne_Fecha, finne_CodigoCliente, 
                       finne_Cliente, finne_importe_total, finne_Descripcion, finne_Comprobante
                FROM remitos
                WHERE finne_transaccionID = %s
            """
            cursor.execute(sql, (transaccion_id,))
            remito = cursor.fetchone()
            if not remito:
                return {"status": "error", "message": "No se encontró el remito especificado en la base de datos."}
                
            # 2. Generar el correo HTML
            html_cuerpo = template_content
            html_cuerpo = html_cuerpo.replace("{{CLIENTE}}", str(remito["finne_Cliente"] or "Sin Cliente"))
            html_cuerpo = html_cuerpo.replace("{{CODIGO_CLIENTE}}", str(remito["finne_CodigoCliente"] or "Sin Código"))
            html_cuerpo = html_cuerpo.replace("{{NUMERO_REMITO}}", str(remito["finne_Comprobante"] or "Sin Número"))
            
            fecha_str = str(remito["finne_Fecha"])
            if isinstance(remito["finne_Fecha"], datetime) or hasattr(remito["finne_Fecha"], "strftime"):
                fecha_str = remito["finne_Fecha"].strftime("%Y-%m-%d")
            html_cuerpo = html_cuerpo.replace("{{FECHA}}", fecha_str)
            
            html_cuerpo = html_cuerpo.replace("{{TRANSACCION_ID}}", str(remito["finne_transaccionID"]))
            html_cuerpo = html_cuerpo.replace("{{DESCRIPCION}}", str(remito["finne_Descripcion"] or "-"))
            html_cuerpo = html_cuerpo.replace("{{IMPORTE}}", f"{float(remito['finne_importe_total'] or 0.0):.2f}")
            
            subject = f"Reenvío de Comprobante: Remito Nro {remito['finne_Comprobante'] or remito['finne_transaccionID']}"
            
            msg = MIMEMultipart("mixed")
            msg["Subject"] = subject
            msg["From"] = f'"{config.ALERTA_SMTP_NAME}" <{config.ALERTA_SMTP_USER}>'
            msg["To"] = ", ".join(destinatarios)
            
            # Copias CC (Auditoría/Control)
            copias_str = config.EMAIL_DESTINATARIOS or ""
            copias = [c.strip() for c in copias_str.split(",") if c.strip()]
            if copias:
                msg["Cc"] = ", ".join(copias)
            
            # Cuerpo HTML
            body_part = MIMEText(html_cuerpo, "html", "utf-8")
            msg.attach(body_part)
            
            # 3. Adjuntar la imagen si existe
            if archivo_ruta:
                full_image_path = os.path.abspath(archivo_ruta)
                if not os.path.exists(full_image_path):
                    full_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), archivo_ruta)
                    
                if os.path.exists(full_image_path):
                    with open(full_image_path, "rb") as img_file:
                        img_data = img_file.read()
                        image_part = MIMEImage(img_data, name=os.path.basename(full_image_path))
                        image_part.add_header('Content-ID', f'<{os.path.basename(full_image_path)}>')
                        image_part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(full_image_path))
                        msg.attach(image_part)
                else:
                    print(f"[SMTP WARNING] Imagen adjunta especificada no encontrada físicamente: {full_image_path}")
            
            # 4. Enviar
            try:
                smtp_server = smtplib.SMTP(config.ALERTA_SMTP_HOST, config.ALERTA_SMTP_PORT, timeout=12)
                smtp_server.starttls()
                smtp_server.login(config.ALERTA_SMTP_USER, config.ALERTA_SMTP_PASSWORD)
                todos = destinatarios + copias
                smtp_server.sendmail(config.ALERTA_SMTP_USER, todos, msg.as_string())
                smtp_server.quit()
            except Exception as smtp_err:
                return {"status": "error", "message": f"Fallo al enviar correo SMTP: {smtp_err}"}
                
            # 5. Marcar como reclamado en la BD
            update_sql = """
                UPDATE remitos
                SET finne_Reclamado = 1,
                    finne_FechaUltimoReclamo = CURRENT_DATE()
                WHERE finne_transaccionID = %s
            """
            cursor.execute(update_sql, (transaccion_id,))
            connection.commit()
            
        return {"status": "success", "message": "Email enviado con éxito al destinatario con la imagen adjunta."}
    except Exception as e:
        print(f"[API ERROR] Error en reenvío individual por email: {e}")
        return {"status": "error", "message": f"Error al procesar el envío: {e}"}
    finally:
        connection.close()


# Montar el frontend React compilado en la raíz si la carpeta 'client/dist' existe
client_dist_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "client", "dist")
if os.path.exists(client_dist_path):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    
    # Montar assets estáticos de React
    assets_path = os.path.join(client_dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
        
    # Ruta catch-all de respaldo para servir index.html (Soporte SPA para recargas del navegador)
    @app.get("/{catchall:path}")
    def serve_client(catchall: str):
        # Si empieza con api/, FastAPI debe tirar un error 404 normal
        if catchall.startswith("api/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="API Endpoint no encontrado")
        return FileResponse(os.path.join(client_dist_path, "index.html"))

if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Determinar si estamos ejecutando desde el código fuente y no desde un ejecutable empaquetado
    is_development = not getattr(sys, "frozen", False)
    
    if is_development:
        # Agregar la carpeta del servidor al path para que uvicorn resuelva "server:app"
        server_dir = os.path.dirname(os.path.abspath(__file__))
        if server_dir not in sys.path:
            sys.path.insert(0, server_dir)
            
        print("[SYSTEM] Iniciando en Modo Desarrollo con Autoreload (Hot Reload) activo...")
        uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=[server_dir])
    else:
        # Iniciar localmente escuchando en todas las interfaces de red de la LAN en el puerto 8000
        uvicorn.run(app, host="0.0.0.0", port=8000)
