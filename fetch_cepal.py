import requests
import pandas as pd
import os
from datetime import date

CACHE_DIR_CEPAL = "cache_cepal"

INDICADORES_CEPAL = {
    4544: "inflacion_cepal",
    2179: "tipo_cambio_cepal",
}


def obtener_indicador_cepal(indicator_id, nombre_indicador, paises_iso3=None):
    archivo_cache = os.path.join(CACHE_DIR_CEPAL, f"{nombre_indicador}.csv")

    if os.path.exists(archivo_cache):
        fecha_modificacion = date.fromtimestamp(os.path.getmtime(archivo_cache))
        if fecha_modificacion == date.today():
            print(f"[cache] {nombre_indicador}")
            return pd.read_csv(archivo_cache)

    print(f"[API CEPAL] {nombre_indicador}")
    url = f"https://api-cepalstat.cepal.org/cepalstat/api/v1/indicator/{indicator_id}/data"
    params = {"format": "json", "lang": "es"}

    try:
        response = requests.get(url, params=params, timeout=20)
    except requests.exceptions.RequestException as e:
        print(f"  -> Error de conexión: {e}")
        return pd.DataFrame()

    if response.status_code != 200:
        print(f"  -> Error HTTP {response.status_code}")
        return pd.DataFrame()

    data = response.json()

    if "body" not in data or "data" not in data["body"]:
        print(f"  -> Respuesta inesperada: {data}")
        return pd.DataFrame()

    registros_crudos = data["body"]["data"]
    dimensiones = data["body"]["dimensions"]

    # Buscamos la dimensión de años por nombre, no por ID fijo
    dim_anios = next((d for d in dimensiones if "año" in d["name"].lower()), None)

    if dim_anios is None:
        print(f"  -> No se encontró dimensión de años para {nombre_indicador}")
        return pd.DataFrame()

    campo_anio = f"dim_{dim_anios['id']}"
    lookup_anios = {m["id"]: m["name"] for m in dim_anios["members"]}

    registros = []
    for r in registros_crudos:
        if paises_iso3 is not None and r.get("iso3") not in paises_iso3:
            continue

        id_anio = r.get(campo_anio)
        if id_anio not in lookup_anios:
            continue  # registro sin año reconocible, lo saltamos

        try:
            anio = int(lookup_anios[id_anio])
            valor = float(r["value"])
        except (ValueError, TypeError):
            continue

        registros.append({
            "pais": r["iso3"],  # CEPAL no nos da el nombre completo, solo el código
            "pais_iso3": r["iso3"],
            "anio": anio,
            "valor": valor,
            "indicador": nombre_indicador
        })

    df = pd.DataFrame(registros)
    df = df.sort_values(["pais_iso3", "anio"]).reset_index(drop=True)

    os.makedirs(CACHE_DIR_CEPAL, exist_ok=True)
    df.to_csv(archivo_cache, index=False)

    return df


def obtener_panel_cepal(indicadores_cepal, paises_iso3=None):
    dfs = []
    for indicator_id, nombre in indicadores_cepal.items():
        df = obtener_indicador_cepal(indicator_id, nombre, paises_iso3)
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


if __name__ == "__main__":
    from fetch_wb import PAISES

    panel_cepal = obtener_panel_cepal(INDICADORES_CEPAL, paises_iso3=set(PAISES.keys()))
    print(panel_cepal.head(10))
    print(f"\nTotal filas: {len(panel_cepal)}")
    print(f"Países: {sorted(panel_cepal['pais_iso3'].unique())}")
    print(panel_cepal.groupby('indicador').size())