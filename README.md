# Automatización de Recepción y Procesamiento de Documentos

Este proyecto permite realizar el escaneo masivo de documentos en papel utilizando el alimentador automático (ADF) de una impresora multifunción mapeada en la red LAN (por ejemplo, **RICOH IM C300**) y, posteriormente, procesar las imágenes resultantes mediante reconocimiento visual usando **MediaPipe** y **OpenCV**.

El flujo consta de dos pasos principales:
1. **Paso 1 (Escaneo)**: Comunicación con el driver WIA del escáner en red para disparar la bandeja de alimentación y guardar las páginas como archivos de imagen (JPEG/PNG) parametrizables.
2. **Paso 2 (Reconocimiento)**: Análisis de los documentos usando MediaPipe para identificar regiones de interés u objetos dentro de las imágenes escaneadas.

---

## Estructura del Proyecto

```text
dy_automatizacion_recepcion_docs/
├── .env                  # Variables de entorno locales (DPI, formato, etc. - No subir al repositorio)
├── .env.template         # Plantilla de variables de entorno de ejemplo
├── .gitignore            # Omitir archivos temporales y la configuración local
├── config.py             # Carga centralizada y tipada de variables de configuración
├── scanner.py            # Módulo de integración WIA para listado de dispositivos y escaneo masivo
├── recognition.py        # Módulo de reconocimiento de imágenes usando OpenCV y MediaPipe
├── main.py               # Interfaz de consola CLI interactiva para el usuario
└── requirements.txt      # Dependencias del proyecto
```

---

## Requisitos Previos

### 1. Sistema Operativo y Python
- **Windows** (requerido para el módulo COM WIA).
- **Python 3.10** o superior (se recomienda **Python 3.10** debido a compatibilidad estricta de versiones anteriores de MediaPipe y TensorFlow en Windows).

### 2. Driver WIA de la Multifunción RICOH IM C300

Para que Windows reconozca el escáner a través de la red, existen **dos tipos de drivers WIA**. Es importante instalar el correcto:

#### Driver WSD Genérico de Windows (No recomendado)
- Se instala automáticamente cuando Windows detecta la impresora en la red vía WSD (Web Services for Devices).
- Aparece como **"Dispositivo de digitalización de WSD"** en la descripción del dispositivo.
- **Problema conocido**: Muchas Ricoh tienen la opción *"Prohibir comando esc. WSD"* activada por defecto, lo que bloquea el escaneo remoto (Pull Scan) desde el ADF con error `E_FAIL (-2147467259)`.

#### Driver Network WIA de Ricoh (✔ Recomendado)
- Se conecta **directamente por IP** al escáner, sin pasar por el protocolo WSD.
- Aparece como **"Type Generic Scanner(Network) WIA"** en la lista de dispositivos.
- **Solución definitiva** al bloqueo de WSD. Este es el driver que se debe usar.

**Instalación del Driver Network WIA (método probado):**

1. **Desde el menú interactivo** (Opción 1): Seleccione el archivo `Setup.inf` del driver Network WIA. El programa ejecutará `pnputil` con elevación UAC y abrirá el panel de Escáneres y Cámaras automáticamente.

2. **Manual desde PowerShell (Administrador)**:
   ```powershell
   # Paso 1: Agregar el driver al almacén de Windows
   pnputil /add-driver "drivers_win\Network WIA Driver scanner_z06624L20_WIA\Network\Setup.inf" /install

   # Paso 2: Abrir el panel de Escáneres y Cámaras para agregar el dispositivo
   rundll32 shell32.dll,Control_RunDLL sticpl.cpl
   ```
   En el panel: clic en **Agregar** → seleccionar **"Type Generic Scanner(Network) WIA"** → ingresar la IP del escáner (`192.168.1.54`).

3. **Verificar**: Ejecutar `python main.py`, Opción 2 para ver si el nuevo escáner aparece listado. Seleccionarlo para que quede guardado en `.env`.

### 3. Motor de Reconocimiento Óptico de Caracteres (Tesseract OCR)
Para habilitar el paso 2 de extracción de textos del documento e incluirlos de forma estructurada en el JSON:
1. Instale el motor de Tesseract. El instalador descargado se encuentra en la carpeta del proyecto en `drivers_win/tesseract-ocr-w64-setup-5.5.0.20241111.exe`. Puede ejecutarlo desde el menú del programa (Opción 1) o haciendo doble clic en él.
2. **IMPORTANTE**: Durante la instalación, en el paso de selección de componentes, despliegue la sección **"Additional language data"** (Datos de idioma adicionales) y marque la opción **"Spanish"** (español) para habilitar el reconocimiento correcto de tildes y caracteres en español. También asegúrese de tener marcado "English".

---


## Instalación

1. **Clonar o abrir el directorio del proyecto**.
2. **Crear el entorno virtual con uv** (usando Python 3.10):
   ```powershell
   uv venv --python 3.10
   ```
3. **Instalar las dependencias**:
   ```powershell
   uv pip install -r requirements.txt
   ```
4. **Configurar las variables de entorno**:
   Copie el archivo `.env.template` a `.env` y edite las variables si es necesario:
   ```powershell
   copy .env.template .env
   ```

---

## Uso del Programa

Ejecute el script principal usando el cargador de `uv`:
```powershell
uv run python main.py
```


Se presentará un menú interactivo en español con las siguientes opciones:

