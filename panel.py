import pandas as pd
from fetch_wb import obtener_panel_completo, PAISES, INDICADORES
from fetch_bid import obtener_panel_bid, INDICADORES_BID


def obtener_panel_combinado():
    """
    Junta los datos del Banco Mundial y del BID en un solo DataFrame,
    con el mismo formato de columnas para ambas fuentes.
    """
    panel_wb = obtener_panel_completo(PAISES, INDICADORES)
    panel_wb["fuente"] = "Banco Mundial"

    panel_bid = obtener_panel_bid(INDICADORES_BID, paises_iso3=set(PAISES.keys()))
    panel_bid["fuente"] = "BID"

    panel = pd.concat([panel_wb, panel_bid], ignore_index=True)
    return panel


if __name__ == "__main__":
    panel = obtener_panel_combinado()
    print(panel["indicador"].unique())
    print(f"\nTotal filas: {len(panel)}")
    print(panel.groupby("fuente").size())