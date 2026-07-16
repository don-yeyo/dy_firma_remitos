import os
import json
import csv
import base64
import re
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv


import config

load_dotenv()

# Modelos de Pydantic para forzar la estructura de salida estructurada
class ElementoGraficoFirma(BaseModel):
    emision: str = Field(
        description="Emisor al que pertenece la firma. Valores posibles: 'persona' (para una firma suelta o asociada al sello de una persona física), 'comercio' (para una firma hecha encima o claramente asociada al sello de la institución o comercio)."
    )
    complejidad: str = Field(
        description="Complejidad del trazo de la firma. Valores posibles: 'baja', 'media', 'alta'."
    )
    posicion_x: str = Field(
        description="Posición horizontal de la firma en el remito. Valores posibles: 'izquierda', 'medio', 'derecha'."
    )
    posicion_y: str = Field(
        description="Posición vertical de la firma en el remito. Valores posibles: 'arriba', 'medio', 'abajo'."
    )

class ElementoGraficoSello(BaseModel):
    emision: str = Field(
        description=(
            "Emisor al que pertenece el sello. Valores posibles: "
            "'persona' (para sellos simples de persona física, típicamente de 2 renglones con nombre, apellido y un número), "
            "'comercio' (para sellos de comercio/institución, más elaborados, que incluyan logos, palabras como 'supermercados', 'S.A.', fechas o tengan un tamaño significativamente más grande)."
        )
    )
    complejidad: str = Field(
        description="Complejidad del diseño del sello. Valores posibles: 'baja', 'media', 'alta'."
    )
    posicion_x: str = Field(
        description="Posición horizontal del sello en el remito. Valores posibles: 'izquierda', 'medio', 'derecha'."
    )
    posicion_y: str = Field(
        description="Posición vertical del sello en el remito. Valores posibles: 'arriba', 'medio', 'abajo'."
    )

class ExtractedText(BaseModel):
    transaccion_id: Optional[str] = Field(None, description="Identificador único de la transacción")
    numero_remito: Optional[str] = Field(description="Campo 'Numero' arriba a la derecha (ej. R-0005-00473008)")
    fecha: Optional[str] = Field(description="Campo 'Fecha' arriba a la derecha")
    tipo: Optional[str] = Field(description="Valores posibles: 'ORIGINAL', 'DUPLICADO', 'TRIPLICADO', 'CUATRIPLICADO'")
    cliente_cod: Optional[str] = Field(description="Campo Cód Cliente")
    cliente_desc: Optional[str] = Field(description="Nombre del cliente o Sr. (es)")
    cbte_relacionado: Optional[str] = Field(description="Campo 'Factura Nro'")
    firmas: list[ElementoGraficoFirma] = Field(default_factory=list, description="Lista de todas las firmas manuscritas detectadas en el documento. Puede ser un array vacío si no hay ninguna.")
    sellos: list[ElementoGraficoSello] = Field(default_factory=list, description="Lista de todos los sellos físicos detectados en el documento. Puede ser un array vacío si no hay ninguno.")

class StructuredData(BaseModel):
    extracted_text: ExtractedText


