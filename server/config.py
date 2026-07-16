import os
from dotenv import load_dotenv

# Cargar variables de entorno buscando en múltiples rutas posibles para robustez en ejecución y desarrollo
env_path = ".env"
if not os.path.exists(env_path):
    env_path = os.path.join("server", ".env")
    if not os.path.exists(env_path):
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

# Configuraciones y valores por defecto
SCANNER_NAME = os.getenv("SCANNER_NAME", "RICOH IM C300")
SCAN_OUTPUT_DIR = os.getenv("SCAN_OUTPUT_DIR", "scanned_documents")
SCAN_DPI = int(os.getenv("SCAN_DPI", "200"))
SCAN_COLOR_MODE = int(os.getenv("SCAN_COLOR_MODE", "1"))  # 1 = Color, 2 = Grayscale, 4 = B&W
SCAN_FORMAT = os.getenv("SCAN_FORMAT", "JPG").upper()
SCAN_SOURCE = os.getenv("SCAN_SOURCE", "ADF").upper()  # ADF o FLATBED

# Tiempos de espera (delays) para sincronización con el hardware y sistema operativo
SCAN_ADF_DELAY = float(os.getenv("SCAN_ADF_DELAY", "2.5"))
SCAN_FILE_WRITE_DELAY = float(os.getenv("SCAN_FILE_WRITE_DELAY", "0.5"))

# Proveedor de IA (gemini, local o powerautomate) y configuraciones
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
if AI_PROVIDER == "local":
    AI_PROVIDER = "local_vlm"

VLM_API_URL = os.getenv("VLM_API_URL", "http://localhost:11434/v1")
VLM_API_KEY = os.getenv("VLM_API_KEY", "ollama")
VLM_MODEL = os.getenv("VLM_MODEL", "qwen2.5vl:7b")
VLM_NUM_CTX = int(os.getenv("VLM_NUM_CTX", "16384"))

POWERAUTOMATE_URL = os.getenv("POWERAUTOMATE_URL", "")
SHAREPOINT_FQDN = os.getenv("SHAREPOINT_FQDN", "")

DB_HOST = os.getenv("DB_HOST", "dydb2-instance-1.cz8kik28igwg.us-east-1.rds.amazonaws.com")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "Firma_de_remitos")
DB_USER = os.getenv("DB_USER", "DBAdmin_Firma_de_Remitos")
DB_PASSWORD = os.getenv("DB_PASSWORD", "37@Firmadoss32")


# WIA GUIDs de Formatos de Imagen comunes
WIA_FORMATS = {
    "BMP": "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}",
    "PNG": "{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}",
    "GIF": "{B96B3CB0-0728-11D3-9D7B-0000F81EF32E}",
    "JPG": "{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}",
    "TIFF": "{B96B3CB1-0728-11D3-9D7B-0000F81EF32E}"
}

# Obtener el GUID correspondiente al formato seleccionado
WIA_IMAGE_FORMAT_GUID = WIA_FORMATS.get(SCAN_FORMAT, WIA_FORMATS["JPG"])

# Asegurar que el directorio de salida exista
if not os.path.exists(SCAN_OUTPUT_DIR):
    os.makedirs(SCAN_OUTPUT_DIR)

def print_config():
    print("=" * 50)
    print(" CONFIGURACIÓN CARGADA ")
    print("=" * 50)
    print(f"Escáner objetivo:    {SCANNER_NAME}")
    print(f"Carpeta de salida:   {os.path.abspath(SCAN_OUTPUT_DIR)}")
    print(f"Resolución (DPI):    {SCAN_DPI}")
    print(f"Modo de color:       {SCAN_COLOR_MODE} (1=Color, 2=Grayscale, 4=B&W)")
    print(f"Formato de imagen:   {SCAN_FORMAT} ({WIA_IMAGE_FORMAT_GUID})")
    print(f"Origen del papel:    {SCAN_SOURCE}")
    print(f"Delays de hardware:  ADF={SCAN_ADF_DELAY}s, Escritura={SCAN_FILE_WRITE_DELAY}s")
    print("-" * 50)
    print(f"Proveedor de IA:     {AI_PROVIDER.upper()}")
    if AI_PROVIDER == "local_vlm":
        print(f"API URL VLM Local:   {VLM_API_URL}")
        print(f"Modelo VLM Local:    {VLM_MODEL}")
        print(f"Contexto (num_ctx):  {VLM_NUM_CTX} tokens")
    elif AI_PROVIDER == "powerautomate":
        print(f"Power Automate URL:  {POWERAUTOMATE_URL}")
        print(f"SharePoint FQDN:     {SHAREPOINT_FQDN}")
    print("-" * 50)
    print(" CONFIGURACIÓN DE BASE DE DATOS ")
    print(f"Host MySQL:          {DB_HOST}")
    print(f"Puerto:              {DB_PORT}")
    print(f"Base de Datos:       {DB_NAME}")
    print(f"Usuario:             {DB_USER}")
    print("=" * 50)


def update_env_scanner_name(new_name):
    """Actualiza la variable SCANNER_NAME en el archivo .env y recarga la configuración."""
    global SCANNER_NAME
    env_file = ".env"
    lines = []
    updated = False
    
    # Leer el archivo .env actual
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
    # Intentar reemplazar la línea
    new_lines = []
    for line in lines:
        if line.strip().startswith("SCANNER_NAME="):
            new_lines.append(f"SCANNER_NAME={new_name}\n")
            updated = True
        else:
            new_lines.append(line)
            
    # Si no se encontró, añadirlo al final
    if not updated:
        new_lines.append(f"\nSCANNER_NAME={new_name}\n")
        
    # Guardar cambios
    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
    # Recargar la variable en memoria
    SCANNER_NAME = new_name
    print(f"¡Configuración actualizada en .env! Nuevo escáner: {new_name}")

# Directorios de procesamiento de información
PARSED_DIR = "parsed_documents"
CSV_LOG_PATH = os.path.join(PARSED_DIR, "processed_log.csv")

# Asegurar que el directorio de datos extraídos exista
if not os.path.exists(PARSED_DIR):
    os.makedirs(PARSED_DIR)

# Configuración SMTP para Notificaciones por Correo
ALERTA_SMTP_HOST = os.getenv("ALERTA_SMTP_HOST", "smtp-mail.outlook.com")
ALERTA_SMTP_PORT = int(os.getenv("ALERTA_SMTP_PORT", "587"))
ALERTA_SMTP_USER = os.getenv("ALERTA_SMTP_USER", "")
ALERTA_SMTP_PASSWORD = os.getenv("ALERTA_SMTP_PASSWORD", "")
ALERTA_SMTP_NAME = os.getenv("ALERTA_SMTP_NAME", "Remitos Don Yeyo")
EMAIL_DESTINATARIOS = os.getenv("EMAIL_DESTINATARIOS", "")
EMAIL_SILENCIOSO = os.getenv("EMAIL_SILENCIOSO", "true").lower() == "true"



