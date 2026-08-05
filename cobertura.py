import pandas as pd
from panel import obtener_panel_combinado

if __name__ == "__main__":
    panel = obtener_panel_combinado()

    # Contamos cuántos años de datos tiene cada combinación país x indicador
    matriz = panel.groupby(["pais_iso3", "indicador"]).size().unstack(fill_value=0)

    print("Matriz de cobertura (cantidad de años con datos):\n")
    print(matriz)

    print("\n--- Países con algún indicador completamente vacío ---")
    for pais in matriz.index:
        vacios = matriz.columns[matriz.loc[pais] == 0].tolist()
        if vacios:
            print(f"{pais}: sin datos en {vacios}")