import streamlit as st
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

# Diccionario de URLs
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

st.title("📊 Scraping Carrefour")

if st.button("🔍 Ejecutar scraping"):
    # Configuración Selenium
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)

    precios = {}

    for nombre, url in urls.items():
        try:
            driver.get(url)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.valtech-carrefourar-product-price-0-x-currencyContainer"))
            )

            try:
                container = driver.find_element(By.CSS_SELECTOR, 'span.valtech-carrefourar-product-price-0-x-listPriceValue')
            except NoSuchElementException:
                container = driver.find_element(By.CSS_SELECTOR, 'span.valtech-carrefourar-product-price-0-x-sellingPriceValue')

            # Extraer partes del precio
            entero = ""
            decimal = "00"
            for span in container.find_elements(By.XPATH, './/span'):
                clase = span.get_attribute("class") or ""
                texto = span.text.strip()
                if "currencyInteger" in clase:
                    entero += texto
                elif "currencyFraction" in clase:
                    decimal = texto

            if not entero:
                raise ValueError("No se encontró parte entera del precio.")

            precio_float = float(f"{entero}.{decimal}")
            precio_formateado = f"{precio_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", "")
            precios[nombre] = precio_formateado

        except Exception:
            precios[nombre] = "no hay stock"

    driver.quit()

    # Mostrar tabla
    df = pd.DataFrame(list(precios.items()), columns=["Producto", "Precio"])
    st.dataframe(df)

    # Botón para descargar CSV
    fecha = datetime.now().strftime("%Y-%m-%d")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇ Descargar CSV",
        data=csv,
        file_name=f"precios_carrefour_{fecha}.csv",
        mime="text/csv",
    )
