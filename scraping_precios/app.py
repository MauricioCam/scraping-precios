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
    "Lincoln Tripack 459g": "715956",
    "Gelatina Royal 14g": "662143",
    "Cadbury Frutilla 82g": "680432",
    "Estufa Philco": "1659862",
    "Alfajor Shot con Maní": "353207"
}

# --- Título de la app ---
st.title("📊 Scraping Carrefour (API VTEX)")

st.write("Pulsa el botón para obtener los precios actualizados directamente desde la API de Carrefour.")

# --- Botón de ejecución ---
if st.button("🔍 Ejecutar scraping"):
    st.info("Consultando API de Carrefour...")

    resultados = {}

    for nombre, product_id in productos.items():
        try:
            url = f"https://www.carrefour.com.ar/api/catalog_system/pub/products/search?fq=productId:{product_id}"
            response = requests.get(url, timeout=10)
            data = response.json()

            # Extraer precios
            offer = data[0]['items'][0]['sellers'][0]['commertialOffer']
            price_list = offer['ListPrice']
            price = offer['Price']

            # Usar precio de lista si existe, sino precio actual
            final_price = price_list if price_list > 0 else price

            # Formatear precio: "4470,00"
            precio_formateado = f"{final_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", "")

            # Guardar resultado
            resultados[nombre] = precio_formateado if final_price > 0 else "no hay stock"

        except Exception:
            resultados[nombre] = "no hay stock"

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