class DocumentProcessor:

    def __init__(self):
        self._ensure_csv_log_exists()
        self.provider = config.AI_PROVIDER
        
        if self.provider == "local_vlm":
            print(f"Inicializando procesador con VLM Local ({config.VLM_MODEL})...")
            try:
                from openai import OpenAI
                self.local_client = OpenAI(
                    base_url=config.VLM_API_URL,
                    api_key=config.VLM_API_KEY
                )
            except Exception as e:
                print(f"Error al inicializar el cliente OpenAI local: {e}")
                self.local_client = None
            self.client = None
        elif self.provider == "powerautomate":
            print("Inicializando procesador con Power Automate Flow...")
            self.local_client = None
            self.client = None
        else:
            # gemini
            self.provider = "gemini"
            print("Inicializando procesador con Google Gemini...")
            self.local_client = None
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key or api_key == "tu_clave_api_aqui":
                print("ADVERTENCIA: GEMINI_API_KEY no está configurada correctamente en el archivo .env")
                self.client = None
            else:
                self.client = genai.Client(api_key=api_key)


    def _ensure_csv_log_exists(self):
        """Asegura que el archivo de log CSV exista con sus cabeceras."""
        if not os.path.exists(config.CSV_LOG_PATH):
            try:
                os.makedirs(os.path.dirname(config.CSV_LOG_PATH), exist_ok=True)
                with open(config.CSV_LOG_PATH, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["timestamp", "image_name", "status"])
            except Exception as e:
                print(f"Error al crear el archivo de log CSV: {e}")

    def get_processed_images(self):
        """Lee el log CSV y devuelve un conjunto de nombres de imágenes ya procesadas."""
        processed = set()
        if os.path.exists(config.CSV_LOG_PATH):
            try:
                with open(config.CSV_LOG_PATH, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if "image_name" in row and row["status"] == "Success":
                            processed.add(row["image_name"])
            except Exception as e:
                print(f"Error al leer el archivo de log CSV: {e}")
        return processed

    def log_processing(self, image_name, status):
        """Agrega un registro al archivo de log CSV."""
        try:
            with open(config.CSV_LOG_PATH, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([timestamp, image_name, status])
        except Exception as e:
            print(f"Error al escribir en el log CSV: {e}")

    def _log_db_status(self, message, level="INFO"):
        """Escribe un registro en parsed_documents/db_processing.log."""
        log_file = os.path.join(config.PARSED_DIR, "db_processing.log")
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [{level}] {message}\n")
        except Exception as e:
            print(f"Error al escribir en el log de BD: {e}")

    def _update_database_record(self, file_name, parsed_data):
        """
        Extrae el ID de transacción y el tipo de ejemplar de los datos parseados y el nombre de archivo,
        busca el registro coincidente en MySQL RDS AWS, consolida las firmas/sellos de todos los ejemplares
        (original, duplicado, triplicado, cuatriplicado) fusionando la información histórica en BD con la actual,
        evalúa y actualiza los campos bot_confirmado_cliente y bot_confirmado_distribuidor según el número
        de copias, y actualiza el registro respectivo. Retorna un diccionario con el resultado para el reporte.
        """
        import pymysql
        
        self._log_db_status(f"Iniciando persistencia para: {file_name}")
        print(f"  -> Conectando a BD remota para actualizar {file_name}...")
        
        # 1. Extraer transaccion_id prioritariamente de la respuesta parseada
        transaccion_id = None
        extracted_text = parsed_data.get("extracted_text", {})
        
        # Buscar en extracted_text
        trans_val = extracted_text.get("transaccion_id")
        if trans_val:
            try:
                transaccion_id = int(str(trans_val).strip())
                self._log_db_status(f"transaccion_id extraído exitosamente de extracted_text: {transaccion_id}")
            except ValueError:
                pass
                
        # Buscar en el root si no se encontró
        if not transaccion_id:
            trans_val = parsed_data.get("transaccion_id")
            if trans_val:
                try:
                    transaccion_id = int(str(trans_val).strip())
                    self._log_db_status(f"transaccion_id extraído exitosamente de la raíz del JSON: {transaccion_id}")
                except ValueError:
                    pass
                    
        # Fallback al nombre del archivo solo si no está en la respuesta parseada
        if not transaccion_id:
            match_trans = re.search(r"scan_(\d+)_pag_", file_name)
            if match_trans:
                try:
                    transaccion_id = int(match_trans.group(1))
                    self._log_db_status(f"transaccion_id no encontrado en la respuesta. Usando fallback de nombre de archivo: {transaccion_id}", "WARNING")
                except ValueError:
                    pass
                    
        if not transaccion_id:
            # Fallback secundario a cualquier bloque numérico de más de 8 dígitos en el nombre del archivo
            match_fallback = re.search(r"(\d{9,})", file_name)
            if match_fallback:
                try:
                    transaccion_id = int(match_fallback.group(1))
                    self._log_db_status(f"transaccion_id no encontrado en respuesta. Usando fallback de bloque numérico de archivo: {transaccion_id}", "WARNING")
                except ValueError:
                    pass
                    
        if not transaccion_id:
            err_msg = f"No se pudo extraer transaccion_id de la respuesta ni del nombre de archivo: {file_name}"
            self._log_db_status(err_msg, "ERROR")
            print(f"  ❌ [BD]: {err_msg}")
            return {
                "numero_remito": extracted_text.get("numero_remito", "Desconocido"),
                "transaccion_id": None,
                "encontrado": False,
                "error_msg": err_msg
            }

        # 2. Identificar la columna a actualizar basado en extracted_text -> tipo (o en su defecto, número de página)
        tipo = str(extracted_text.get("tipo", "")).upper().strip()
        
        tipo_map = {
            "ORIGINAL": "ocr_original",
            "DUPLICADO": "ocr_duplicado",
            "TRIPLICADO": "ocr_triplicado",
            "CUATRIPLICADO": "ocr_cuatriplcado"
        }
        
        campo_db = tipo_map.get(tipo)
        
        if not campo_db:
            # Fallback por número de página en el nombre de archivo (ej: _pag_4)
            match_pag = re.search(r"_pag_(\d+)", file_name)
            if match_pag:
                try:
                    pag_num = int(match_pag.group(1))
                    pag_map = {
                        1: "ocr_original",
                        2: "ocr_duplicado",
                        3: "ocr_triplicado",
                        4: "ocr_cuatriplcado"
                    }
                    campo_db = pag_map.get(pag_num)
                    self._log_db_status(f"Tipo no detectado o inválido ({tipo}). Mapeado por número de página ({pag_num}) a campo '{campo_db}'.", "WARNING")
                except Exception:
                    pass
                    
        if not campo_db:
            err_msg = f"No se pudo determinar el tipo de ejemplar (original/duplicado/triplicado/cuatriplicado) para: {file_name}"
            self._log_db_status(err_msg, "ERROR")
            print(f"  ❌ [BD]: {err_msg}")
            return {
                "numero_remito": extracted_text.get("numero_remito", "Desconocido"),
                "transaccion_id": transaccion_id,
                "encontrado": False,
                "error_msg": err_msg
            }

        # 3. Formatear la confianza como porcentaje entero
        confianza_val = parsed_data.get("confianza", 100)
        if isinstance(confianza_val, (int, float)):
            if confianza_val <= 1.0:
                confianza_val = int(confianza_val * 100)
            else:
                confianza_val = int(confianza_val)
        else:
            try:
                f_val = float(confianza_val)
                if f_val <= 1.0:
                    confianza_val = int(f_val * 100)
                else:
                    confianza_val = int(f_val)
            except Exception:
                confianza_val = 100
                
        # 4. Generar el payload JSON estructurado requerido para este ejemplar
        firmas = parsed_data.get("firmas")
        if firmas is None:
            firmas = extracted_text.get("firmas", [])
            
        sellos = parsed_data.get("sellos")
        if sellos is None:
            sellos = extracted_text.get("sellos", [])
            
        def clean_element(elem):
            if hasattr(elem, "model_dump"):
                d = elem.model_dump()
            elif isinstance(elem, dict):
                d = elem
            else:
                return {}
            return {
                "emision": d.get("emision", ""),
                "complejidad": d.get("complejidad", ""),
                "posicion_x": d.get("posicion_x", ""),
                "posicion_y": d.get("posicion_y", "")
            }

        cleaned_firmas = [clean_element(f) for f in firmas] if isinstance(firmas, list) else []
        cleaned_sellos = [clean_element(s) for s in sellos] if isinstance(sellos, list) else []

        ocr_data = {
            "firmas": cleaned_firmas,
            "sellos": cleaned_sellos,
            "original_filename": file_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "confianza": confianza_val,
            "archivo": parsed_data.get("archivo", "")
        }
        ocr_json_str = json.dumps(ocr_data, ensure_ascii=False)

        # 5. Conectarse, fusionar ejemplares y actualizar en la base de datos remota
        connection = None
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
            
            with connection.cursor() as cursor:
                # Buscar el registro coincidente recuperando las columnas de ejemplares y copias
                select_sql = """
                    SELECT id, finne_Copias, ocr_original, ocr_duplicado, ocr_triplicado, ocr_cuatriplcado, finne_transaccionID
                    FROM remitos 
                    WHERE finne_transaccionID = %s
                """
                cursor.execute(select_sql, (transaccion_id,))
                row = cursor.fetchone()
                
                if not row:
                    err_msg = f"No se encontró ningún registro en la base de datos con finne_transaccionID = {transaccion_id}"
                    self._log_db_status(err_msg, "ERROR")
                    print(f"  ❌ [BD]: {err_msg}")
                    return {
                        "numero_remito": extracted_text.get("numero_remito", "Desconocido"),
                        "transaccion_id": transaccion_id,
                        "encontrado": False,
                        "error_msg": err_msg
                    }
                
                # Helper local para determinar si un JSON contiene firmas o sellos
                def esta_firmado(ocr_val):
                    if not ocr_val:
                        return False
                    if isinstance(ocr_val, str):
                        try:
                            ocr_val = json.loads(ocr_val)
                        except Exception:
                            return False
                    if not isinstance(ocr_val, dict):
                        return False
                    f_list = ocr_val.get("firmas", [])
                    s_list = ocr_val.get("sellos", [])
                    return len(f_list) > 0 or len(s_list) > 0

                # Obtener ejemplares consolidados: el actual se pisa con la información nueva, los demás con lo histórico de BD
                original_doc = ocr_data if campo_db == "ocr_original" else row.get("ocr_original")
                duplicado_doc = ocr_data if campo_db == "ocr_duplicado" else row.get("ocr_duplicado")
                triplicado_doc = ocr_data if campo_db == "ocr_triplicado" else row.get("ocr_triplicado")
                cuatriplicado_doc = ocr_data if campo_db == "ocr_cuatriplcado" else row.get("ocr_cuatriplcado")

                copias = row.get("finne_Copias")
                if copias is None:
                    copias = 2  # Por defecto
                    
                # Aplicar reglas de negocio para determinar las confirmaciones
                if copias == 2:
                    # Distribuidor firma duplicado. Operador logístico no se requiere.
                    bot_confirmado_cliente = False
                    bot_confirmado_distribuidor = esta_firmado(duplicado_doc)
                else:
                    # Copias > 2: Operador logístico firma duplicado. Distribuidor firma triplicado o cuatriplicado.
                    bot_confirmado_cliente = esta_firmado(duplicado_doc)
                    bot_confirmado_distribuidor = esta_firmado(triplicado_doc) or esta_firmado(cuatriplicado_doc)

                # Actualizar el ejemplar respectivo y las confirmaciones de firmas
                update_sql = f"""
                    UPDATE remitos 
                    SET {campo_db} = %s,
                        bot_confirmado_cliente = %s,
                        bot_confirmado_distribuidor = %s
                    WHERE id = %s
                """
                cursor.execute(update_sql, (ocr_json_str, bot_confirmado_cliente, bot_confirmado_distribuidor, row["id"]))
                
            connection.commit()
            success_msg = (
                f"Base de Datos actualizada con éxito. Registro ID={row['id']} columna={campo_db} "
                f"para transaccion={transaccion_id}. Copias={copias}. "
                f"Confirmados -> Operador: {bot_confirmado_cliente}, Distribuidor: {bot_confirmado_distribuidor}."
            )
            self._log_db_status(success_msg, "INFO")
            print(f"  ✔ [BD]: {success_msg}")
            
            return {
                "numero_remito": extracted_text.get("numero_remito", "Desconocido"),
                "transaccion_id": transaccion_id,
                "encontrado": True,
                "copias": copias,
                "confirmado_cliente": bot_confirmado_cliente,
                "confirmado_distribuidor": bot_confirmado_distribuidor
            }
            
        except Exception as e:
            err_msg = f"Error al actualizar la base de datos para {file_name}: {e}"
            self._log_db_status(err_msg, "ERROR")
            print(f"  ❌ [BD]: {err_msg}")
            return {
                "numero_remito": extracted_text.get("numero_remito", "Desconocido"),
                "transaccion_id": transaccion_id,
                "encontrado": False,
                "error_msg": err_msg
            }
        finally:
            if connection:
                try:
                    connection.close()
                except Exception:
                    pass

    def process_document(self, image_path):
        """
        Procesa un documento escaneado (imagen) usando Google Gemini 1.5, el VLM Local o Power Automate.
        Guarda los resultados estructurados (JSON) en parsed_documents/.
        """
        if self.provider == "local_vlm" and not self.local_client:
            print("El cliente de VLM Local no está inicializado.")
            return None
        elif self.provider == "gemini" and not self.client:
            print("El cliente de Gemini no está inicializado. Falta la API Key en el .env.")
            return None
        elif self.provider == "powerautomate" and not config.POWERAUTOMATE_URL:
            print("La URL del flujo de Power Automate (POWERAUTOMATE_URL) no está configurada en el .env.")
            return None

        file_name = os.path.basename(image_path)
        print(f"Procesando imagen con {self.provider.upper()}: {file_name}...")
        
        try:
            if self.provider == "powerautomate":
                import urllib.request
                import urllib.parse
                
                # Leer y codificar imagen a base64
                with open(image_path, "rb") as image_file:
                    datos_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                
                # Armar el payload JSON
                payload = {
                    "filename": file_name,
                    "imagebase64": datos_base64
                }
                
                # Enviar petición POST
                req = urllib.request.Request(
                    config.POWERAUTOMATE_URL,
                    data=json.dumps(payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                
                print("  Enviando datos al flujo de Power Automate...")
                with urllib.request.urlopen(req) as response:
                    status_code = response.getcode()
                    if status_code not in (200, 201, 202):
                        raise Exception(f"El servidor de Power Automate retornó código de estado: {status_code}")
                    response_body = response.read().decode('utf-8')
                
                # Parsear la respuesta externa
                response_data = json.loads(response_body)
                resultado_str = response_data.get("resultado")
                if not resultado_str:
                    raise Exception("La respuesta de Power Automate no contiene el campo 'resultado'.")
                
                # Parsear el JSON embebido del resultado
                resultado_dict = json.loads(resultado_str)
                
                # Decodificar y formatear el path de archivo con SharePoint FQDN si existe
                archivo_path = resultado_dict.get("archivo", "")
                if archivo_path and config.SHAREPOINT_FQDN:
                    # Decodificación doble: 
                    # 1. urllib.parse.unquote convierte %252f -> %2f y %2b -> +
                    # 2. urllib.parse.unquote_plus convierte %2f -> / y + -> espacio en blanco
                    decoded_path = urllib.parse.unquote(archivo_path)
                    decoded_path = urllib.parse.unquote_plus(decoded_path)
                    
                    # Normalizar barras y unir con SharePoint FQDN
                    sharepoint_fqdn = config.SHAREPOINT_FQDN.rstrip('/')
                    path_part = decoded_path.lstrip('/')
                    
                    # Codificar URL preservando barras usando quote(..., safe="/")
                    encoded_path_part = urllib.parse.quote(path_part, safe="/")
                    
                    formatted_url = f"{sharepoint_fqdn}/{encoded_path_part}"
                    resultado_dict["archivo"] = formatted_url
                    print(f"  URL SharePoint formateada: {formatted_url}")
                
                parsed_data = resultado_dict

            else:
                prompt = (
                    "Eres un asistente experto en extracción de datos de remitos (Document AI).\n"
                    "Extrae la información de este remito respetando estrictamente el esquema JSON proporcionado.\n"
                    "Pon especial atención en detectar visualmente la presencia de firmas (rayones, trazos a mano) "
                    "y de sellos (de tinta, redondos, rectangulares u ovalados, o texto de aclaración estampado).\n\n"
                    "REGLAS DE NEGOCIO IMPORTANTES PARA DETECTAR LA EMISIÓN DE FIRMAS Y SELLOS:\n"
                    "1. Sello de Persona: Suele ser simple y constar de dos renglones de texto estampado o manuscrito que indican el nombre y apellido de una persona y un número (DNI, legajo o ID), por ejemplo 'RICCA, Nahuel D.N.I: 42.179.358'. Aunque parezca texto normal, si sirve como aclaración de la firma, debe registrarse como un sello de emision 'persona'.\n"
                    "2. Sello de Comercio: Suele ser más elaborado y grande. Puede incluir un logo, la palabra 'supermercados', 'S.A.', una fecha o dirección (como el sello circular en el centro).\n"
                    "3. Relación Firma-Emisor: Si la firma manuscrita está realizada encima de un sello del comercio (institucional), se clasifica como emision: 'comercio'. Si corresponde a una persona natural, puede estar suelta o cerca de la aclaración/sello de una persona física (emision: 'persona').\n\n"
                    "Busca minuciosamente en el documento TODOS los sellos. Por ejemplo, en la zona de firma a la derecha puede haber un sello de persona (aclaración y DNI) cruzado por la firma manuscrita, además del sello circular comercial en el centro. Agrégalos todos."
                )

                if self.provider == "local_vlm":
                    # Cargar imagen y redimensionar si es muy grande para optimizar tokens en VLM local
                    import io
                    img_pil = Image.open(image_path)
                    
                    # Resolución máxima recomendada para mantener legibilidad de OCR sin saturar la VRAM
                    max_size = 1280
                    width, height = img_pil.size
                    if max(width, height) > max_size:
                        if width > height:
                            new_width = max_size
                            new_height = int(height * (max_size / width))
                        else:
                            new_height = max_size
                            new_width = int(width * (max_size / height))
                        # Usar Lanczos para preservar la nitidez del texto para el OCR
                        img_pil = img_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Guardar a bytes en memoria para la codificación Base64
                    buffered = io.BytesIO()
                    img_pil.save(buffered, format="JPEG", quality=85)
                    datos_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

                    response = self.local_client.chat.completions.create(
                        model=config.VLM_MODEL,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{datos_base64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        response_format={
                            "type": "json_object",
                            "schema": StructuredData.model_json_schema()
                        },
                        extra_body={
                            "options": {
                                "num_ctx": config.VLM_NUM_CTX
                            }
                        },
                        temperature=0.0
                    )
                    result_json_str = response.choices[0].message.content
                else:
                    img = Image.open(image_path)
                    response = self.client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[prompt, img],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=StructuredData,
                            temperature=0.1
                        )
                    )
                    result_json_str = response.text
                
                parsed_data = json.loads(result_json_str)

            # Generar el objeto final a guardar en el disco
            base, ext = os.path.splitext(file_name)
            json_file_path = os.path.join(config.PARSED_DIR, f"{base}.json")
            
            if self.provider == "powerautomate":
                final_data = {
                    "original_filename": file_name,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    **parsed_data
                }
            else:
                final_data = {
                    "original_filename": file_name,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "extracted_text": parsed_data.get("extracted_text", {})
                }
            
            os.makedirs(config.PARSED_DIR, exist_ok=True)
            with open(json_file_path, "w", encoding="utf-8") as jf:
                json.dump(final_data, jf, indent=4, ensure_ascii=False)
            
            print(f"  ✔ JSON estructurado por {self.provider.upper()} guardado en: {json_file_path}")
            
            # Actualizar en base de datos remota y obtener resultado
            db_status = self._update_database_record(file_name, final_data)
            
            self.log_processing(file_name, "Success")
            
            return {
                "original": image_path,
                "json": json_file_path,
                "data": final_data,
                "db_status": db_status
            }

            
        except Exception as e:
            print(f"Error durante el análisis del documento {file_name}: {e}")
            self.log_processing(file_name, f"Error: {str(e)}")
            return None

    def process_all_scans(self):
        """Busca todas las imágenes no procesadas en el directorio de salida y las analiza con el proveedor de IA configurado."""
        print(f"Escaneando directorio de salida para procesamiento AI: {config.SCAN_OUTPUT_DIR}")
        
        valid_extensions = (".jpg", ".jpeg", ".png", ".bmp")
        if not os.path.exists(config.SCAN_OUTPUT_DIR):
            print(f"El directorio de escaneos no existe: {config.SCAN_OUTPUT_DIR}")
            return
            
        all_files = os.listdir(config.SCAN_OUTPUT_DIR)
        processed_set = self.get_processed_images()
        
        files_to_process = []
        for f in all_files:
            if f.lower().endswith(valid_extensions):
                if f not in processed_set:
                    files_to_process.append(os.path.join(config.SCAN_OUTPUT_DIR, f))
        
        if not files_to_process:
            print("No se encontraron nuevas imágenes escaneadas para procesar.")
            return
            
        print(f"Se encontraron {len(files_to_process)} nuevas imágenes para analizar con {self.provider.upper()}.")

        db_results = []
        for file_path in files_to_process:
            result = self.process_document(file_path)
            if result:
                print(f"  -> {os.path.basename(file_path)}: Procesado exitosamente.")
                if "db_status" in result and result["db_status"]:
                    db_results.append(result["db_status"])
            else:
                db_results.append({
                    "numero_remito": "Desconocido",
                    "transaccion_id": "Error al procesar",
                    "encontrado": False,
                    "error_msg": "Excepción en procesamiento del documento"
                })
            print("-" * 40)
            
        if db_results:
            # Gestionar número de lote incremental
            lote_file = os.path.join(config.PARSED_DIR, "lote_counter.txt")
            lote_num = 1
            try:
                if os.path.exists(lote_file):
                    with open(lote_file, "r", encoding="utf-8") as lf:
                        content = lf.read().strip()
                        if content.isdigit():
                            lote_num = int(content) + 1
                os.makedirs(os.path.dirname(lote_file), exist_ok=True)
                with open(lote_file, "w", encoding="utf-8") as lf:
                    lf.write(str(lote_num))
            except Exception as e:
                print(f"Advertencia al gestionar contador de lotes: {e}")
                
            # Imprimir resumen de detección de firmas solicitado
            print("\n" + "=" * 50)
            print("RESUMEN DE DETECCION DE FIRMAS")
            print(f"Fecha: {datetime.now().strftime('%Y-%m-%d')}")
            print(f"Lote: {lote_num}")
            print("=" * 50)
            
            for r in db_results:
                print()
                num_remito = r.get("numero_remito", "Desconocido")
                tx_id = r.get("transaccion_id")
                
                if not r.get("encontrado", False):
                    tx_str = str(tx_id) if tx_id else "Desconocido"
                    print(f"Nro Remito {num_remito}")
                    print(f"❌ No se encontró en DB con TransaccionID {tx_str}")
                else:
                    copias = r.get("copias", 2)
                    conf_cliente = r.get("confirmado_cliente")
                    conf_dist = r.get("confirmado_distribuidor")
                    
                    # Formatear cliente/operador
                    if copias == 2:
                        op_status = "(no se requiere)"
                    else:
                        op_status = "Sí" if conf_cliente else "No"
                        
                    # Formatear distribuidor
                    dist_status = "Sí" if conf_dist else "No"
                    
                    print(f"Nro Remito {num_remito}")
                    print(f"Firmado por Operador: {op_status}")
                    print(f"Firmado por Distribuidor: {dist_status}")
            print("\n" + "=" * 50)
