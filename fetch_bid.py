import requests
import pandas as pd
import os
from datetime import date

CACHE_DIR_BID = "cache_bid"

# Mapeo de indicadores del BID que nos interesan: resource_id -> nombre legible
INDICADORES_BID = {
    "ca1066c7-5bbd-4262-9d60-54506bc7a7ea": "balance_fiscal_bid",
    "cd916d59-3c77-4c71-90ea-d10a636a1d46": "inflacion_bid",
}


def obtener_indicador_bid(resource_id, nombre_indicador, paises_iso3=None):
    """
    Trae UN indicador completo del BID vía CKAN, filtrado a frecuencia anual
    y (opcionalmente) a una lista de países.
    """
    archivo_cache = os.path.join(CACHE_DIR_BID, f"{nombre_indicador}.csv")

    if os.path.exists(archivo_cache):
        fecha_modificacion = date.fromtimestamp(os.path.getmtime(archivo_cache))
        if fecha_modificacion == date.today():
            print(f"[cache] {nombre_indicador}")
            return pd.read_csv(archivo_cache)

    print(f"[API BID] {nombre_indicador}")
    url = "https://data.iadb.org/api/action/datastore_search"
    params = {"resource_id": resource_id, "limit": 5000}

    try:
        response = requests.get(url, params=params, timeout=15)
    except requests.exceptions.RequestException as e:
        print(f"  -> Error de conexión: {e}")
        return pd.DataFrame()

    if response.status_code != 200:
        print(f"  -> Error HTTP {response.status_code}")
        return pd.DataFrame()

    data = response.json()

    if not data.get("success") or "result" not in data:
        print(f"  -> Respuesta inesperada: {data}")
        return pd.DataFrame()

    registros_crudos = data["result"]["records"]

    registros = []
    for r in registros_crudos:
        if r.get("frequency") != "Annual":
            continue  # nos quedamos solo con datos anuales

        if paises_iso3 is not None and r["isoalpha3"] not in paises_iso3:
            continue  # filtramos solo los países que nos interesan

        try:
            valor = float(r["value"])
            anio = int(r["period"])
        except (ValueError, TypeError):
            continue  # si el valor o el año no son convertibles, saltamos ese registro

        registros.append({
            "pais": r["country"],
            "pais_iso3": r["isoalpha3"],
            "anio": anio,
            "valor": valor,
            "indicador": nombre_indicador
        })

    df = pd.DataFrame(registros)
    df = df.sort_values(["pais", "anio"]).reset_index(drop=True)

    os.makedirs(CACHE_DIR_BID, exist_ok=True)
    df.to_csv(archivo_cache, index=False)

    return df

def obtener_panel_bid(indicadores_bid, paises_iso3=None):
    dfs = []
    for resource_id, nombre in indicadores_bid.items():
        df = obtener_indicador_bid(resource_id, nombre, paises_iso3)
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


if __name__ == "__main__":
    from fetch_wb import PAISES  # reusamos la misma lista de países

    panel_bid = obtener_panel_bid(INDICADORES_BID, paises_iso3=set(PAISES.keys()))
    print(panel_bid.head(10))
    print(f"\nTotal filas: {len(panel_bid)}")
    print(f"Países: {sorted(panel_bid['pais_iso3'].unique())}")
    print(f"Años: {panel_bid['anio'].min()} - {panel_bid['anio'].max()}")


