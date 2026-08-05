import streamlit as st
from panel import obtener_panel_combinado
from narrativa import generar_resumen_economico
from transformaciones import normalizar_a_variacion

st.set_page_config(page_title="Panel Macro LatAm", layout="wide")

st.markdown("""
<style>
    /* Limita el tamaño de los headers que pueda generar el markdown de la narrativa */
    .stMarkdown h1 { font-size: 1.4rem !important; }
    .stMarkdown h2 { font-size: 1.2rem !important; }
    .stMarkdown h3 { font-size: 1.05rem !important; }
</style>
""", unsafe_allow_html=True)

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


# --- Sección 0: KPIs destacados ---
def ultimo_valor_por_pais(panel, indicador):
    """Devuelve el valor más reciente disponible de un indicador, por país."""
    datos = panel[panel["indicador"] == indicador].dropna(subset=["valor"])
    if datos.empty:
        return {}
    idx_ultimo_anio = datos.groupby("pais_iso3")["anio"].idxmax()
    ultimos = datos.loc[idx_ultimo_anio]
    return dict(zip(ultimos["pais_iso3"], ultimos["valor"]))

crecimiento_actual = ultimo_valor_por_pais(panel, "crecimiento_pib")
inflacion_actual = ultimo_valor_por_pais(panel, "inflacion")


st.markdown("#### Vista rápida — último dato disponible por país")
cols = st.columns(len(crecimiento_actual))
for i, (pais, valor) in enumerate(sorted(crecimiento_actual.items())):
    with cols[i]:
        inflacion_pais = inflacion_actual.get(pais)
        delta_texto = f"Inflación: {inflacion_pais:.1f}%" if inflacion_pais is not None else None
        st.metric(label=pais, value=f"{valor:.1f}%", delta=delta_texto, delta_color="inverse")

st.divider()

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

# --- Sección: Cobertura de datos ---
with st.expander("ℹ️ Cobertura de datos por país"):
    st.caption("Cantidad de años con datos disponibles por indicador. Los huecos reflejan limitaciones reales de las fuentes, no errores del panel.")

    matriz_cobertura = panel.groupby(["pais_iso3", "indicador"]).size().unstack(fill_value=0)
    st.dataframe(matriz_cobertura, use_container_width=True)

    st.markdown("""
    **Notas conocidas:**
    - Ecuador no tiene series de tipo de cambio propio en CEPAL porque su economía está dolarizada desde 2000.
    - Venezuela presenta los mayores huecos de cobertura en balance fiscal, inflación (BID) y tipo de cambio (CEPAL), 
      consistente con limitaciones conocidas en la publicación de estadísticas oficiales del país en los últimos años.
    """)

# --- Sección 4: Datos crudos ---
with st.expander("Ver datos completos"):
    st.dataframe(panel)