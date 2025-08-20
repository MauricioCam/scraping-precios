# coto_app.py
import streamlit as st
import pandas as pd
import requests
from urllib.parse import urljoin
from datetime import datetime

# =========================
# Cargar EANs
# =========================
from productos_streamlit import productos  # {"Nombre": {"ean": "...", "productId": "..."}}

# =========================
# Configuración
# =========================
st.set_page_config(page_title="🏷️ Coto · Relevamiento por EAN", layout="wide")
st.markdown("# 🏷️ Coto · Relevamiento por EAN (flujo robusto)")
st.caption("Flujo: búsqueda (Ntk=product.eanPrincipal) → record.id → detalle (format=json) → sku.activePrice")

# Constantes / Headers
BASE = "https://www.cotodigital.com.ar"
SEARCH_CATEGORIA = "/sitios/cdigi/categoria"
DEFAULT_SUCURSAL = "200"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}

# =========================
# Utilidades
# =========================
def coerce_first(x):
    return (x[0] if isinstance(x, list) and x else x)

def find_key_recursive(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = find_key_recursive(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for it in obj:
            r = find_key_recursive(it, key)
            if r is not None:
                return r
    return None

def iter_records(node):
    if isinstance(node, dict):
        if any(k in node for k in ("record.id","product.repositoryId","product.displayName","product.eanPrincipal")):
            yield node
        for v in node.values():
            yield from iter_records(v)
    elif isinstance(node, list):
        for it in node:
            yield from iter_records(it)

def cast_price(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    # '1.795,00' -> 1795.00
    if s.count(",") == 1 and s.count(".") > 1:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None

def format_ar_price_no_thousands(value):
    if value is None:
        return None
    return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", "")

# =========================
# Core scraping (mismo flujo validado)
# =========================
def get_record_id_by_ean(session: requests.Session, ean: str, sucursal: str):
    params = {"Dy": "1", "Ntt": ean, "Ntk": "product.eanPrincipal", "idSucursal": sucursal, "format": "json"}
    r = session.get(urljoin(BASE, SEARCH_CATEGORIA), params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    for rec in iter_records(data):
        e = coerce_first(find_key_recursive(rec, "product.eanPrincipal"))
        if str(e) == str(ean):
            rid  = coerce_first(find_key_recursive(rec, "record.id"))
            name = coerce_first(find_key_recursive(rec, "product.displayName")) \
                   or coerce_first(find_key_recursive(rec, "record.title"))
            return rid, (str(name) if name else None)
    return None, None

def fetch_detail_by_record_id(session: requests.Session, record_id: str, sucursal: str):
    product_url = f"{BASE}/sitios/cdigi/productos/_/R-{record_id}"
    detail_url = f"{product_url}?Dy=1&idSucursal={sucursal}&format=json"

    headers = dict(session.headers)
    headers["Referer"] = product_url  # ayuda en algunos entornos
    r = session.get(detail_url, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()

    ean   = coerce_first(find_key_recursive(data, "product.eanPrincipal"))
    name  = coerce_first(find_key_recursive(data, "product.displayName"))
    raw   = coerce_first(find_key_recursive(data, "sku.activePrice"))

    price = cast_price(raw)
    if price is None:
        # fallbacks por si cambia el campo
        for alt in ("activePrice","sku.price","sku.listPrice","price","listPrice"):
            raw_alt = coerce_first(find_key_recursive(data, alt))
            price = cast_price(raw_alt)
            if price is not None:
                break

    return {
        "ean": ean,
        "name": name,
        "price": format_ar_price_no_thousands(price),
        "detail_url": detail_url,
    }

def scrape_coto_by_items(items, sucursal=DEFAULT_SUCURSAL, return_debug=False):
    """
    items: lista de tuplas [(nombre_ref, ean_str), ...]
    """
    s = requests.Session()
    s.headers.update(HEADERS)
    out = []
    debug_rows = []

    total = len(items)
    prog = st.progress(0, text="Procesando…")
    done = 0

    for nombre_ref, ean in items:
        ean = str(ean).strip()
        nombre_ref = str(nombre_ref).strip()
        row = {"EAN": ean, "Nombre del Producto": nombre_ref, "Precio": "Revisar"}  # ← default pedido

        try:
            record_id, name_hint = get_record_id_by_ean(s, ean, sucursal)
            if record_id:
                det = fetch_detail_by_record_id(s, record_id, sucursal)
                row["EAN"] = det.get("ean") or ean
                # nombre normal: priorizamos detalle → hint → nombre original
                row["Nombre del Producto"] = det.get("name") or name_hint or nombre_ref
                # precio si existe; si no, queda "Revisar"
                if det.get("price") is not None:
                    row["Precio"] = det.get("price")

                if return_debug:
                    debug_rows.append({"EAN": row["EAN"], "detail_url": det.get("detail_url")})
            # si no hay record_id, dejamos "Precio" = "Revisar" y mantenemos nombre_ref
        except Exception:
            # ante error, mantenemos EAN y Nombre normal; "Precio" = "Revisar"
            pass

        out.append(row)
        done += 1
        prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")

    return (out, debug_rows) if return_debug else (out, None)

# =========================
# UI
# =========================
with st.sidebar:
    st.header("Parámetros")
    suc = st.text_input("idSucursal (Coto)", value=DEFAULT_SUCURSAL, help="Se aplica a búsqueda y detalle.")
    show_debug = st.checkbox("Mostrar URLs de detalle (debug)", value=False)
    st.caption("Salida: EAN · Nombre del Producto · Precio (sku.activePrice)")

st.markdown(f"**Productos cargados:** {len(productos)}")

if st.button("🔍 Ejecutar relevamiento - Coto"):
    # Construimos [(nombre_ref, ean), ...] preservando el nombre original
    items = []
    for nombre, meta in productos.items():
        ean = str(meta.get("ean", "")).strip()
        if ean:
            items.append((nombre, ean))

    if not items:
        st.warning("No hay EANs válidos en productos_streamlit.py")
    else:
        rows, dbg = scrape_coto_by_items(items, sucursal=suc or DEFAULT_SUCURSAL, return_debug=show_debug)

        df = pd.DataFrame(rows, columns=["EAN", "Nombre del Producto", "Precio"])
        st.success("✅ Relevamiento completado")
        st.dataframe(df, use_container_width=True)

        if show_debug and dbg:
            with st.expander("Debug: detalle de URLs llamadas"):
                st.dataframe(pd.DataFrame(dbg), use_container_width=True)

        fecha = datetime.now().strftime("%Y-%m-%d")
        st.download_button(
            "⬇ Descargar CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name=f"precios_coto_{fecha}.csv",
            mime="text/csv",
        )
