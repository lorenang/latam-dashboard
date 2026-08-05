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
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}]
    )
    return mensaje.content[0].text


def tabla_a_texto(panel, nombre_indicador):
    datos = panel[panel["indicador"] == nombre_indicador]
    tabla = datos.pivot(index="anio", columns="pais", values="valor").round(1)
    return tabla.to_string()


def armar_seccion_todos_los_indicadores(panel):
    """
    Genera un bloque de texto con la tabla de CADA indicador presente en el panel,
    para que Claude vea todas las fuentes, no solo PIB e inflación del Banco Mundial.
    """
    bloques = []
    for indicador in sorted(panel["indicador"].unique()):
        datos = panel[panel["indicador"] == indicador]

        # DEBUG: detectamos si hay filas duplicadas por (año, país) antes de pivotear
        duplicados = datos.duplicated(subset=["anio", "pais"], keep=False)
        if duplicados.any():
            print(f"⚠️  {indicador} tiene {duplicados.sum()} filas duplicadas por (año, país)")
            print(datos[duplicados].sort_values(["pais", "anio"]).head(10))
            continue  # saltamos este indicador por ahora, para no crashear

        texto_tabla = tabla_a_texto(panel, indicador)
        bloques.append(f"### {indicador.upper()}\n{texto_tabla}")

    return "\n\n".join(bloques)


def generar_resumen_economico(panel, forzar_regenerar=False, cambios=None):
    seccion_indicadores = armar_seccion_todos_los_indicadores(panel)

    seccion_cambios = ""
    if cambios:
        seccion_cambios = f"""

            CAMBIOS DESDE LA ÚLTIMA ACTUALIZACIÓN:
            {cambios}

            Si hay cambios relevantes, mencionalos brevemente al final del resumen bajo un subtítulo "Novedades de esta semana"."""

    prompt = f"""Sos un analista económico especializado en América Latina. 
            Te paso datos de tres fuentes distintas (Banco Mundial, BID y CEPAL) para 6 países,
            cubriendo crecimiento del PIB, inflación, deuda pública, balance fiscal y tipo de cambio.
            Nota: algunos indicadores como inflación y tipo de cambio están duplicados entre fuentes
            (por ejemplo "inflacion" es del Banco Mundial, "inflacion_bid" es del BID, "inflacion_cepal" es de CEPAL)
            — esto es intencional, para que puedas contrastarlos.

            {seccion_indicadores}

            Escribí un resumen ejecutivo de máximo 300 palabras que:
            1. Identifique el país con la trayectoria más volátil y por qué
            2. Señale qué país tuvo el desempeño más estable
            3. Mencione cualquier patrón regional compartido (ej: el shock de 2020)
            4. Comente brevemente el estado del balance/deuda fiscal de los países con datos disponibles
            5. Si las distintas fuentes de inflación o tipo de cambio difieren notablemente entre sí para algún país, mencionalo como nota de calidad de datos
            6. Use un tono profesional pero directo, como para un brief de inversores
            7. No uses un título con # al principio (ya hay un título en la página). Usá **negrita** para los subtítulos de cada sección, no headers con # ni ##.
            8. Si algún país tiene datos muy limitados o ausentes en ciertos indicadores (por ejemplo, series muy cortas o vacías), no hagas afirmaciones fuertes sobre ese país en esas dimensiones — mencioná la limitación de datos en vez de inventar una conclusión.
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