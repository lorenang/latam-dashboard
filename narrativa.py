import os
import hashlib
import pandas as pd
from dotenv import load_dotenv
from anthropic import Anthropic
from panel import obtener_panel_combinado

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
CACHE_DIR_NARRATIVA = "cache_narrativa"


def generar_resumen(prompt):
    mensaje = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return mensaje.content[0].text


def tabla_a_texto(panel, nombre_indicador):
    datos = panel[panel["indicador"] == nombre_indicador]
    tabla = datos.pivot(index="anio", columns="pais", values="valor").round(1)
    return tabla.to_string()

def generar_resumen_economico(panel, forzar_regenerar=False, cambios=None):
    texto_pib = tabla_a_texto(panel, "crecimiento_pib")
    texto_inflacion = tabla_a_texto(panel, "inflacion")

    seccion_cambios = ""
    if cambios:
        seccion_cambios = f"""

CAMBIOS DESDE LA ÚLTIMA ACTUALIZACIÓN:
{cambios}

Si hay cambios relevantes, mencionalos brevemente al final del resumen bajo un subtítulo "Novedades de esta semana"."""

    prompt = f"""Sos un analista económico especializado en América Latina. 
...(el resto del prompt igual que antes)...

No repitas los números tal cual aparecen en la tabla — interpretalos.{seccion_cambios}"""

    # el resto de la función sigue igual (cache, llamada a la API, etc.)

def generar_resumen_economico(panel, forzar_regenerar=False, cambios=None):
    texto_pib = tabla_a_texto(panel, "crecimiento_pib")
    texto_inflacion = tabla_a_texto(panel, "inflacion")

    seccion_cambios = ""
    if cambios:
            seccion_cambios = f"""
                CAMBIOS DESDE LA ÚLTIMA ACTUALIZACIÓN:
                {cambios}
                
                Si hay cambios relevantes, mencionalos brevemente al final del resumen bajo un subtítulo "Novedades de esta semana"."""
                

    prompt = f"""Sos un analista económico especializado en América Latina. 
            Te paso dos tablas con datos del Banco Mundial: crecimiento del PIB (% anual) 
            e inflación (% anual) para 6 países entre 2015 y 2025.

            CRECIMIENTO DEL PIB (%):
            {texto_pib}

            INFLACIÓN (%):
            {texto_inflacion}

            Escribí un resumen ejecutivo de máximo 200 palabras que:
            1. Identifique el país con la trayectoria más volátil y por qué
            2. Señale qué país tuvo el desempeño más estable
            3. Mencione cualquier patrón regional compartido (ej: el shock de 2020)
            4. Use un tono profesional pero directo, como para un brief de inversores
            5. Si hay datos de inflación de dos fuentes distintas (Banco Mundial y BID) que difieren, mencionalo brevemente como nota de calidad de datos

            No repitas los números tal cual aparecen en la tabla — interpretalos.{seccion_cambios}"""

    hash_prompt = hashlib.md5(prompt.encode()).hexdigest()[:10]
    archivo_cache = os.path.join(CACHE_DIR_NARRATIVA, f"resumen_{hash_prompt}.txt")

    if not forzar_regenerar and os.path.exists(archivo_cache):
        print("[cache] resumen económico")
        with open(archivo_cache, "r") as f:
            return f.read()

    print("[API Claude] generando resumen nuevo")
    resumen = generar_resumen(prompt)

    os.makedirs(CACHE_DIR_NARRATIVA, exist_ok=True)
    with open(archivo_cache, "w") as f:
        f.write(resumen)

    return resumen


if __name__ == "__main__":
    panel = obtener_panel_combinado()
    resumen = generar_resumen_economico(panel)
    print(resumen)