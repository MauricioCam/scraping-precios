# app.py
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from urllib.parse import urljoin

# ===========================
# 📥 IMPORTAR EL DICCIONARIO
# ===========================
from productos_streamlit import productos
# productos = {
#   "Nombre A": {"ean": "7622...", "productId": "12345"},
#   ...
# }

# ===========================
# 🔹 HEADERS / COOKIES
# ===========================
# Carrefour (mantengo tu cookie/UA)
COOKIE_SEGMENT = "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZWwiOiIxIiwicHJpY2VUYWJsZXMiOm51bGwsInJlZ2lvbklkIjpudWxsLCJ1dG1fY2FtcGFpZ24iOm51bGwsInV0bV9zb3VyY2UiOm51bGwsInV0bWlfY2FtcGFpZ24iOm51bGwsImN1cnJlbmN5Q29kZSI6IkFSUyIsImN1cnJlbmN5U3ltYm9sIjoiJCIsImNvdW50cnlDb2RlIjoiQVJHIiwiY3VsdHVyZUluZm8iOiJlcy1BUiIsImFkbWluX2N1dHR1cmVJbmZvIjoiZXMtQVIiLCJjaGFubmVsUHJpdmFjeSI6InB1YmxpYyJ9"
HEADERS_CARREFOUR = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": f"vtex_segment={COOKIE_SEGMENT}"
}

# Coto (JSON)
BASE_COTO = "https://www.cotodigital.com.ar"
SEARCH_PATH_COTO = "/sitios/cdigi/categoria"
DEFAULT_SUCURSAL_COTO = "200"
HEADERS_COTO = {
    "Accept": "application/json,text/plain,*/*",
    "User-Agent": "Mozilla/5.0"
}

# ===========================
# 🔧 UTILIDADES
# ===========================
def format_ar_price_no_thousands(value):
    """1795.0 -> '1795,00' (sin separador de miles)."""
    if value is None:
        return None
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", "")

def find_key_recursive(obj, keyname):
    if isinstance(obj, dict):
        if keyname in obj:
            return obj[keyname]
        for v in obj.values():
            r = find_key_recursive(v, keyname)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for it in obj:
            r = find_key_recursive(it, keyname)
            if r is not None:
                return r
    return None

def coerce_first(x):
    return (x[0] if isinstance(x, list) and x else x)

