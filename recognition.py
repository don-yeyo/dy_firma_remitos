import os
import json
import csv
import base64
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
        else:
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

    def process_document(self, image_path):
        """
        Procesa un documento escaneado (imagen) usando Google Gemini 1.5 o el VLM Local.
        Guarda los resultados estructurados (JSON) en parsed_documents/.
        """
        if self.provider == "local_vlm" and not self.local_client:
            print("El cliente de VLM Local no está inicializado.")
            return None
        elif self.provider != "local_vlm" and not self.client:
            print("El cliente de Gemini no está inicializado. Falta la API Key en el .env.")
            return None

        file_name = os.path.basename(image_path)
        print(f"Procesando imagen con {self.provider.upper()}: {file_name}...")
        
        try:
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
            
            final_data = {
                "original_filename": file_name,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "extracted_text": parsed_data.get("extracted_text", {})
            }
            
            os.makedirs(config.PARSED_DIR, exist_ok=True)
            with open(json_file_path, "w", encoding="utf-8") as jf:
                json.dump(final_data, jf, indent=4, ensure_ascii=False)
            
            print(f"  ✔ JSON estructurado por {self.provider.upper()} guardado en: {json_file_path}")
            
            self.log_processing(file_name, "Success")
            
            return {
                "original": image_path,
                "json": json_file_path,
                "data": final_data
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

        
        for file_path in files_to_process:
            result = self.process_document(file_path)
            if result:
                print(f"  -> {os.path.basename(file_path)}: Procesado exitosamente.")
            print("-" * 40)
