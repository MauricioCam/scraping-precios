import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# -------------------
# 🔹 COOKIE de Hiper Olivos
# -------------------
COOKIE_SEGMENT = "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZWwiOiIxIiwicHJpY2VUYWJsZXMiOm51bGwsInJlZ2lvbklkIjpudWxsLCJ1dG1fY2FtcGFpZ24iOm51bGwsInV0bV9zb3VyY2UiOm51bGwsInV0bWlfY2FtcGFpZ24iOm51bGwsImN1cnJlbmN5Q29kZSI6IkFSUyIsImN1cnJlbmN5U3ltYm9sIjoiJCIsImNvdW50cnlDb2RlIjoiQVJHIiwiY3VsdHVyZUluZm8iOiJlcy1BUiIsImFkbWluX2N1bHR1cmVJbmZvIjoiZXMtQVIiLCJjaGFubmVsUHJpdmFjeSI6InB1YmxpYyJ9"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": f"vtex_segment={COOKIE_SEGMENT}"
}

# -------------------
# 🔹 Diccionario de productos (Nombre: productId)
# -------------------
productos = {
    "Oreo 3x354g": "715951",
    "Oreo 118g": "715949",
    "Oreo Golden 118g": "679211",
    "Pepitos 119g": "715953",
    "Pepitos Tripack 357g": "715954",
    "Lincoln Tripack 459g": "715956",
    "Lincoln 219g": "720550",
    "Terrabusi Mix Familiar 390g": "714816",
    "Terrabusi Mix Familiar 590g": "715957",
    "Cerealitas 212g": "720563",
    "Melba Rellena 120g": "553640",
    "Alfajor Terrabusi Triple 70g": "353214",
    "Alfajor Terrabusi Pack 6": "521104",
    "Alfajor Oreo Triple 56g": "680445",
    "Alfajor Milka Mousse 42g": "528728",
    "Alfajor Shot con Maní 60g": "353207",
    "Alfajor Pepitos Triple 57g": "569707",
    "Alfajor Triple Milka Oreo 61g": "667747",
    "Milka con leche 55g": "628578",
    "Cadbury Frutilla 82g": "680432",
    "Milka Aireado 110g": "680427",
    "Shot Maní 90g": "41397",
    "Shot Maní 35g": "42840",
    "Beldent Menta 20g": "670219",
    "Tang Naranja 15g": "711449",
    "Verão Naranja 7g": "711446",
    "Gelatina Frutilla 25g": "714815",
    "Gelatina Cereza 25g": "714811",
    "Gelatina Frutos Rojos 25g": "714814",
    "Mousse Royal Chocolate 65g": "716932",
    "Postre Royal Vainilla 75g": "716922",
    "Flan Royal Vainilla 60g": "716929",
    "Gelatina Royal Frambuesa 25g": "714809",
    "Gelatina sin sabor Royal 14g": "662143",
    "Gelatina Royal Frutilla 25g": "714808"
}

# -------------------
# 🔹 Streamlit UI
# -------------------
st.title("📊 Precios Carrefour - API (Sucursal Hiper Olivos)")
st.write("Obtiene los precios de los productos listados directamente desde la API de Carrefour, aplicando la cookie de **Hiper Olivos**.")

if st.button("🔍 Ejecutar scraping"):
    resultados = []

    for nombre, product_id in productos.items():
        try:
            url = f"https://www.carrefour.com.ar/api/catalog_system/pub/products/search?fq=productId:{product_id}"
            r = requests.get(url, headers=HEADERS, timeout=10)
            data = r.json()

            if not data:
                resultados.append({"productId": product_id, "Nombre": nombre, "Precio": "Revisar"})
                continue

            offer = data[0]['items'][0]['sellers'][0]['commertialOffer']
            price_list = offer.get('ListPrice', 0)
            price = offer.get('Price', 0)

            # Preferimos precio de lista si existe, sino precio actual
            final_price = price_list if price_list > 0 else price

            if final_price > 0:
                precio_formateado = f"{final_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", "")
                resultados.append({"productId": product_id, "Nombre": nombre, "Precio": precio_formateado})
            else:
                resultados.append({"productId": product_id, "Nombre": nombre, "Precio": "Revisar"})

        except Exception:
            resultados.append({"productId": product_id, "Nombre": nombre, "Precio": "Revisar"})

    # --- Crear DataFrame y mostrarlo
    df = pd.DataFrame(resultados, columns=["productId", "Nombre", "Precio"])
    st.success("✅ Scraping completado vía API")
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
