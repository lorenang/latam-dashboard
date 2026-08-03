import streamlit as st
from panel import obtener_panel_combinado
from narrativa import generar_resumen_economico
from transformaciones import normalizar_a_variacion

st.set_page_config(page_title="Panel Macro LatAm", layout="wide")

st.title("📊 Panel Macroeconómico — América Latina")
st.caption("Datos: Banco Mundial · BID · CEPAL | Actualizado con IA generativa")


# --- Funciones cacheadas (van ARRIBA, antes de usarlas) ---
@st.cache_data(ttl=3600)
def cargar_panel():
    return obtener_panel_combinado()

@st.cache_data(ttl=3600)
def cargar_resumen(panel):
    return generar_resumen_economico(panel)


# --- Carga de datos, usando las versiones cacheadas ---
with st.spinner("Cargando datos..."):
    panel = cargar_panel()

# --- Sección 1: Resumen ejecutivo con IA ---
st.header("Resumen ejecutivo")
with st.spinner("Generando análisis..."):
    resumen = cargar_resumen(panel)
st.markdown(resumen)

# --- Sección 2: PIB e inflación ---
st.header("Indicadores")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Crecimiento del PIB (%)")
    datos_pib = panel[panel["indicador"] == "crecimiento_pib"]
    tabla_pib = datos_pib.pivot(index="anio", columns="pais", values="valor")
    st.line_chart(tabla_pib)

with col2:
    st.subheader("Inflación (%)")
    datos_inflacion = panel[panel["indicador"] == "inflacion"]
    tabla_inflacion = datos_inflacion.pivot(index="anio", columns="pais", values="valor")
    st.line_chart(tabla_inflacion)

# --- Sección 3: Tipo de cambio ---
st.header("Tipo de cambio")

datos_tc = panel[panel["indicador"] == "tipo_cambio"]

if datos_tc.empty:
    st.warning("⚠️ No se pudieron obtener datos de tipo de cambio en este momento. Probá recargar más tarde.")
else:
    tabla_tc = datos_tc.pivot(index="anio", columns="pais", values="valor")

    vista = st.radio(
        "¿Cómo querés verlo?",
        ["Variación % (todos los países)", "Valor absoluto (un país)"],
        horizontal=True
    )

    if vista == "Variación % (todos los países)":
        tabla_variacion = normalizar_a_variacion(tabla_tc)
        st.line_chart(tabla_variacion)
        st.caption(f"Variación % respecto a {tabla_tc.index.min()}")
    else:
        pais_elegido = st.selectbox("Elegí un país", tabla_tc.columns)
        st.line_chart(tabla_tc[[pais_elegido]])
        st.caption(f"Tipo de cambio nominal — {pais_elegido}")

# --- Sección 4: Datos crudos ---
with st.expander("Ver datos completos"):
    st.dataframe(panel)