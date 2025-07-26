import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- Diccionario de productos Carrefour (Nombre: productId) ---
productos = {
    "Oreo 3x354g": "715951",
    "Oreo 118g": "715949",
    "Oreo Golden 118g": "679211",
    "Pepitos 119g": "715953",
    "Pepitos Tripack 357g": "715954",
    "Lincoln Tripack 459g": "715956",
    "Lincoln 219g": "720550",
    "Lincoln Vainilla 153g": "sin_id",  # ⚠️ No detectado
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
    "Tang Manzana 15g": "sin_id",      # ⚠️ No detectado
    "Clight Naranja 8g": "sin_id",     # ⚠️ No detectado
    "Clight Mandarina 8g": "sin_id",   # ⚠️ No detectado
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

# --- Título de la app ---
st.title("📊 Scraping Carrefour (API VTEX)")

st.write("Pulsa el botón para obtener los precios actualizados directamente desde la API de Carrefour.")

# --- Botón de ejecución ---
if st.button("🔍 Ejecutar scraping"):
    st.info("Consultando API de Carrefour...")

    resultados = {}

    for nombre, product_id in productos.items():
        if product_id == "sin_id":
            resultados[nombre] = "❌ ID no detectado"
            continue

        try:
            url = f"https://www.carrefour.com.ar/api/catalog_system/pub/products/search?fq=productId:{product_id}"
            response = requests.get(url, timeout=10)
            data = response.json()

            # Extraer precios del JSON
            offer = data[0]['items'][0]['sellers'][0]['commertialOffer']
            price_list = offer['ListPrice']
            price = offer['Price']

            # Usar precio de lista si existe, sino el actual
            final_price = price_list if price_list > 0 else price

            # Formatear precio tipo "4.470,00"
            precio_formateado = f"{final_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", "")

            resultados[nombre] = precio_formateado if final_price > 0 else "no hay stock"

        except Exception:
            resultados[nombre] = "error"

    # --- Crear DataFrame ---
    df = pd.DataFrame(list(resultados.items()), columns=["Producto", "Precio"])

    # --- Mostrar tabla en Streamlit ---
    st.success("✅ Scraping completado (API)")
    st.dataframe(df)

    # --- Botón para descargar CSV ---
    fecha = datetime.now().strftime("%Y-%m-%d")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇ Descargar CSV",
        data=csv,
        file_name=f"precios_carrefour_{fecha}.csv",
        mime="text/csv",
    )
