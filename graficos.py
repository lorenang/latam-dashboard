import matplotlib.pyplot as plt
from fetch_wb import obtener_panel_completo, PAISES, INDICADORES


def graficar_indicador(panel, nombre_indicador, titulo, ylabel):
    """
    Grafica un indicador como líneas comparativas por país.
    """
    datos = panel[panel["indicador"] == nombre_indicador]
    tabla = datos.pivot(index="anio", columns="pais", values="valor")

    fig, ax = plt.subplots(figsize=(10, 6))
    tabla.plot(ax=ax, marker="o")

    ax.set_title(titulo)
    ax.set_xlabel("Año")
    ax.set_ylabel(ylabel)
    ax.legend(title="País", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{nombre_indicador}.png", dpi=150)
    print(f"Guardado: {nombre_indicador}.png")


if __name__ == "__main__":
    panel = obtener_panel_completo(PAISES, INDICADORES)

    graficar_indicador(panel, "crecimiento_pib", "Crecimiento del PIB en América Latina", "% anual")
    graficar_indicador(panel, "inflacion", "Inflación en América Latina", "% anual")