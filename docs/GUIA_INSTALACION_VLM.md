# Guía de Instalación del Agente VLM Local (Qwen2.5-VL)

Esta guía detalla la instalación, configuración e integración del modelo visual local (VLM) **Qwen2.5-VL-7B-Instruct** para el procesamiento de remitos comerciales. Cubre tanto el entorno de desarrollo local (Windows 11 con Ollama) como el despliegue seguro en producción (Servidor Dedicado con Linux, Docker y vLLM).

---

## 1. Entorno de Desarrollo Local (Windows 11)

Para el desarrollo local se utiliza **Ollama**, ya que ofrece soporte nativo para Windows con aceleración por GPU (NVIDIA CUDA) y permite exponer un endpoint compatible con la API de OpenAI de forma extremadamente sencilla.

### Paso A: Instalación de Ollama
1. Descarga el instalador de Ollama para Windows desde el sitio oficial: [ollama.com/download/windows](https://ollama.com/download/windows).
2. Ejecuta el instalador (`OllamaSetup.exe`) y sigue las instrucciones en pantalla.
3. Verifica que la aplicación se esté ejecutando en segundo plano (verás el icono de la llama en la bandeja del sistema de Windows).

### Paso B: Descarga del Modelo Visual
1. Abre una terminal de PowerShell.
2. Ejecuta el siguiente comando para descargar y probar el modelo:
   ```powershell
   ollama run qwen2.5vl:7b
   ```
   *Nota: Este modelo tiene un tamaño aproximado de 4.7 GB. Requiere una GPU con al menos 8 GB de VRAM para ejecutarse con fluidez.*
3. Una vez finalizada la descarga, puedes cerrar la consola o escribir `/bye` para salir del chat interactivo. El servidor de Ollama seguirá corriendo en segundo plano en `http://localhost:11434`.

### Paso C: Crear Modelo Derivado con Mayor Contexto
Dado que las imágenes de remitos escaneadas consumen una cantidad importante de tokens de visión, la API de compatibilidad de OpenAI en Ollama puede rechazar las peticiones si exceden el contexto por defecto. Para solucionar esto, creamos un modelo personalizado con el contexto ampliado a 16384 tokens:
1. Asegúrate de tener el archivo `Modelfile` creado en la raíz del proyecto con el siguiente contenido:
   ```dockerfile
   FROM qwen2.5vl:7b
   PARAMETER num_ctx 16384
   ```
2. Ejecuta el siguiente comando en tu terminal para crear el nuevo modelo derivado:
   ```powershell
   ollama create qwen2.5vl-large-ctx -f Modelfile
   ```
3. Configura `VLM_MODEL=qwen2.5vl-large-ctx` en tu archivo `.env`.

---

## 2. Entorno de Producción (Servidor Dedicado Linux + Docker)

Para el despliegue en un servidor dedicado privado (en red local o privada corporativa), se recomienda utilizar **vLLM** u **Ollama** dentro de contenedores Docker, aplicando aislamiento estricto de red (Air-Gapping) y seguridad de accesos por capas.

### Paso A: Archivo de Orquestación Docker Compose (vLLM)
Crea un archivo `docker-compose.yml` en el servidor dedicado para levantar el motor de inferencia optimizado de vLLM con aceleración de GPU NVIDIA:

```yaml
version: '3.8'

services:
  vllm-extractor:
    image: vllm/vllm-openai:latest
    container_name: vllm-server-seguro
    restart: unless-stopped
    # Desconecta el contenedor de redes con acceso a Internet
    networks:
      - red-interna-ai
    ports:
      # Expone el puerto de inferencia únicamente a la interfaz loopback (localhost)
      # Esto evita que otros equipos accedan directamente sin pasar por el proxy inverso
      - "127.0.0.1:8000:8000"
    volumes:
      # Monta el volumen local persistente que contiene los pesos descargados previamente
      - /opt/model_cache/qwen2.5-7b-vl:/root/.cache/huggingface
    environment:
      - HF_HUB_OFFLINE=1
      - TRANSFORMERS_OFFLINE=1
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

networks:
  red-interna-ai:
    driver: bridge
    # Configura la red como interna para impedir estrictamente tráfico saliente (egress)
    internal: true
```

### Paso B: Endurecimiento de Seguridad (Hardening) y Proxy Inverso Nginx
Dado que el motor de inferencia carece de autenticación nativa, se debe proteger con un proxy inverso **Nginx** local que obligue el uso de HTTPS (TLS) y valide tokens:

```nginx
# Ejemplo de bloque de configuración de Nginx (/etc/nginx/sites-available/vlm-proxy)
server {
    listen 443 ssl;
    server_name vlm-extractor.infra.local;

    ssl_certificate /etc/ssl/certs/vlm_selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/vlm_selfsigned.key;

    # Permitir únicamente requests desde el servidor de la aplicación de automatización
    allow 192.168.1.50; # IP de la app cliente
    deny all; # Bloquear el resto

    location /v1 {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Validación de Token de Seguridad
        proxy_set_header Authorization "Bearer token_seguridad_local_interno";
    }
}
```

### Paso C: Límites de Consumo de VRAM
Para evitar que escaneos masivos de muchos documentos o de páginas extremadamente complejas desborden la GPU (provocando fallos por falta de memoria u Out of Memory - OOM), se deben configurar límites operativos en la ejecución de vLLM:
- `--limit-mm-per-prompt image=1`: Limita a una única imagen por petición (evita procesar PDFs multipágina pesados en una sola llamada).
- `--max-model-len 4096`: Limita la longitud máxima de contexto.
- `--gpu-memory-utilization 0.90`: Reserva un 10% de la memoria de la GPU para picos inesperados.

---

## 3. Integración en el Pipeline de Python

El reconocimiento se realiza conectándonos al endpoint local (Ollama o el proxy de producción) mediante la biblioteca oficial de OpenAI, configurando la decodificación guiada para garantizar un JSON estructurado que cumpla con el esquema definido por Pydantic.

> [!TIP]
> **Optimización de Memoria**: Para evitar congelamientos o el uso excesivo de VRAM/RAM en hardware local, el código implementa un redimensionado Lanczos dinámico en memoria a un tamaño máximo de 1280px. Esto preserva la legibilidad perfecta para el OCR y reduce drásticamente la cantidad de tokens visuales cargados en el contexto del modelo.

### Ejemplo de Configuración en el Código


```python
import base64
from openai import OpenAI
from pydantic import BaseModel, Field

# Definición del esquema esperado de los datos del remito
class LineaItem(BaseModel):
    codigo: str = Field(None, description="Código de artículo del proveedor.")
    descripcion: str = Field(..., description="Descripción del producto.")
    cantidad: float = Field(..., description="Cantidad física entregada.")

class RemitoValidado(BaseModel):
    es_remito_valido: bool = Field(..., description="Bandera que indica si es un remito comercial legible.")
    numero_remito: str = Field(None, description="Número de remito en formato estándar.")
    razon_social_proveedor: str = Field(None, description="Nombre legal de la entidad emisora.")
    items: list[LineaItem] = Field(default_factory=list, description="Lista de artículos detallados.")

# Iniciar cliente
client = OpenAI(
    base_url="http://localhost:11434/v1",  # URL de Ollama (o el endpoint TLS en producción)
    api_key="ollama" # Token (ollama en local, token en producción)
)

# Al realizar la inferencia, se debe pasar num_ctx en las opciones (extra_body) para soportar tokens de visión:
# response = client.chat.completions.create(
#     model="qwen2.5vl:7b",
#     messages=[...],
#     response_format={"type": "json_object", "schema": RemitoValidado.model_json_schema()},
#     extra_body={"options": {"num_ctx": 16384}},
#     temperature=0.0
# )
```

---

## 4. Solución de Problemas (Troubleshooting) y Mantenimiento

### A. Error de Tamaño de Contexto (Context Size Limit)
* **Síntoma**: Mensajes del tipo `Error 400 - request exceeds the available context size`.
* **Causa**: Las imágenes de remitos con resoluciones nativas altas generan miles de parches visuales (tokens de visión). Ollama por defecto asigna una ventana de contexto de 2048 o 4096 tokens, lo que resulta en un desbordamiento.
* **Solución**: 
  1. Crear un modelo personalizado mediante un `Modelfile` que fije `PARAMETER num_ctx 16384` (el cual ya está creado en la raíz como `qwen2.5vl-large-ctx`).
  2. Ajustar la variable `VLM_NUM_CTX=16384` en el archivo `.env`.
  3. Redimensionar imágenes en memoria: El código del pipeline de Python redimensiona automáticamente las imágenes a una resolución máxima de 1280px en el lado mayor usando interpolación Lanczos. Esto reduce drásticamente los tokens a menos de 1000 sin comprometer la legibilidad del texto en el OCR.

### B. Control del Servicio de Ollama en Windows
Todas las siguientes tareas administrativas y de mantenimiento pueden realizarse de forma interactiva seleccionando la **Opción 7 (Gestionar Servicio Ollama)** en el menú principal de la aplicación (`main.py`). Si prefieres realizarlas por consola, los comandos correspondientes son:

#### Forzar Cierre del Servidor (Liberar Memoria GPU/RAM)
Si el procesamiento se congela debido a una saturación en la GPU o deseas limpiar la memoria física de procesos residuales, ejecuta en PowerShell:
```powershell
taskkill /f /im ollama.exe /im ollama_llama_server.exe /im python.exe
```

#### Revivir/Iniciar Ollama en Segundo Plano (Modo Silencioso)
Para levantar el servidor de Ollama directamente desde PowerShell sin que te bloquee la consola y sin levantar ventanas emergentes molestas, ejecuta:
```powershell
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
```
*(También puedes iniciarlo de forma convencional buscando el acceso directo de **Ollama** en el menú Inicio de Windows).*

