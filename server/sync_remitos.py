import os
import sys
import json
import logging
import argparse
import requests
import pymysql
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Cargar configuración centralizada del proyecto
import config

# Configuración de Logging
os.makedirs("logs", exist_ok=True)
log_format = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join("logs", "sync_remitos.log"), encoding="utf-8")
    ]
)
logger = logging.getLogger("SyncRemitos")

class FinnegansAPI:
    """Clase simplificada y robusta para la integración con la API de Finnegans ERP."""
    def __init__(self):
        self.client_id = os.getenv("FINNEGANS_CLIENT_ID")
        self.client_secret = os.getenv("FINNEGANS_CLIENT_SECRET")
        self.empresa_cod = os.getenv("FINNEGANS_EMPRESA_COD", "EMPRE01")
        self.token_url = os.getenv("FINNEGANS_TOKEN_URL", "https://api.teamplace.finneg.com/api/oauth/token")
        
        # URL Base para reportes del ERP
        self.reports_url = os.getenv("FINNEGANS_API_URL", "https://api.teamplace.finneg.com/api/reports")
        self.report_name = os.getenv("FINNEGANS_REMITOS_REPORT_NAME", "AFIRMAREMVEN_MG")
        
        timeout_env = os.getenv("FINNEGANS_HTTP_TIMEOUT", "90")
        try:
            self.timeout = int(timeout_env)
        except ValueError:
            self.timeout = 90
            
        self._access_token = None

    def _get_access_token(self) -> str:
        """Obtiene el token de acceso de Finnegans manejando respuestas JSON o texto plano."""
        if self._access_token:
            return self._access_token
            
        if not self.client_id or not self.client_secret:
            raise ValueError("Faltan credenciales FINNEGANS_CLIENT_ID o FINNEGANS_CLIENT_SECRET en las variables de entorno.")
            
        params = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        logger.debug(f"Solicitando token a Finnegans...")
        try:
            resp = requests.get(self.token_url, params=params, timeout=self.timeout)
            if resp.status_code != 200:
                logger.error(f"Error de autenticación en Finnegans [{resp.status_code}]: {resp.text}")
                resp.raise_for_status()
                
            body_text = resp.text.strip()
            if not body_text:
                raise ValueError("La respuesta de Finnegans para el token de acceso está vacía.")
                
            # Intentar parsear como JSON
            try:
                data = resp.json()
                self._access_token = data.get("access_token")
            except (json.JSONDecodeError, AttributeError):
                self._access_token = None
                
            # Si no vino como JSON, tomar la respuesta directa (texto plano/UUID)
            if not self._access_token:
                if " " not in body_text and len(body_text) > 10:
                    self._access_token = body_text
                else:
                    raise ValueError(f"Formato de token no reconocido: {body_text[:200]}")
                    
            logger.info("Token de acceso de Finnegans obtenido con éxito.")
            return self._access_token
            
        except Exception as e:
            logger.error(f"Falla al conectar con Finnegans para obtener token: {e}")
            raise

    def get_remitos_report(self, fecha_desde: str, fecha_hasta: str) -> List[Dict[str, Any]]:
        """Consulta el reporte de remitos en Finnegans en el rango de fechas especificado."""
        token = self._get_access_token()
        url = f"{self.reports_url}/{self.report_name}"
        
        params = {
            "ACCESS_TOKEN": token,
            "PARAMWEBREPORT_FechaDesde": fecha_desde,
            "PARAMWEBREPORT_FechaHasta": fecha_hasta,
            "PARAMWEBREPORT_Documento": "",
            "PARAMWEBREPORT_Cliente": "",
            "PARAMWEBREPORT_CircuitoContable": "",
            "PARAMWEBREPORT_dimension": "",
            "PARAMWEBREPORT_valor": "",
            "PARAMWEBREPORT_Producto": "",
            "PARAMWEBREPORT_Moneda": "",
            "PARAMWEBREPORT_Empresa": self.empresa_cod,
            "PARAMWEBREPORT_IncluirConceptosCalculados": "false",
            "PARAMWEBREPORT_Firma": ""
        }
        
        logger.info(f"Consultando remitos en Finnegans desde {fecha_desde} hasta {fecha_hasta} (Reporte: {self.report_name})...")
        try:
            resp = requests.get(url, params=params, timeout=self.timeout)
            if resp.status_code == 400 and "invalid token" in resp.text.lower():
                logger.warning("Token expirado o inválido. Reintentando con un nuevo token...")
                self._access_token = None
                token = self._get_access_token()
                params["ACCESS_TOKEN"] = token
                resp = requests.get(url, params=params, timeout=self.timeout)
                
            if resp.status_code != 200:
                logger.error(f"Error al obtener reporte de remitos [{resp.status_code}]: {resp.text[:500]}")
                resp.raise_for_status()
                
            data = resp.json()
            if isinstance(data, list):
                logger.info(f"Se recuperaron {len(data)} registros de remitos desde Finnegans.")
                return data
            else:
                logger.error(f"Respuesta inesperada de Finnegans (se esperaba lista): {resp.text[:500]}")
                return []
                
        except Exception as e:
            logger.error(f"Falla al obtener el reporte de remitos desde Finnegans: {e}")
            raise

