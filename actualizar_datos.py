import pandas as pd
import os
from panel import obtener_panel_combinado
from narrativa import generar_resumen_economico

SNAPSHOT_ACTUAL = "snapshot_actual.csv"


def detectar_cambios(panel_nuevo):
    if not os.path.exists(SNAPSHOT_ACTUAL):
        return None

    panel_anterior = pd.read_csv(SNAPSHOT_ACTUAL)

    clave = ["pais_iso3", "anio", "indicador"]
    merge = panel_nuevo.merge(
        panel_anterior, on=clave, how="outer", suffixes=("_nuevo", "_anterior"), indicator=True
    )

    solo_nuevos = merge[merge["_merge"] == "left_only"]
    ambos_nan = merge["valor_nuevo"].isna() & merge["valor_anterior"].isna()

    revisiones = merge[
        (merge["_merge"] == "both") &
        (~ambos_nan) &
        (merge["valor_nuevo"].round(2) != merge["valor_anterior"].round(2))
    ]

    partes = []
    if len(solo_nuevos) > 0:
        partes.append(f"{len(solo_nuevos)} datos nuevos que antes no estaban disponibles")
    if len(revisiones) > 0:
        ejemplos = revisiones[["pais_iso3", "anio", "indicador", "valor_anterior", "valor_nuevo"]].head(5)
        partes.append(f"{len(revisiones)} valores revisados, por ejemplo:\n{ejemplos.to_string(index=False)}")

    if not partes:
        return "Sin cambios respecto a la corrida anterior."

    return "\n".join(partes)


if __name__ == "__main__":
    print("Actualizando panel de datos...")
    panel = obtener_panel_combinado()

    cambios = detectar_cambios(panel)

    panel.to_csv(SNAPSHOT_ACTUAL, index=False)

    print("Generando narrativa...")
    resumen = generar_resumen_economico(panel, forzar_regenerar=True, cambios=cambios)

    print("Listo. Resumen actualizado:")
    print(resumen)