def cast_price_to_float(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    # Si viniera como '1.795,00' normalizamos
    if s.count(",") == 1 and s.count(".") > 1:
        s = s.replace(".", "").replace(",", ".")
    return float(s)

# =============== Coto: búsqueda por EAN ===============
def coto_search_by_ean(ean: str, suc: str = DEFAULT_SUCURSAL_COTO):
    """
    Busca por EAN usando Ntt y devuelve:
    - name (display)
    - product_url (SEO) si está disponible
    """
    params = {"Dy": "1", "Ntt": ean, "idSucursal": suc, "format": "json"}
    r = requests.get(urljoin(BASE_COTO, SEARCH_PATH_COTO), params=params, headers=HEADERS_COTO, timeout=20)
    r.raise_for_status()
    data = r.json()

    # iterar posibles 'records' en la respuesta
    def iter_records(node):
        if isinstance(node, dict):
            if any(k in node for k in ("record.id", "product.repositoryId", "product.displayName")):
                yield node
            for v in node.values():
                yield from iter_records(v)
        elif isinstance(node, list):
            for it in node:
                yield from iter_records(it)

    best = None
    for rec in iter_records(data):
        ean_node = find_key_recursive(rec, "product.eanPrincipal")
        if coerce_first(ean_node) == str(ean):
            best = rec
            break

    if not best:
        return None

    name = coerce_first(find_key_recursive(best, "product.displayName")) or coerce_first(find_key_recursive(best, "record.title"))

    # intentar extraer URL del producto
    url_fields = ["product.URL", "product.productURL", "product.seoUrl", "seo.url", "link", "url"]
    product_url = None
    for f in url_fields:
        v = find_key_recursive(best, f)
        if v:
            v = coerce_first(v)
            if isinstance(v, str) and v.startswith("/"):
                product_url = urljoin(BASE_COTO, v)
                break
            if isinstance(v, str) and v.startswith("http"):
                product_url = v
                break

    return {"name": str(name) if name else None, "product_url": product_url}

def coto_fetch_detail(product_url: str, suc: str = DEFAULT_SUCURSAL_COTO):
    """
    Llama al detalle del producto con format=json y extrae EAN, nombre y sku.activePrice.
    """
    if "?" in product_url:
        product_url = product_url.split("?", 1)[0]
    detail_url = f"{product_url}?Dy=1&idSucursal={suc}&format=json"

    r = requests.get(detail_url, headers=HEADERS_COTO, timeout=20)
    r.raise_for_status()
    data = r.json()

    raw_ean   = coerce_first(find_key_recursive(data, "product.eanPrincipal"))
    raw_name  = coerce_first(find_key_recursive(data, "product.displayName"))
    raw_price = coerce_first(find_key_recursive(data, "sku.activePrice"))

    price_float = cast_price_to_float(raw_price)
    return {
        "ean": raw_ean,
        "name": raw_name,
        "price": format_ar_price_no_thousands(price_float)
    }

# ===========================
# 🎨 INTERFAZ STREAMLIT
# ===========================
st.set_page_config(page_title="📊 Relevamiento Precios", layout="wide")
st.title("📊 Relevamiento de Precios")

tab_carrefour, tab_coto = st.tabs(["Carrefour", "Coto"])

# -------- TAB CARREFOUR (tu flujo original) --------
with tab_carrefour:
    st.subheader("Carrefour (Hiper Olivos)")
    st.write("Relevamiento automático de todos los SKUs, aplicando la sucursal **Hiper Olivos**.")

    if st.button("🔍 Ejecutar relevamiento - Carrefour"):
        with st.spinner("⏳ Relevando Carrefour..."):
            resultados = []

            for nombre, datos in productos.items():
                ean = datos.get("ean")
                product_id = datos.get("productId")

                try:
                    url = f"https://www.carrefour.com.ar/api/catalog_system/pub/products/search?fq=productId:{product_id}"
                    r = requests.get(url, headers=HEADERS_CARREFOUR, timeout=10)
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

            df = pd.DataFrame(resultados, columns=["EAN", "Nombre", "Precio"])
            st.success("✅ Relevamiento Carrefour completado")
            st.dataframe(df, use_container_width=True)

            fecha = datetime.now().strftime("%Y-%m-%d")
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇ Descargar CSV (Carrefour)",
                data=csv,
                file_name=f"precios_carrefour_{fecha}.csv",
                mime="text/csv",
            )

# -------- TAB COTO (por EAN usando JSON) --------
with tab_coto:
    st.subheader("Coto (por EAN)")
    suc = st.text_input("idSucursal (Coto)", value=DEFAULT_SUCURSAL_COTO, help="Se usa para todas las búsquedas/detalles.")
    st.caption("Salida: EAN, Nombre del Producto, Precio (sku.activePrice)")

    if st.button("🧭 Ejecutar relevamiento - Coto"):
        with st.spinner("⏳ Relevando Coto..."):
            rows = []
            for nombre, datos in productos.items():
                ean = str(datos.get("ean", "")).strip()
                if not ean:
                    rows.append({"EAN": None, "Nombre": "EAN faltante", "Precio": None})
                    continue
                try:
                    found = coto_search_by_ean(ean, suc=suc or DEFAULT_SUCURSAL_COTO)
                    if not found or not found.get("product_url"):
                        rows.append({"EAN": ean, "Nombre": "No encontrado", "Precio": None})
                        continue

                    d = coto_fetch_detail(found["product_url"], suc=suc or DEFAULT_SUCURSAL_COTO)
                    rows.append({
                        "EAN": d["ean"] or ean,
                        "Nombre": d["name"] or found.get("name") or nombre,
                        "Precio": d["price"]
                    })
                except Exception as ex:
                    rows.append({"EAN": ean, "Nombre": f"Error: {ex}", "Precio": None})

            dfc = pd.DataFrame(rows, columns=["EAN", "Nombre", "Precio"])
            st.success("✅ Relevamiento Coto completado")
            st.dataframe(dfc, use_container_width=True)

            fecha = datetime.now().strftime("%Y-%m-%d")
            csv = dfc.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇ Descargar CSV (Coto)",
                data=csv,
                file_name=f"precios_coto_{fecha}.csv",
                mime="text/csv",
            )
