# app.py
import streamlit as st
import pandas as pd
import requests
from urllib.parse import urljoin

# =========================
# Importa tus EANs
# =========================
from productos_streamlit import productos  # dict: { "Nombre": {"ean": "...", "productId": "..."}, ... }

st.set_page_config(page_title="Coto · Relevamiento por EAN", layout="centered")
st.title("Relevamiento de precios Coto por EAN")
st.caption("Salida: EAN, Nombre del Producto, Precio (sku.activePrice)")

BASE = "https://www.cotodigital.com.ar"
SEARCH_PATH = "/sitios/cdigi/categoria"
DEFAULT_SUCURSAL = "200"

HEADERS = {
    "Accept": "application/json,text/plain,*/*",
    "User-Agent": "Mozilla/5.0"
}

# ============ utilidades JSON ============
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
    if s.count(",") == 1 and s.count(".") > 1:  # miles con punto + coma decimal
        s = s.replace(".", "").replace(",", ".")
    return float(s)

def format_ar_price(value):
    if value is None:
        return None
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ============ búsqueda por EAN ============
def search_product_by_ean(ean: str, suc: str = DEFAULT_SUCURSAL):
    """
    Busca por EAN usando Ntt y devuelve:
    - name (display)
    - product_url (SEO) si está disponible
    """
    params = {"Dy": "1", "Ntt": ean, "idSucursal": suc, "format": "json"}
    r = requests.get(urljoin(BASE, SEARCH_PATH), params=params, headers=HEADERS, timeout=20)
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
                product_url = urljoin(BASE, v)
                break
            if isinstance(v, str) and v.startswith("http"):
                product_url = v
                break

    return {"name": str(name) if name else None, "product_url": product_url}

def fetch_detail_from_product_url(product_url: str, suc: str = DEFAULT_SUCURSAL):
    """
    Llama al detalle del producto con format=json y extrae EAN, nombre y sku.activePrice.
    """
    # forzar parámetros del detalle
    if "?" in product_url:
        product_url = product_url.split("?", 1)[0]
    detail_url = f"{product_url}?Dy=1&idSucursal={suc}&format=json"

    r = requests.get(detail_url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    data = r.json()

    raw_ean   = coerce_first(find_key_recursive(data, "product.eanPrincipal"))
    raw_name  = coerce_first(find_key_recursive(data, "product.displayName"))
    raw_price = coerce_first(find_key_recursive(data, "sku.activePrice"))

    price_float = cast_price_to_float(raw_price)
    return {
        "ean": raw_ean,
        "name": raw_name,
        "price": format_ar_price(price_float)
    }

# ============ UI ============
st.write(f"Productos cargados: **{len(productos)}**")
if st.button("Ejecutar relevamiento"):
    rows = []
    for _, meta in productos.items():
        ean = str(meta.get("ean", "")).strip()
        if not ean:
            rows.append({"EAN": None, "Nombre del Producto": "EAN faltante", "Precio": None})
            continue
        try:
            found = search_product_by_ean(ean)
            if not found or not found.get("product_url"):
                rows.append({"EAN": ean, "Nombre del Producto": "No encontrado", "Precio": None})
                continue

            d = fetch_detail_from_product_url(found["product_url"])
            rows.append({
                "EAN": d["ean"] or ean,
                "Nombre del Producto": d["name"] or found["name"],
                "Precio": d["price"]
            })
        except Exception as ex:
            rows.append({"EAN": ean, "Nombre del Producto": f"Error: {ex}", "Precio": None})

    df = pd.DataFrame(rows, columns=["EAN", "Nombre del Producto", "Precio"])
    st.success("Relevamiento completado ✅")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("Descargar CSV", data=csv, file_name="coto_relevamiento.csv", mime="text/csv")
