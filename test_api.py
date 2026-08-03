import os
from dotenv import load_dotenv

load_dotenv()  # lee el archivo .env y carga sus variables

api_key = os.getenv("ANTHROPIC_API_KEY")

if api_key:
    print(f"Key cargada correctamente: {api_key[:12]}...")  # solo mostramos el inicio, por seguridad
else:
    print("No se encontró la key. Revisá el archivo .env")