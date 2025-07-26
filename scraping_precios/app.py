import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# -------------------
# 🔹 COOKIE de Hiper Olivos (Carrefour)
# -------------------
COOKIE_CARREFOUR = "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZWwiOiIxIiwicHJpY2VUYWJsZXMiOm51bGwsInJlZ2lvbklkIjpudWxsLCJ1dG1fY2FtcGFpZ24iOm51bGwsInV0bV9zb3VyY2UiOm51bGwsInV0bWlfY2FtcGFpZ24iOm51bGwsImN1cnJlbmN5Q29kZSI6IkFSUyIsImN1cnJlbmN5U3ltYm9sIjoiJCIsImNvdW50cnlDb2RlIjoiQVJHIiwiY3VsdHVyZUluZm8iOiJlcy1BUiIsImFkbWluX2N1bHR1cmVJbmZvIjoiZXMtQVIiLCJjaGFubmVsUHJpdmFjeSI6InB1YmxpYyJ9"

HEADERS_CARREFOUR = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": f"vtex_segment={COOKIE_CARREFOUR}"
}

HEADERS_DIA = {
    "User-Agent": "Mozilla/5.0"
}

# -------------------
# 🔹 Diccionario de productos Carrefour (Nombre: productId)
# -------------------
productos_carrefour = {
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
# 🔹 Diccionario de productos Día (Nombre: productId)
# -------------------
productos_dia = {
    "Oreo 3x354g": "271630",
    "Oreo Golden 118g": "283177",
    "Pepitos 119g": "271628",
    "Pepitos Tripack 357g": "271632",
    "Lincoln Tripack 459g": "170177",
    "Terrabusi Mix Familiar 390g": "284571",
    "Terrabusi Mix Familiar 590g": "284655",
    "Cerealitas 212g": "147689",
    "Melba Rellena 120g": "73264",
    "Melba 360g": "52289",
    "Alfajor Terrabusi Triple 70g": "23423",
    "Alfajor Oreo Triple 56g": "274632",
    "Alfajor Shot con Maní 60g": "23431",
    "Alfajor Pepitos Triple 57g": "23430",
    "Alfajor Triple Milka Oreo 61g": "182539",
    "Milka con leche 55g": "249906",
    "Shot Maní 90g": "168862",
    "Shot Maní 35g": "110388",
    "Beldent Menta 20g": "269579",
    "Tang Naranja 15g": "274179",
    "Tang Manzana 15g": "274181",
    "Clight Naranja 8g": "274217",
    "Clight Mandarina 8g": "274276",
    "Flan Royal Vainilla 60g": "146743"
}

# -------------------
# 🔹 Función para obtener precio de la API
# -------------------
def obtener_precio(url, headers):
    """Consulta la API de VTEX y devuelve precio de lista o precio actual."""
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        if not data:
            return "❌ Sin datos"
        offer = data[0]['items'][0]['sellers'][0]['commertialOffer']
        price_list = offer.get('ListPrice', 0)
        price = offer.get('Price', 0)
        final_price = price_list if price_list > 0 else price
        if final_price > 0:
            return f"{final_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", "")
        return "no hay stock"
    except Exception:
        return "⚠️ Error"

# -------------------
# 🔹 Streamlit UI
# -------------------
st.title("📊 Comparación de precios Carrefour (Hiper Olivos) y Día")

if st.button("🔍 Ejecutar scraping"):
    with st.spinner("⏳ Procesando precios de Carrefour y Día..."):
        resultados = []

        # Usamos el diccionario de Carrefour como base de "Nombre"
        for nombre, id_carrefour in productos_carrefour.items():
            # Carrefour
            url_carrefour = f"https://www.carrefour.com.ar/api/catalog_system/pub/products/search?fq=productId:{id_carrefour}"
            precio_carrefour = obtener_precio(url_carrefour, HEADERS_CARREFOUR)

            # Día (si existe en diccionario)
            id_dia = productos_dia.get(nombre)
            if id_dia:
                url_dia = f"https://diaonline.supermercadosdia.com.ar/api/catalog_system/pub/products/search?fq=productId:{id_dia}"
                precio_dia = obtener_precio(url_dia, HEADERS_DIA)
            else:
                precio_dia = "❌ No en Día"

            resultados.append({
                "productId": id_carrefour,
                "Nombre": nombre,
                "Carrefour (Hiper Olivos)": precio_carrefour,
                "Día (Online)": precio_dia
            })

        # --- Crear DataFrame y mostrarlo
        df = pd.DataFrame(resultados, columns=["productId", "Nombre", "Carrefour (Hiper Olivos)", "Día (Online)"])
        st.success("✅ Scraping completado")
        st.dataframe(df)

        # --- Botón de descarga CSV
        fecha = datetime.now().strftime("%Y-%m-%d")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇ Descargar CSV",
            data=csv,
            file_name=f"precios_carrefour_dia_{fecha}.csv",
            mime="text/csv",
        )
