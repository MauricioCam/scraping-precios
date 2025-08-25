import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from urllib.parse import urljoin

# ============================================
# Config app
# ============================================
st.set_page_config(page_title="📊 Relevamiento de Precios", layout="wide")
st.title("📊 Relevamiento de Precios")
st.caption("Carrefour y Coto — usando EANs de productos_streamlit.py")

# ============================================
# Datos de entrada (diccionario compartido)
# ============================================
from productos_streamlit import productos  # {"Nombre": {"ean": "...", "productId": "..."}}

# ============================================
# Utilidades comunes
# ============================================
def format_ar_price_no_thousands(value):
    """1795.0 -> '1795,00' (sin separador de miles)."""
    if value is None:
        return None
    return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", "")

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

# ============================================
# Pestañas
# ============================================
tab_carrefour, tab_coto, tab_jumbo = st.tabs(["🛒 Carrefour", "🏷️ Coto", "🟥 Jumbo"])

# ============================================
# 🛒 Carrefour
# ============================================
with tab_carrefour:
    st.subheader("Carrefour · Hiper Olivos")
    st.write("Relevamiento automático de todos los SKUs, aplicando la sucursal **Hiper Olivos**.")

    # --- Cookie / headers Carrefour (VTEX)
    COOKIE_SEGMENT = (
        "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZWwiOiIxIiwicHJpY2VUYWJsZXMiOm51bGwsInJlZ2lvbklkIjpudWxsLCJ1dG1fY2FtcGFpZ24iOm51bGws"
        "InV0bV9zb3VyY2UiOm51bGwsInV0bWlfY2FtcGFpZ24iOm51bGwsImN1cnJlbmN5Q29kZSI6IkFSUyIsImN1cnJlbmN5U3ltYm9sIjoiJCIsImNvdW50"
        "cnlDb2RlIjoiQVJHIiwiY3VsdHVyZUluZm8iOiJlcy1BUiIsImFkbWluX2N1dHR1cmVJbmZvIjoiZXMtQVIiLCJjaGFubmVsUHJpdmFjeSI6InB1YmxpYyJ9"
    )
    HEADERS_CARR = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"vtex_segment={COOKIE_SEGMENT}",
    }

    if st.button("🔍 Ejecutar relevamiento (Carrefour)"):
        with st.spinner("⏳ Relevando Carrefour..."):
            resultados = []
            for nombre, datos in productos.items():
                ean = datos.get("ean")
                product_id = datos.get("productId")
                try:
                    url = f"https://www.carrefour.com.ar/api/catalog_system/pub/products/search?fq=productId:{product_id}"
                    r = requests.get(url, headers=HEADERS_CARR, timeout=10)
                    data = r.json()

                    if not data:
                        resultados.append({"EAN": ean, "Nombre": nombre, "Precio": "Revisar"})
                        continue

                    offer = data[0]['items'][0]['sellers'][0]['commertialOffer']
                    price_list = offer.get('ListPrice', 0)
                    price = offer.get('Price', 0)
                    final_price = price_list if price_list > 0 else price

                    if final_price and final_price > 0:
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
            st.download_button(
                label="⬇ Descargar CSV (Carrefour)",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name=f"precios_carrefour_{fecha}.csv",
                mime="text/csv",
            )

