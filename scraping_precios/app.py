import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ------------------------------------------------
# FUNCIÓN DE SCRAPING: busca el precio SIN impuestos, lo multiplica x1.21
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

            # 🔍 Buscar el precio sin impuestos
            span_precio = soup.select_one("span.carrefourar-transparencia-fiscal-0-x-valuePriceWithoutTaxes")

            if not span_precio:
                precios[nombre] = "no hay stock"
                continue

            # Ejemplo de texto: "$ 668,60 c/u"
            texto_precio = span_precio.get_text(strip=True)

            # Limpiar el texto → eliminar "$" y "c/u"
            texto_precio = texto_precio.replace("$", "").replace("c/u", "").strip()

            # Convertir a float (reemplazar coma por punto)
            precio_base = float(texto_precio.replace(".", "").replace(",", "."))

            # Multiplicar por 1.21
            precio_final = precio_base * 1.21

            # Formatear a formato argentino (1.234,56)
            precio_formateado = f"{precio_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", "")

            precios[nombre] = precio_formateado

        except Exception:
            precios[nombre] = "no hay stock"

    # Crear DataFrame para Streamlit
    df = pd.DataFrame(list(precios.items()), columns=["Producto", "Precio"])
    return df

# ------------------------------------------------
# INTERFAZ DE STREAMLIT
# ------------------------------------------------
st.title("📊 Dashboard de precios Carrefour")
st.write("Consulta precios (con impuestos aplicados) en tiempo real.")

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
