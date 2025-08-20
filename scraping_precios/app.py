# app.py
import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# ===========================
# 📥 IMPORTAR EL DICCIONARIO
# ===========================
from productos_streamlit import productos

# ===========================
# 🔹 COOKIE de Hiper Olivos
# ===========================
COOKIE_SEGMENT = "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZWwiOiIxIiwicHJpY2VUYWJsZXMiOm51bGwsInJlZ2lvbklkIjpudWxsLCJ1dG1fY2FtcGFpZ24iOm51bGwsInV0bV9zb3VyY2UiOm51bGwsInV0bWlfY2FtcGFpZ24iOm51bGwsImN1cnJlbmN5Q29kZSI6IkFSUyIsImN1cnJlbmN5U3ltYm9sIjoiJCIsImNvdW50cnlDb2RlIjoiQVJHIiwiY3VsdHVyZUluZm8iOiJlcy1BUiIsImFkbWluX2N1dHR1cmVJbmZvIjoiZXMtQVIiLCJjaGFubmVsUHJpdmFjeSI6InB1YmxpYyJ9"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": f"vtex_segment={COOKIE_SEGMENT}"
}

def format_ar_price_no_thousands(value):
    """1795.0 -> '1795,00' (sin separador de miles)."""
    if value is None:
        return None
    return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", "")

# ===========================
# 🎨 INTERFAZ STREAMLIT
# ===========================
st.set_page_config(page_title="📊 Precios Carrefour", layout="wide")

# ------ Menú lateral (sin page_link) ------
with st.sidebar:
    st.header("Menú")
    st.button("Carrefour", disabled=True)
    open_coto = st.button("Ir a Coto ▶")
    if open_coto:
        try:
            st.switch_page("pages/coto.py")  # requiere Streamlit reciente
        except Exception:
            st.info("Usa el selector de páginas en la barra lateral para abrir **Coto**.")

st.title("📊 Relevamiento Precios Carrefour")
st.write("Relevamiento automático de todos los SKUs, aplicando la sucursal **Hiper Olivos**.")

if st.button("🔍 Ejecutar relevamiento"):
    with st.spinner("⏳ Relevando... Esto puede tardar unos 2 minutos"):
        resultados = []

        for nombre, datos in productos.items():
            ean = datos.get("ean")
            product_id = datos.get("productId")

            try:
                url = f"https://www.carrefour.com.ar/api/catalog_system/pub/products/search?fq=productId:{product_id}"
                r = requests.get(url, headers=HEADERS, timeout=10)
                data = r.json()

                if not data:
                    resultados.append({"EAN": ean, "Nombre": nombre, "Precio": "Revisar"})
                    continue

                offer = data[0]['items'][0]['sellers'][0]['commertialOffer']
                price_list = offer.get('ListPrice', 0)
                price = offer.get('Price', 0)
                final_price = price_list if price_list > 0 else price

                if final_price > 0:
                    precio_formateado = format_ar_price_no_thousands(final_price)
                    resultados.append({"EAN": ean, "Nombre": nombre, "Precio": precio_formateado})
                else:
                    resultados.append({"EAN": ean, "Nombre": nombre, "Precio": "Revisar"})

            except Exception:
                resultados.append({"EAN": ean, "Nombre": nombre, "Precio": "Revisar"})

        # --- Crear DataFrame y mostrarlo
        df = pd.DataFrame(resultados, columns=["EAN", "Nombre", "Precio"])
        st.success("✅ Relevamiento completado")
        st.dataframe(df, use_container_width=True)

        # --- Botón de descarga CSV
        fecha = datetime.now().strftime("%Y-%m-%d")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇ Descargar CSV",
            data=csv,
            file_name=f"precios_carrefour_{fecha}.csv",
            mime="text/csv",
        )
