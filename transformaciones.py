def normalizar_a_variacion(tabla, anio_base=None):
    """
    Convierte una tabla de valores absolutos en % de variación respecto al año base.
    Si no se especifica anio_base, usa el primer año disponible.
    """
    if anio_base is None:
        anio_base = tabla.index.min()

    valores_base = tabla.loc[anio_base]
    variacion = (tabla / valores_base - 1) * 100
    return variacion