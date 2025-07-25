import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ------------------------------------------------
# FUNCION DE SCRAPING SIN SELENIUM
# ------------------------------------------------
def obtener_precios():
    urls = {
        "Oreo 3x354g": "https://www.carrefour.com.ar/galletitas-oreo-rellenas-con-crema-sabor-original-354-g-715951/p",
        "Oreo 118g": "https://www.carrefour.com.ar/galletitas-dulce-oreo-rellenas-con-crema-118-g-715949/p",
        "Oreo Golden 118g": "https://www.carrefour.com.ar/galletitas-oreo-golden-sabor-vainilla-rellenas-con-crema-118-g-679211/p",
        "Pepitos 119g": "https://www.carrefour.com.ar/galletitas-pepitos-con-chips-de-chocolate-119-g-715953/p",
        "Lincoln Tripack 459g": "https://www.carrefour.com.ar/galletitas-dulces-lincoln-clasicas--terrabusi-tripack-459-g-715956/p",
        "Gelatina Royal 14g": "https://www.carrefour.com.ar/gelatina-sin-sabor-royal-14-g-662143/p",
        "Cadbury Frutilla 82g": "https://www.carrefour.com.ar/chocolate-cadbury-frutilla-relleno-yoghurt-82-g-680432/p",
        "Estufa": "https://www.carrefour.com.ar/estufa-de-cuarzo-philco-1800-w-phcu18t1-1659862/p"
    }

    precios = {}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for nombre, url in urls.items():
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code != 200:
                precios[nombre] = "no hay stock"
                continue

            soup = BeautifulSoup(r.text, "html.parser")

            # Buscar primero precio de lista (si existe)
            container = soup.select_one("span.valtech-carrefourar-product-price-0-x-listPriceValue")

            # Si no hay precio de lista, buscamos precio actual
            if container is None:
                container = soup.select_one("span.valtech-carrefourar-product-price-0-x-sellingPriceValue")

            if container is None:
                precios[nombre] = "no hay stock"
                continue

            # Buscar parte entera y decimal
            entero = container.select_one("span.valtech-carrefourar-product-price-0-x-currencyInteger")
            decimal = container.select_one("span.valtech-carrefourar-product-price-0-x-currencyFraction")

            if entero:
                entero = entero.text.strip().replace(".", "")
            else:
                entero = ""

            if decimal:
                decimal = decimal.text.strip()
            else:
                decimal = "00"

            if entero == "":
                precios[nombre] = "no hay stock"
                continue

            # Formatear precio a "1.200,00"
            precio_float = float(f"{entero}.{decimal}")
            precio_formateado = f"{precio_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", "")

            precios[nombre] = precio_formateado

        except Exception:
            precios[nombre] = "no hay stock"

    df = pd.DataFrame(list(precios.items()), columns=["Producto", "Precio"])
    return df

# ------------------------------------------------
# INTERFAZ STREAMLIT
# ------------------------------------------------
st.title("📊 Dashboard de precios Carrefour")
st.write("Consulta de precios en tiempo real (scraping con requests + BeautifulSoup).")

# Botón para ejecutar scraping
if st.button("🔄 Actualizar precios"):
    st.session_state["df"] = obtener_precios()
    st.success("✅ Precios actualizados.")

# Ejecutar scraping al cargar la página si no hay datos guardados
if "df" not in st.session_state:
    st.session_state["df"] = obtener_precios()

# Mostrar la tabla
st.dataframe(st.session_state["df"])

# Botón para descargar CSV
csv = st.session_state["df"].to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Descargar precios en CSV",
    data=csv,
    file_name=f"precios_{datetime.now().strftime('%Y-%m-%d')}.csv",
    mime="text/csv",
)
