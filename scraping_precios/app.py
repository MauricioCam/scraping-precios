import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# -------------------
# 🔹 COOKIE de Hiper Olivos
# -------------------
COOKIE_SEGMENT = "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZWwiOiIxIiwicHJpY2VUYWJsZXMiOm51bGwsInJlZ2lvbklkIjpudWxsLCJ1dG1fY2FtcGFpZ24iOm51bGwsInV0bV9zb3VyY2UiOm51bGwsInV0bWlfY2FtcGFpZ24iOm51bGwsImN1cnJlbmN5Q29kZSI6IkFSUyIsImN1cnJlbmN5U3ltYm9sIjoiJCIsImNvdW50cnlDb2RlIjoiQVJHIiwiY3VsdHVyZUluZm8iOiJlcy1BUiIsImFkbWluX2N1bHR1cmVJbmZvIjoiZXMtQVIiLCJjaGFubmVsUHJpdmFjeSI6InB1YmxpYyJ9"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": f"vtex_segment={COOKIE_SEGMENT}"
}

# -------------------
# 🔹 Lista de URLs
# -------------------
urls = [
    "https://www.carrefour.com.ar/galletitas-oreo-rellenas-con-crema-sabor-original-354-g-715951/p",
    "https://www.carrefour.com.ar/galletitas-dulce-oreo-rellenas-con-crema-118-g-715949/p",
    "https://www.carrefour.com.ar/galletitas-oreo-golden-sabor-vainilla-rellenas-con-crema-118-g-679211/p",
    "https://www.carrefour.com.ar/galletitas-pepitos-con-chips-de-chocolate-119-g-715953/p",
    "https://www.carrefour.com.ar/galletitas-pepitos-con-chips-de-chocolate-357-g-pack-x3-de-119-g-715954/p",
    "https://www.carrefour.com.ar/galletitas-dulces-lincoln-clasicas--terrabusi-tripack-459-g-715956/p",
    "https://www.carrefour.com.ar/galletitas-dulces-lincoln-clasicas-terrabusi-219-g-720550/p",
    "https://www.carrefour.com.ar/galletitas-clasicas-lincoln-vainilla-153-g/p",
    "https://www.carrefour.com.ar/galletitas-dulces-variedad-terrabusi-mix-tamano-familiar-390-g-714816/p",
    "https://www.carrefour.com.ar/galletitas-dulce-variedad-terrabusi-mix-tamano-familiar-590-g-715957/p",
    "https://www.carrefour.com.ar/galletitas-crackers-cerealitas-clasicas-212-g-720563/p",
    "https://www.carrefour.com.ar/galletitas-dulce-melba-rellenas-con-crema-120-g-553640/p",
    "https://www.carrefour.com.ar/alfajor-terrabusi-triple-clasico-70-g-353214/p",
    "https://www.carrefour.com.ar/alfajor-terrabusi-chocolate-clasico-pack-6-uni-521104/p",
    "https://www.carrefour.com.ar/alfajor-oreo-triple-56-g-680445/p",
    "https://www.carrefour.com.ar/alfajor-milka-mousse-42-g-display-6-uni-528728/p",
    "https://www.carrefour.com.ar/alfajor-shot-con-mani-triple-60-g-353207/p",
    "https://www.carrefour.com.ar/alfajor-pepitos-triples-57-g-569707/p",
    "https://www.carrefour.com.ar/alfajor-triple-milka-oreo-61-g-667747/p",
    "https://www.carrefour.com.ar/chocolate-milka-con-leche-55-g-628578/p?idsku=24314",
    "https://www.carrefour.com.ar/chocolate-cadbury-frutilla-relleno-yoghurt-82-g-680432/p",
    "https://www.carrefour.com.ar/chocolate-milka-aireado-con-leche-110-g-680427/p",
    "https://www.carrefour.com.ar/chocolate-shot-con-mani-90-g-41397/p",
    "https://www.carrefour.com.ar/chocolate-shot-con-mani-35-g-42840-42840/p",
    "https://www.carrefour.com.ar/chicles-beldent-menta-fuerte-20-g-670219/p",
    "https://www.carrefour.com.ar/jugo-en-polvo-tang-naranja-15-g-711449/p",
    "https://www.carrefour.com.ar/jugo-en-polvo-tang-manzana-15-g/p",
    "https://www.carrefour.com.ar/jugo-en-polvo-clight-naranja-8-g/p",
    "https://www.carrefour.com.ar/jugo-en-polvo-clight-mandarina-8-g/p",
    "https://www.carrefour.com.ar/jugo-en-polvo-verao-naranja-7-g-rinde-1-l-711446/p",
    "https://www.carrefour.com.ar/gelatina-royal-sabor-frutilla-25-g-714815/p",
    "https://www.carrefour.com.ar/gelatina-royal-sabor-cereza-25-g-714811/p",
    "https://www.carrefour.com.ar/gelatina-royal-sabor-frutos-rojos-25-g-714814/p",
    "https://www.carrefour.com.ar/mousse-royal-de-chocolate-65-g-716932/p",
    "https://www.carrefour.com.ar/postre-royal-de-vainilla-75-g-716922/p",
    "https://www.carrefour.com.ar/flan-royal-de-vainilla-60-g-716929/p",
    "https://www.carrefour.com.ar/gelatina-royal-sabor-frambuesa-25-g-714809/p",
    "https://www.carrefour.com.ar/gelatina-sin-sabor-royal-14-g-662143/p",
    "https://www.carrefour.com.ar/gelatina-royal-sabor-frutilla-25-g-714808/p"
]

# -------------------
# 🔹 Interfaz Streamlit
# -------------------
st.title("📊 Precios Carrefour - Sucursal Hiper Olivos")
st.write("Se obtendrán los precios de todos los productos de la lista usando la cookie de la sucursal **Hiper Olivos**.")

if st.button("🔍 Ejecutar scraping"):
    resultados = []

    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")

            # nombre del producto
            title_tag = soup.select_one("h1.vtex-store-components-3-x-productNameContainer")
            nombre = title_tag.text.strip() if title_tag else "Producto sin nombre"

            # precio del producto
            precio_tag = soup.select_one("span.valtech-carrefourar-product-price-0-x-sellingPriceValue")
            if precio_tag:
                precio = precio_tag.text.strip()
            else:
                precio = "❌ No hay precio"

            resultados.append({"Producto": nombre, "Precio": precio})
        except Exception as e:
            resultados.append({"Producto": url, "Precio": "⚠️ Error"})

    # --- DataFrame y tabla
    df = pd.DataFrame(resultados)
    st.success("✅ Scraping completado")
    st.dataframe(df)

    # --- Botón CSV
    fecha = datetime.now().strftime("%Y-%m-%d")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇ Descargar CSV",
        data=csv,
        file_name=f"precios_hiper_olivos_{fecha}.csv",
        mime="text/csv",
    )
