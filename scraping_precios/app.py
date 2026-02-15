import streamlit as st

st.set_page_config(
    page_title="Scraping de Precios",
    layout="wide"
)

st.title("📊 Scraping de Precios")
st.markdown(
    """
    Bienvenido al panel de análisis.

    Utilizá el menú lateral para navegar entre las secciones:
    - **Relevamiento Diario**
    - **Dinámicas**
    - **Mercado**
    """
)

st.divider()

st.subheader("📌 Secciones disponibles")

st.markdown(
    """
    🔹 **Relevamiento Diario**  
    Consulta diaria de precios por cadena y producto.

    🔹 **Dinámicas**  
    Análisis de variaciones, tendencias y comportamiento de precios.

    🔹 **Mercado**  
    Vista consolidada del mercado por EAN / categoría.
    """
)

st.info("⬅️ Usá el menú lateral para acceder a cada página")
