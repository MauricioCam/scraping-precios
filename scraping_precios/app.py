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

# ===========================
# 🎨 INTERFAZ STREAMLIT
# ===========================
st.title("📊 Relevamiento Precios Carrefour")
st.write("Relevamiento automático de todos los SKUs, aplicando la sucursal **Hiper Olivos**.")

if st.button("🔍 Ejecutar relevamiento"):
    with st.spinner("⏳ Relevando... Esto puede tardar unos 2 minutos"):
        resultados = []

        for nombre, datos in productos.items():
            ean = datos["ean"]
            product_id = datos["productId"]

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
                    precio_formateado = f"{final_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", "")
                    resultados.append({"EAN": ean, "Nombre": nombre, "Precio": precio_formateado})
                else:
                    resultados.append({"EAN": ean, "Nombre": nombre, "Precio": "no hay stock"})

            except Exception:
                resultados.append({"EAN": ean, "Nombre": nombre, "Precio": "Revisar"})

        # --- Crear DataFrame y mostrarlo
        df = pd.DataFrame(resultados, columns=["EAN", "Nombre", "Precio"])
        st.success("✅ Relevamiento completado (se puede copiar y pegar en excel o descargar en csv con el botón de más abajo)")
        st.dataframe(df)

        # --- Botón de descarga CSV
        fecha = datetime.now().strftime("%Y-%m-%d")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇ Descargar CSV",
            data=csv,
            file_name=f"precios_hiper_olivos_{fecha}.csv",
            mime="text/csv",
        )