### 1. Instalar controladores (impresora/escáner WIA)
Escanea la carpeta `drivers_win/` en busca de instaladores ejecutables (`.exe`) o archivos de controlador (`.inf`). Al seleccionar uno:
- **Archivos `.inf`**: Ejecuta `pnputil /add-driver` con elevación UAC para agregarlo al almacén de controladores de Windows, y luego abre automáticamente el panel de **Escáneres y Cámaras** (`sticpl.cpl`) para completar la configuración del dispositivo de red.
- **Archivos `.exe`**: Lanza el instalador gráfico del fabricante.

### 2. Seleccionar escáneres/multifunciones del sistema (WIA)
Muestra los escáneres compatibles con WIA instalados en Windows. Al elegir el número correspondiente a tu Ricoh, se guardará automáticamente en el archivo `.env` en la variable `SCANNER_NAME` y se correrá un test de conexión de red rápido.

### 3. Enviar página de prueba de impresión
Dispara la página de prueba oficial del controlador en Windows para la impresora configurada en `SCANNER_NAME`. Esto permite comprobar que el canal físico de impresión funciona correctamente.

### 4. Iniciar Escaneo Masivo (Paso 1 - Bandeja/ADF)
Dispara la bandeja de alimentación automática (ADF) de la multifunción. Escanea de forma consecutiva todas las páginas cargadas y las almacena en la carpeta especificada en `.env` (por defecto `scanned_documents/`).

**Resiliencia ante errores:**
- Si el ADF falla con `E_FAIL`, el sistema reintenta hasta **3 veces** reconectándose al dispositivo WIA entre cada intento.
- Si persiste el error, ofrece un menú interactivo para: reintentar, cambiar a **modo Flatbed (vidrio)** o abortar.

### 5. Procesar Imágenes Escaneadas (Paso 2 - IA)
Analiza las imágenes de la carpeta de escaneo usando un modelo de lenguaje visual (VLM) o un flujo de automatización. Soporta tres proveedores:
- **Gemini AI** (nube): Requiere `GEMINI_API_KEY` en `.env`.
- **Ollama Local** / **VLM Local**: Requiere Ollama o vLLM corriendo con el modelo configurado en `VLM_MODEL`.
- **Power Automate**: Convierte la imagen a Base64 y la envía al flujo configurado en `POWERAUTOMATE_URL`. Parsea e integra los resultados y genera el link del archivo en SharePoint formateando el path con `SHAREPOINT_FQDN`.

### 6. Mostrar Configuración Actual (.env)
Imprime en pantalla los parámetros con los que está operando el sistema actualmente (DPI, Color, Formato, etc.).

### 7. Gestionar Servicio Ollama (VLM Local)
Submenú para iniciar, detener, verificar estado del servidor Ollama y liberar memoria RAM/VRAM.

---

## Personalización y Variables de Entorno (.env)

| Variable | Descripción | Valores de Ejemplo |
| :--- | :--- | :--- |
| `SCANNER_NAME` | Nombre o parte del nombre de la impresora multifunción | `RICOH IM C300` |
| `SCAN_OUTPUT_DIR` | Directorio donde se guardarán las imágenes | `scanned_documents` |
| `SCAN_DPI` | Resolución del escaneo | `150`, `200`, `300` |
| `SCAN_COLOR_MODE` | Formato de color | `1` (Color), `2` (Grises), `4` (B&N) |
| `SCAN_FORMAT` | Formato de archivo de imagen | `JPG`, `PNG`, `TIFF` |
| `SCAN_SOURCE` | Alimentador automático o cama plana | `ADF` o `FLATBED` |
| `AI_PROVIDER` | Proveedor de IA o servicio para procesamiento | `gemini`, `local` o `powerautomate` |
| `VLM_MODEL` | Modelo de VLM local para Ollama | `qwen2.5vl:7b` |
| `GEMINI_API_KEY` | Clave API de Google Gemini | `AIza...` |
| `POWERAUTOMATE_URL` | URL del flujo de Power Automate a invocar | `https://.../workflows/...` |
| `SHAREPOINT_FQDN` | FQDN del SharePoint para formatear la ruta del archivo | `https://donyeyosa416.sharepoint.com/:i:/r/sites/Administracin` |

---

## Troubleshooting

### Error `E_FAIL (-2147467259)` al escanear desde el ADF
**Causa**: El driver WSD genérico de Windows está bloqueado por la configuración del escáner Ricoh (*"Prohibir comando esc. WSD: Prohibir"*).

**Solución**: Instalar el **Driver Network WIA de Ricoh** (ver sección "Driver WIA" arriba). Este driver se conecta por IP y no depende del protocolo WSD.

### El escáner WIA no aparece en la Opción 2
1. Verifique que el driver Network WIA esté instalado (`pnputil /enum-drivers` como Admin).
2. Abra el panel de Escáneres y Cámaras (`rundll32 shell32.dll,Control_RunDLL sticpl.cpl`) y verifique que el dispositivo esté listado.
3. Si no aparece, agréguelo desde ese mismo panel con la IP del escáner.

### Ollama se congela o no responde al procesar imágenes
**Causa**: Las imágenes del escaneo son demasiado grandes en píxeles para la VRAM disponible.

**Solución automática**: El sistema redimensiona las imágenes a un máximo de 1280px antes de enviarlas al VLM local. Si persiste:
1. Detenga Ollama (Opción 7 → Subopción 3) o ejecute: `taskkill /f /im ollama.exe`
2. Vuelva a iniciar Ollama (Opción 7 → Subopción 2)


