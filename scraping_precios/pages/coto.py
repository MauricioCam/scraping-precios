# pages/coto.py
import streamlit as st
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# EANs desde tu diccionario
from productos_streamlit import productos

# --------- Config ---------
st.set_page_config(page_title="🏷️ Precios Coto", layout="wide")
st.title("🏷️ Relevamiento de precios Coto por EAN")
st.caption("Salida: EAN, Nombre del Producto, Precio (sku.activePrice)")

BASE_COTO = "https://www.cotodigital.com.ar"
SEARCH_PATH_COTO = "/sitios/cdigi/categoria"
DEFAULT_SUCURSAL = "200"

HEADERS_COTO = {
    "Accept": "application/json,text/plain,*/*",
    "User-Agent": "Mozilla/5.0",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# --------- Utilidades ---------
def format_ar_price_no_thousands(value):
    if value is None:
        return None
    return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", "")

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
    if s.count(",") == 1 and s.count(".") > 1:
        s = s.replace(".", "").replace(",", ".")
    return float(s)

@st.cache_resource(show_spinner=False)
def get_session():
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=0.3, status_forcelist=(429, 500, 502, 503, 504))
    adapter = HTTPAdapter(max_retries=retry, pool_connections=50, pool_maxsize=50)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update(HEADERS_COTO)
    return s

# --------- Capa de datos (cacheadas) ---------
@st.cache_data(ttl=3600, show_spinner=False)
def coto_search_by_ean(ean: str, sucursal: str):
    """Búsqueda JSON por EAN. Si trae precio, lo devolvemos (1 request)."""
    s = get_session()
    params = {"Dy": "1", "Ntt": ean, "idSucursal": sucursal, "format": "json"}
    r = s.get(urljoin(BASE_COTO, SEARCH_PATH_COTO), params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    # Iterar posibles 'records'
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

    # Intentar URL del producto
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

    # Si el precio ya viene en búsqueda → 1 request total
    raw_price_search = coerce_first(find_key_recursive(best, "sku.activePrice"))
    price_search = cast_price_to_float(raw_price_search) if raw_price_search is not None else None

    return {
        "name": str(name) if name else None,
        "product_url": product_url,
        "price_from_search": price_search
    }

@st.cache_data(ttl=1200, show_spinner=False)
def coto_fetch_detail(product_url: str, sucursal: str):
    """Detalle JSON con format=json → EAN, nombre y sku.activePrice."""
    s = get_session()
    if "?" in product_url:
        product_url = product_url.split("?", 1)[0]
    detail_url = f"{product_url}?Dy=1&idSucursal={sucursal}&format=json"
    r = s.get(detail_url, timeout=15)
    r.raise_for_status()
    data = r.json()

    raw_ean   = coerce_first(find_key_recursive(data, "product.eanPrincipal"))
    raw_name  = coerce_first(find_key_recursive(data, "product.displayName"))
    raw_price = coerce_first(find_key_recursive(data, "sku.activePrice"))
    price_float = cast_price_to_float(raw_price)

    return {
        "ean": raw_ean,
        "name": raw_name,
        "price": price_float
    }

def process_one_ean(nombre_ref: str, ean: str, sucursal: str):
    """Pipeline eficiente por EAN."""
    try:
        found = coto_search_by_ean(ean, sucursal)
        if not found:
            return {"EAN": ean, "Nombre": "No encontrado", "Precio": None}

        # 1 request si la búsqueda ya trae precio
        if found.get("price_from_search") is not None:
            return {
                "EAN": ean,
                "Nombre": found.get("name") or nombre_ref,
                "Precio": format_ar_price_no_thousands(found["price_from_search"])
            }

        # Si no, ir al detalle
        if not found.get("product_url"):
            return {"EAN": ean, "Nombre": found.get("name") or nombre_ref, "Precio": None}

        det = coto_fetch_detail(found["product_url"], sucursal)
        return {
            "EAN": det.get("ean") or ean,
            "Nombre": det.get("name") or found.get("name") or nombre_ref,
            "Precio": format_ar_price_no_thousands(det.get("price"))
        }
    except Exception as ex:
        return {"EAN": ean, "Nombre": f"Error: {ex}", "Precio": None}

# --------- UI ---------
with st.sidebar:
    st.header("Opciones")
    suc = st.text_input("idSucursal (Coto)", value=DEFAULT_SUCURSAL, help="Se aplica a búsquedas y detalles.")
    max_workers = st.slider("Concurrencia (hilos)", 1, 20, 10)

st.write(f"Productos cargados: **{len(productos)}**")

if st.button("⚡ Ejecutar relevamiento - Coto"):
    eans = [(nombre, str(d.get("ean", "")).strip()) for nombre, d in productos.items() if str(d.get("ean", "")).strip()]
    if not eans:
        st.warning("No hay EANs válidos en productos_streamlit.py")
    else:
        all_rows = []
        total = len(eans)
        prog = st.progress(0, text="Procesando EANs...")
        done = 0

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(process_one_ean, nombre, ean, suc or DEFAULT_SUCURSAL) for nombre, ean in eans]
            for fut in as_completed(futures):
                all_rows.append(fut.result())
                done += 1
                prog.progress(done / max(1, total), text=f"Procesando EANs... {done}/{total}")

        df = pd.DataFrame(all_rows, columns=["EAN", "Nombre", "Precio"]).sort_values("Nombre")
        st.success("✅ Relevamiento Coto completado")
        st.dataframe(df, use_container_width=True)

        fecha = datetime.now().strftime("%Y-%m-%d")
        st.download_button(
            "⬇ Descargar CSV (Coto)",
            df.to_csv(index=False).encode('utf-8'),
            file_name=f"precios_coto_{fecha}.csv",
            mime="text/csv",
        )
