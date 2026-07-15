import os
from dotenv import load_dotenv
from openai import OpenAI

def main():
    # 1. Cargar variables de entorno del archivo .env
    load_dotenv()
    
    api_url = os.getenv("VLM_API_URL", "http://localhost:11434/v1")
    api_key = os.getenv("VLM_API_KEY", "ollama")
    model_name = os.getenv("VLM_MODEL", "qwen2.5vl:7b")

    
    print("=== Test de Conexión con VLM Local ===")
    print(f"URL de la API: {api_url}")
    print(f"Modelo configurado: {model_name}")
    print("--------------------------------------")
    
    # 2. Inicializar el cliente compatible con OpenAI
    try:
        client = OpenAI(
            base_url=api_url,
            api_key=api_key
        )
    except Exception as e:
        print(f"Error al inicializar el cliente OpenAI: {e}")
        return

    # 3. Realizar consulta simple (chat completion) sin imagen primero
    print("Enviando consulta de prueba de texto al modelo...")
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": "Responde con una sola palabra: 'OK' si recibes este mensaje."}
            ],
            temperature=0.0
        )
        respuesta = response.choices[0].message.content.strip()
        print(f"Respuesta del modelo: '{respuesta}'")
        
        if "OK" in respuesta.upper():
            print("\n[ÉXITO] La conexión con Ollama y el modelo Qwen2.5-VL está funcionando correctamente.")
        else:
            print("\n[ADVERTENCIA] El modelo respondió, pero la respuesta no fue la esperada. Respuesta completa:")
            print(respuesta)
            
    except Exception as e:
        print("\n[ERROR] No se pudo conectar con Ollama o el modelo no está disponible.")
        print("Detalle del error:")
        print(e)
        print("\nPor favor, verifica lo siguiente:")
        print("1. ¿Ollama se encuentra ejecutándose en tu bandeja del sistema?")
        print(f"2. ¿Has descargado el modelo ejecutando 'ollama run {model_name}' en PowerShell?")
        print("3. ¿El puerto o la dirección en VLM_API_URL en tu archivo .env es correcto?")

if __name__ == "__main__":
    main()