# ============================================
# 🏷️ Coto
# ============================================
with tab_coto:
    st.subheader("Coto · Relevamiento por EAN")
    st.caption("Flujo: búsqueda (Ntk=product.eanPrincipal) → record.id → detalle (format=json) → sku.activePrice")

    # Constantes / headers Coto
    BASE = "https://www.cotodigital.com.ar"
    SEARCH_CATEGORIA = "/sitios/cdigi/categoria"
    DEFAULT_SUCURSAL = "200"
    HEADERS_COTO = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
    }

    suc = st.text_input("idSucursal (Coto)", value=DEFAULT_SUCURSAL, help="Se aplica a búsqueda y detalle.")
    show_debug = st.checkbox("Mostrar URLs de detalle (debug)", value=False)

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

    def cast_price(val):
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip()
        if s.count(",") == 1 and s.count(".") > 1:  # '1.795,00' -> 1795.00
            s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except Exception:
            return None

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

    def scrape_coto_by_items(items, sucursal: str, return_debug=False):
        s = requests.Session()
        s.headers.update(HEADERS_COTO)
        out = []
        debug_rows = []

        total = len(items)
        prog = st.progress(0, text="Procesando…")
        done = 0

        for nombre_ref, ean in items:
            ean = str(ean).strip()
            nombre_ref = str(nombre_ref).strip()
            row = {"EAN": ean, "Nombre del Producto": nombre_ref, "Precio": "Revisar"}  # default pedido

            try:
                record_id, name_hint = get_record_id_by_ean(s, ean, sucursal)
                if record_id:
                    det = fetch_detail_by_record_id(s, record_id, sucursal)
                    row["EAN"] = det.get("ean") or ean
                    row["Nombre del Producto"] = det.get("name") or name_hint or nombre_ref
                    if det.get("price") is not None:
                        row["Precio"] = det.get("price")
                    if return_debug:
                        debug_rows.append({"EAN": row["EAN"], "detail_url": det.get("detail_url")})
                # si no hay record_id, dejamos "Revisar" y nombre_ref tal cual
            except Exception:
                pass  # dejamos "Revisar"

            out.append(row)
            done += 1
            prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")

        return (out, debug_rows) if return_debug else (out, None)

    if st.button("⚡ Ejecutar relevamiento (Coto)"):
        # Construimos [(nombre_ref, ean), ...]
        items = []
        for nombre, meta in productos.items():
            ean = str(meta.get("ean", "")).strip()
            if ean:
                items.append((nombre, ean))

        if not items:
            st.warning("No hay EANs válidos en productos_streamlit.py")
        else:
            rows, dbg = scrape_coto_by_items(items, sucursal=(suc or DEFAULT_SUCURSAL), return_debug=show_debug)
            df = pd.DataFrame(rows, columns=["EAN", "Nombre del Producto", "Precio"])
            st.success("✅ Relevamiento Coto completado")
            st.dataframe(df, use_container_width=True)

            if show_debug and dbg:
                with st.expander("Debug: detalle de URLs llamadas"):
                    st.dataframe(pd.DataFrame(dbg), use_container_width=True)

            fecha = datetime.now().strftime("%Y-%m-%d")
            st.download_button(
                "⬇ Descargar CSV (Coto)",
                df.to_csv(index=False).encode("utf-8"),
                file_name=f"precios_coto_{fecha}.csv",
                mime="text/csv",
            )
# ============================================
# Jumbo
# ============================================
with tab_jumbo:
    st.subheader("Jumbo · Relevamiento por EAN (VTEX)")
    st.caption("Consulta por **EAN** y toma **Installments[].Value** del primer item/seller. Sin cookie.")

    HEADERS_JUMBO = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
    }

    if st.button("Ejecutar relevamiento (Jumbo)"):
        with st.spinner("⏳ Relevando Jumbo..."):
            resultados = []
            for nombre, datos in productos.items():
                ean = str(datos.get("ean") or "").strip()
                try:
                    if not ean:
                        resultados.append({"EAN": "", "Nombre": nombre, "Precio": "Revisar"})
                        continue

                    # VTEX search por EAN
                    url = f"https://www.jumbo.com.ar/api/catalog_system/pub/products/search?fq=alternateIds_Ean:{ean}"
                    r = requests.get(url, headers=HEADERS_JUMBO, timeout=12)
                    data = r.json()

                    if not data:
                        resultados.append({"EAN": ean, "Nombre": nombre, "Precio": "Revisar"})
                        continue

                    prod = data[0]
                    items = prod.get("items") or []

                    # Elegimos el item que matchee el EAN (ean o referenceId.Value). Si no, el primero.
                    item_sel = None
                    for it in items:
                        if str(it.get("ean") or "").strip() == ean:
                            item_sel = it
                            break
                        for ref in (it.get("referenceId") or []):
                            if str(ref.get("Value") or "").strip() == ean:
                                item_sel = it
                                break
                        if item_sel:
                            break
                    if not item_sel and items:
                        item_sel = items[0]

                    # Obtenemos Installments[].Value del primer seller
                    installments = []
                    try:
                        installments = (item_sel.get("sellers") or [])[0].get("commertialOffer", {}).get("Installments") or []
                    except Exception:
                        installments = []

                    # Tomamos el mayor Value disponible (suele ser 1 cuota, p.ej. American Express)
                    vals = [float(x.get("Value") or 0) for x in installments if isinstance(x, dict)]
                    price_val = max(vals) if vals else 0.0

                    if price_val > 0:
                        precio_formateado = format_ar_price_no_thousands(price_val)
                        nombre_prod = prod.get("productName") or nombre
                        resultados.append({"EAN": ean, "Nombre": nombre_prod, "Precio": precio_formateado})
                    else:
                        resultados.append({"EAN": ean, "Nombre": nombre, "Precio": "Revisar"})

                except Exception:
                    resultados.append({"EAN": ean, "Nombre": nombre, "Precio": "Revisar"})

            df = pd.DataFrame(resultados, columns=["EAN", "Nombre", "Precio"])
            st.success("✅ Relevamiento Jumbo completado")
            st.dataframe(df, use_container_width=True)

            fecha = datetime.now().strftime("%Y-%m-%d")
            st.download_button(
                label="⬇ Descargar CSV (Jumbo)",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"precios_jumbo_{fecha}.csv",
                mime="text/csv",
            )