def parse_date_to_mysql(date_str: str) -> Optional[str]:
    """Convierte una fecha en formato DD-MM-YYYY a formato YYYY-MM-DD para MySQL."""
    if not date_str:
        return None
    try:
        # Finnegans devuelve las fechas como DD-MM-YYYY
        dt = datetime.strptime(date_str.strip(), "%d-%m-%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        try:
            # Fallback en caso de que venga con barra o en formato ISO
            dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            logger.error(f"No se pudo parsear la fecha de Finnegans: {date_str}")
            return None

def sync_remitos(fecha_desde: str, fecha_hasta: str):
    """Sincroniza los remitos desde la API de Finnegans e inserta/actualiza en MySQL."""
    # 1. Obtener remitos de Finnegans
    try:
        api = FinnegansAPI()
        remitos = api.get_remitos_report(fecha_desde, fecha_hasta)
    except Exception as e:
        logger.critical(f"Abortando sincronización por fallo en la API de Finnegans: {e}")
        sys.exit(1)
        
    if not remitos:
        logger.info("No se encontraron remitos en el rango de fechas consultado.")
        return

    # 2. Conectarse a la base de datos MySQL local
    logger.info(f"Conectándose a la base de datos MySQL en {config.DB_HOST}...")
    try:
        connection = pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor
        )
        logger.info("✔ Conexión establecida con éxito con la base de datos MySQL.")
    except Exception as e:
        logger.critical(f"No se pudo conectar a la base de datos MySQL: {e}")
        sys.exit(1)

    inserted_count = 0
    updated_count = 0
    ignored_count = 0
    
    try:
        with connection.cursor() as cursor:
            # OPTIMIZACIÓN: Consultar de una sola vez los IDs de transacciones de remitos existentes
            # en la base de datos dentro del rango de fechas consultado para evitar 1200 SELECTs secuenciales por red.
            logger.info("Consultando remitos preexistentes en la base de datos...")
            check_all_sql = "SELECT finne_transaccionID FROM remitos WHERE finne_Fecha BETWEEN %s AND %s"
            cursor.execute(check_all_sql, (fecha_desde, fecha_hasta))
            existing_ids = {row["finne_transaccionID"] for row in cursor.fetchall() if row.get("finne_transaccionID")}
            logger.info(f"Se encontraron {len(existing_ids)} remitos ya registrados localmente en este rango de fechas.")
            
            total_to_process = len(remitos)
            logger.info(f"Iniciando procesamiento de los {total_to_process} remitos de Finnegans...")
            
            for index, item in enumerate(remitos, 1):
                transaccion_id = item.get("TRANSACCIONID")
                if not transaccion_id:
                    ignored_count += 1
                    continue
                
                # Mapeo y preparación de variables
                copias = item.get("CANTIDADCOPIAS", 2)
                fecha_raw = item.get("FECHA")
                fecha_db = parse_date_to_mysql(fecha_raw)
                
                try:
                    codigo_cliente = int(item.get("ORGANIZACION_CODIGO") or 0)
                except ValueError:
                    codigo_cliente = 0
                    
                cliente = item.get("CLIENTE", "")[:100]
                importe = item.get("TOTAL", 0.0)
                comprobante = item.get("COMPROBANTE", "")[:30]
                doc_nro_int = item.get("DOCNROINT", "")[:100]
                descripcion = item.get("DESCRIPCION", "")[:255]
                
                # Usar la caché de IDs locales para decidir si es INSERT o UPDATE sin hacer viajes de red
                if transaccion_id in existing_ids:
                    # El registro ya existe. Actualizamos los campos por si hubo modificaciones en el ERP
                    update_sql = """
                        UPDATE remitos 
                        SET finne_Copias = %s,
                            finne_Fecha = %s,
                            finne_CodigoCliente = %s,
                            finne_Cliente = %s,
                            finne_importe_total = %s,
                            finne_Comprobante = %s,
                            finne_DocNroInterno = %s,
                            finne_Descripcion = %s
                        WHERE finne_transaccionID = %s
                    """
                    cursor.execute(update_sql, (
                        copias, fecha_db, codigo_cliente, cliente, 
                        importe, comprobante, doc_nro_int, descripcion, 
                        transaccion_id
                    ))
                    updated_count += 1
                else:
                    # Registro nuevo
                    insert_sql = """
                        INSERT INTO remitos (
                            finne_transaccionID, finne_Copias, finne_Fecha, 
                            finne_CodigoCliente, finne_Cliente, finne_importe_total, 
                            finne_Comprobante, finne_DocNroInterno, finne_Descripcion, 
                            finne_Reclamado, finne_FechaUltimoReclamo, finne_cbte_relacionado
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_sql, (
                        transaccion_id, copias, fecha_db, 
                        codigo_cliente, cliente, importe, 
                        comprobante, doc_nro_int, descripcion, 
                        0, None, None
                    ))
                    # Añadir al set en memoria
                    existing_ids.add(transaccion_id)
                    inserted_count += 1
                
                # Realizar commits parciales y mostrar progreso cada 100 registros para mejorar respuesta y resiliencia
                if index % 100 == 0 or index == total_to_process:
                    connection.commit()
                    logger.info(f" -> Progreso: {index}/{total_to_process} remitos procesados. (Nuevos: {inserted_count}, Actualizados: {updated_count})")
                    
        logger.info(f"Sincronización finalizada con éxito. Resumen:")
        logger.info(f"  - Nuevos insertados: {inserted_count}")
        logger.info(f"  - Existentes actualizados: {updated_count}")
        logger.info(f"  - Omitidos/Ignorados: {ignored_count}")
        
    except Exception as e:
        connection.rollback()
        logger.error(f"Error de base de datos durante la sincronización: {e}")
        sys.exit(1)
    finally:
        connection.close()

def main():
    parser = argparse.ArgumentParser(description="Script de sincronización automática de remitos desde Finnegans ERP a MySQL.")
    parser.add_argument("--desde", help="Fecha inicial de consulta (YYYY-MM-DD).")
    parser.add_argument("--hasta", help="Fecha final de consulta (YYYY-MM-DD).")
    args = parser.parse_args()

    # Si se especifican las fechas por consola, utilizarlas directamente
    if args.desde and args.hasta:
        fecha_desde = args.desde
        fecha_hasta = args.hasta
    else:
        # Calcular ventana temporal de forma automática basándose en SYNC_DAYS_BACK
        try:
            days_back = int(os.getenv("SYNC_DAYS_BACK", "7"))
        except ValueError:
            days_back = 7
            
        hoy = datetime.now()
        fecha_hasta = hoy.strftime("%Y-%m-%d")
        fecha_desde = (hoy - timedelta(days=days_back)).strftime("%Y-%m-%d")

    logger.info("======================================================================")
    logger.info("INICIANDO PROCESO DE SINCRONIZACIÓN DE REMITOS DESDE FINNEGANS")
    logger.info("======================================================================")
    logger.info(f"Rango de búsqueda calculado: Desde {fecha_desde} hasta {fecha_hasta}")
    
    sync_remitos(fecha_desde, fecha_hasta)
    logger.info("Proceso completado exitosamente.\n")

if __name__ == "__main__":
    main()
