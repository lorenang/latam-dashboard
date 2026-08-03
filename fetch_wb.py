import requests
import pandas as pd
import os
from datetime import date

PAISES = {
    "ARG": "Argentina",
    "BRA": "Brasil",
    "CHL": "Chile",
    "COL": "Colombia",
    "MEX": "México",
    "PER": "Perú",
}


INDICADORES = {
    "NY.GDP.MKTP.KD.ZG": "crecimiento_pib",
    "FP.CPI.TOTL.ZG": "inflacion",
    "GC.DOD.TOTL.GD.ZS": "deuda_publica",
    "PA.NUS.FCRF": "tipo_cambio",
}
CACHE_DIR = "cache"


import time

def obtener_indicador(pais_iso3, indicador, desde=2015, hasta=2026, intentos=3):
    archivo_cache = os.path.join(CACHE_DIR, f"{pais_iso3}_{indicador}.csv")

    if os.path.exists(archivo_cache):
        fecha_modificacion = date.fromtimestamp(os.path.getmtime(archivo_cache))
        if fecha_modificacion == date.today():
            print(f"[cache] {pais_iso3} - {indicador}")
            return pd.read_csv(archivo_cache)

    url = f"https://api.worldbank.org/v2/country/{pais_iso3}/indicator/{indicador}"
    params = {"format": "json", "date": f"{desde}:{hasta}", "per_page": 100}

    response = None
    for intento in range(1, intentos + 1):
        print(f"[API] {pais_iso3} - {indicador} (intento {intento}/{intentos})")
        try:
            response = requests.get(url, params=params, timeout=10)
            break  # si llegamos acá, funcionó -> salimos del loop de reintentos
        except requests.exceptions.Timeout:
            print(f"  -> Timeout, reintentando en {intento * 2}s...")
            time.sleep(intento * 2)  # espera creciente: 2s, 4s, 6s...
        except requests.exceptions.RequestException as e:
            print(f"  -> Error de conexión: {e}")
            return pd.DataFrame()

    if response is None:
        print(f"  -> Falló tras {intentos} intentos para {pais_iso3} - {indicador}")
        return pd.DataFrame()

    if response.status_code != 200:
        print(f"  -> Error HTTP {response.status_code} para {pais_iso3}: {response.text[:200]}")
        return pd.DataFrame()

    data = response.json()

    if not isinstance(data, list) or len(data) < 2:
        print(f"  -> Respuesta inesperada para {pais_iso3}-{indicador}: {data}")
        return pd.DataFrame()

    if data[1] is None:
        print(f"  -> Sin datos para {pais_iso3} - {indicador}")
        return pd.DataFrame()

    registros = []
    for fila in data[1]:
        registros.append({
            "pais": fila["country"]["value"],
            "pais_iso3": fila["countryiso3code"],
            "anio": int(fila["date"]),
            "valor": fila["value"]
        })

    df = pd.DataFrame(registros)
    df = df.sort_values("anio").reset_index(drop=True)

    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_csv(archivo_cache, index=False)

    return df


def obtener_indicador_multi_pais(paises_iso3, indicador, desde=2015, hasta=2026):
    """
    Trae el mismo indicador para varios países y los junta en un solo DataFrame.
    """
    dfs = []
    for iso3 in paises_iso3:
        df_pais = obtener_indicador(iso3, indicador, desde, hasta)
        dfs.append(df_pais)

    return pd.concat(dfs, ignore_index=True)

def obtener_panel_completo(paises, indicadores, desde=2015, hasta=2026):
    dfs = []
    for codigo_indicador, nombre_legible in indicadores.items():
        df = obtener_indicador_multi_pais(paises.keys(), codigo_indicador, desde, hasta)
        df["indicador"] = nombre_legible
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


if __name__ == "__main__":
    panel = obtener_panel_completo(PAISES, INDICADORES)
    print(panel.head(10))
    print(f"\nTotal de filas: {len(panel)}")
    print(f"Indicadores obtenidos: {panel['indicador'].unique()}")