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
st.caption("Esta herramienta tiene por objetivo relevar los precios de todo el portfolio de forma automática")

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
tab_carrefour, tab_dia, tab_chango, tab_coto, tab_jumbo, tab_vea, tab_coope, tab_hiper = st.tabs(["🛒 Carrefour", "🟥 Día", "🟢 ChangoMás", "🏷️ Coto", "🟢 Jumbo", "🟢 Vea", "🟡 Cooperativa", "🔴 Libertad"])

# ============================================
# 🛒 Carrefour (por EAN)
# ============================================
with tab_carrefour:
    st.subheader("Carrefour · Hiper Olivos")
    st.write("Relevamiento automático de todos los SKUs, aplicando la sucursal **Hiper Olivos**. (Ahora busca por **EAN**)")

    # --- Cookie / headers Carrefour (VTEX)
    COOKIE_SEGMENT = (
        "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZWwiOiIxIiwicHJpY2VUYWJsZXMiOm51bGwsInJlZ2lvbklkIjpudWxsLCJ1dG1fY2FtcGFpZ24iOm51bGws"
        "InV0bV9zb3VyY2UiOm51bGwsInV0bWlfY2FtcGFpZ24iOm51bGwsImN1cnJlbmN5Q29kZSI6IkFSUyIsImN1cnJlbmN5U3ltYm9sIjoiJCIsImNvdW50"
        "cnlDb2RlIjoiQVJHIiwiY3VsdHVyZUluZm8iOiJlcy1BUiIsImFkbWluX2N1dHR1cmVJbmZvIjoiZXMtQVIiLCJjaGFubmVsUHJpdmFjeSI6InB1YmxpYyJ9"
    )
    HEADERS_CARR = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"vtex_segment={COOKIE_SEGMENT}",
        "Accept": "application/json,text/plain,*/*",
    }

    if st.button("🔍 Ejecutar relevamiento (Carrefour)"):
        with st.spinner("⏳ Relevando Carrefour..."):
            resultados = []
            for nombre, datos in productos.items():
                ean = str(datos.get("ean") or "").strip()
                try:
                    if not ean:
                        resultados.append({"EAN": "", "Nombre": nombre, "Precio": "Revisar"})
                        continue

                    # Buscar por EAN en VTEX
                    url = f"https://www.carrefour.com.ar/api/catalog_system/pub/products/search?fq=alternateIds_Ean:{ean}"
                    r = requests.get(url, headers=HEADERS_CARR, timeout=12)
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

                    if not item_sel or not item_sel.get("sellers"):
                        resultados.append({"EAN": ean, "Nombre": nombre, "Precio": "Revisar"})
                        continue

                    offer = item_sel["sellers"][0].get("commertialOffer", {})
                    price_list = float(offer.get("ListPrice") or 0)
                    price = float(offer.get("Price") or 0)
                    final_price = price_list if price_list > 0 else price

                    if final_price and final_price > 0:
                        precio_formateado = format_ar_price_no_thousands(final_price)
                        nombre_prod = prod.get("productName") or nombre
                        resultados.append({"EAN": ean, "Nombre": nombre_prod, "Precio": precio_formateado})
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
# 🟥 Día
# ============================================
with tab_dia:
    st.subheader("Día · Relevamiento por cod_dia (skuId)")
    st.caption("Consulta VTEX por **skuId (cod_dia)** y toma **commertialOffer.ListPrice** del primer item/seller.")

    HEADERS_DIA = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
    }

    if st.button("🔴 Ejecutar relevamiento (Día)"):
        with st.spinner("⏳ Relevando Día..."):
            resultados = []
            for nombre, datos in productos.items():
                cod_dia = str(datos.get("cod_dia") or "").strip()
                ean = datos.get("ean")
                try:
                    if not cod_dia:
                        resultados.append({"EAN": ean, "Nombre": nombre, "Precio": "Revisar"})
                        continue

                    # VTEX search por skuId (cod_dia)
                    url = f"https://diaonline.supermercadosdia.com.ar/api/catalog_system/pub/products/search?fq=skuId:{cod_dia}"
                    r = requests.get(url, headers=HEADERS_DIA, timeout=12)
                    r.raise_for_status()
                    data = r.json()

                    if not data:
                        resultados.append({"EAN": ean, "Nombre": nombre, "Precio": "Revisar"})
                        continue

                    prod = data[0]
                    items = prod.get("items") or []

                    # Elegimos el item cuyo itemId == cod_dia; si no aparece, usamos el primero
                    item_sel = None
                    for it in items:
                        if str(it.get("itemId") or "").strip() == cod_dia:
                            item_sel = it
                            break
                    if not item_sel and items:
                        item_sel = items[0]

                    if not item_sel:
                        resultados.append({"EAN": ean, "Nombre": nombre, "Precio": "Revisar"})
                        continue

                    offer = (item_sel.get("sellers") or [{}])[0].get("commertialOffer", {}) if item_sel.get("sellers") else {}
                    list_price = offer.get("ListPrice", 0) or 0

                    if list_price > 0:
                        precio_formateado = format_ar_price_no_thousands(list_price)
                        nombre_prod = prod.get("productName") or nombre
                        resultados.append({"EAN": ean, "Nombre": nombre_prod, "Precio": precio_formateado})
                    else:
                        resultados.append({"EAN": ean, "Nombre": nombre, "Precio": "Revisar"})

                except Exception:
                    resultados.append({"EAN": ean, "Nombre": nombre, "Precio": "Revisar"})

            df = pd.DataFrame(resultados, columns=["EAN", "Nombre", "Precio"])
            st.success("✅ Relevamiento Día completado")
            st.dataframe(df, use_container_width=True)

            fecha = datetime.now().strftime("%Y-%m-%d")
            st.download_button(
                label="⬇ Descargar CSV (Día)",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"precios_dia_{fecha}.csv",
                mime="text/csv",
            )
    
# ============================================
# 🟢 ChangoMás (por RefId)
# ============================================
with tab_chango:
    st.subheader("ChangoMás · Relevamiento por RefId (VTEX)")
    st.caption("Consulta por **RefId** usando VTEX Search (`alternateIds_RefId`). Early exit + timeouts cortos. Sin SC alternativos.")

    # Parámetros
    DEFAULT_SEGMENT = (
        "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZWwiOiIxIiwicHJpY2VUYWJsZXMiOm51bGwsInJlZ2lvbklkIjoidjIuNDdERkY5REI3QkE5NEEyMEI1ODRGRjYzQTA3RUIxQ0EiLCJ1dG1fY2FtcGFpZ24iOm51bGwsInV0bV9zb3VyY2UiOm51bGwsInV0bWlfY2FtcGFpZ24iOm51bGwsImN1cnJlbmN5Q29kZSI6IkFSUyIsImN1cnJlbmN5U3ltYm9sIjoiJCIsImNvdW50cnlDb2RlIjoiQVJHIiwiY3VsdHVyZUluZm8iOiJlcy1BUiIsImFkbWluX2N1bHR1cmVJbmZvIjoiZXMtQVIiLCJjaGFubmVsUHJpdmFjeSI6InB1YmxpYyJ9"
    )
    vtex_segment = st.text_input("vtex_segment (ChangoMás)", value=DEFAULT_SEGMENT, type="password")
    sc_primary = st.text_input("Sales channel (sc)", value="1", help="Canal de ventas VTEX, ej: 1")
    show_debug_cm = st.checkbox("Mostrar requests (debug)", value=False)

    # Constantes
    BASE_CM = "https://www.masonline.com.ar"
    TIMEOUTS = (3, 7)  # (connect, read)

    def first_listprice_or_price(item: dict) -> float:
        best_price = 0.0
        for seller in (item.get("sellers") or []):
            co = seller.get("commertialOffer") or {}
            lp = float(co.get("ListPrice") or 0)
            if lp > 0:
                return lp  # 🎯 early exit
            p = float(co.get("Price") or 0)
            if p > best_price:
                best_price = p
        return best_price

    def vt_search_by_refid(session: requests.Session, refid: str, sc: str, headers: dict):
        url = f"{BASE_CM}/api/catalog_system/pub/products/search"
        params = {"fq": f"alternateIds_RefId:{refid}", "sc": sc}
        r = session.get(url, headers=headers, params=params, timeout=TIMEOUTS)
        if show_debug_cm:
            st.text(f"SEARCH {sc}: {r.url} | {r.status_code} | {r.headers.get('content-type')}")
        r.raise_for_status()
        data = r.json()
        if not data:
            return None, None
        prod = data[0]
        items = prod.get("items", []) or []
        return prod, items

    def vt_variations_price(session: requests.Session, product_id: str, refid: str, sc: str, headers: dict):
        url = f"{BASE_CM}/api/catalog_system/pub/products/variations/{product_id}"
        params = {"sc": sc}
        r = session.get(url, headers=headers, params=params, timeout=TIMEOUTS)
        if show_debug_cm:
            st.text(f"VARIATIONS {sc}: {r.url} | {r.status_code}")
        r.raise_for_status()
        data = r.json()
        name = data.get("name")
        for sku in (data.get("skus") or []):
            refids = [str(x.get("Value")) for x in (sku.get("referenceId") or []) if isinstance(x, dict)]
            if str(refid) in refids or not refids:
                lp = float(sku.get("listPrice") or 0)
                if lp > 0:
                    return name, lp
                bp = float(sku.get("bestPrice") or 0)
                return name, (bp if bp > 0 else None)
        return name, None

    st.markdown(f"**Productos cargados:** {len(productos)} (se espera `cod_maso` en cada ítem)")

    if st.button("🟢 Ejecutar relevamiento (ChangoMás por RefId)"):
        with st.spinner("⏳ Relevando ChangoMás..."):
            s = requests.Session()
            headers_cm = {
                "User-Agent": "Mozilla/5.0",
                "Cookie": f"vtex_segment={vtex_segment}",
                "Accept": "application/json,text/plain,*/*",
            }

            resultados = []
            total = len(productos)
            prog = st.progress(0, text="Procesando…")
            done = 0

            for nombre, datos in productos.items():
                refid = str(datos.get("cod_maso", "")).strip()  # ⚠️ clave esperada
                ean   = str(datos.get("ean", "")).strip()
                if not refid:
                    resultados.append({"EAN": ean, "RefId": "", "Nombre": nombre, "Precio": "Revisar"})
                    done += 1
                    prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")
                    continue

                row = {"EAN": ean, "RefId": refid, "Nombre": nombre, "Precio": "Revisar"}
                try:
                    found_price = None
                    found_name = None

                    prod, items = vt_search_by_refid(s, refid, sc_primary.strip(), headers_cm)
                    if prod and items:
                        # Item cuyo RefId coincida; si no, el primero
                        item_sel = None
                        for it in items:
                            for rfi in (it.get("referenceId") or []):
                                if str(rfi.get("Value", "")).strip() == refid:
                                    item_sel = it
                                    break
                            if item_sel:
                                break
                        if not item_sel and items:
                            item_sel = items[0]

                        price_num = first_listprice_or_price(item_sel) if item_sel else 0.0
                        found_name = prod.get("productName") or nombre

                        if price_num <= 0:
                            pid = str(prod.get("productId") or "").strip()
                            if pid:
                                v_name, v_price = vt_variations_price(s, pid, refid, sc_primary.strip(), headers_cm)
                                if v_price:
                                    price_num = v_price
                                    found_name = v_name or found_name

                        if price_num > 0:
                            found_price = price_num

                    if found_price is not None:
                        # 👇 Nuevo: si el precio supera 1.000.000, marcar "Revisar"
                        if float(found_price) > 1_000_000:
                            row["Precio"] = "Revisar"
                            row["Nombre"] = found_name or nombre
                        else:
                            row["Precio"] = format_ar_price_no_thousands(found_price)
                            row["Nombre"] = found_name or nombre

                except Exception:
                    pass  # dejamos "Revisar"

                resultados.append(row)
                done += 1
                prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")

            df = pd.DataFrame(resultados, columns=["EAN", "RefId", "Nombre", "Precio"])
            st.success("✅ Relevamiento ChangoMás completado")
            st.dataframe(df, use_container_width=True)

            fecha = datetime.now().strftime("%Y-%m-%d")
            st.download_button(
                label="⬇ Descargar CSV (ChangoMás)",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"precios_changomas_{fecha}.csv",
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
# 🟢 Jumbo
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

# ============================================
# 🟢 Vea
# ============================================
with tab_vea:
    st.subheader("Vea · Relevamiento por EAN (VTEX)")
    st.caption("Consulta por **EAN** y toma **Installments[].Value** del primer item/seller. Sin cookie.")

    HEADERS_VEA = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
    }

    if st.button("Ejecutar relevamiento (VEA)"):
        with st.spinner("⏳ Relevando Vea..."):
            resultados = []
            for nombre, datos in productos.items():
                ean = str(datos.get("ean") or "").strip()
                try:
                    if not ean:
                        resultados.append({"EAN": "", "Nombre": nombre, "Precio": "Revisar"})
                        continue

                    # VTEX search por EAN
                    url = f"https://www.vea.com.ar/api/catalog_system/pub/products/search?fq=alternateIds_Ean:{ean}"
                    r = requests.get(url, headers=HEADERS_VEA, timeout=12)
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
            st.success("✅ Relevamiento Vea completado")
            st.dataframe(df, use_container_width=True)

            fecha = datetime.now().strftime("%Y-%m-%d")
            st.download_button(
                label="⬇ Descargar CSV (Vea)",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"precios_vea_{fecha}.csv",
                mime="text/csv",
            )
# ============================================
# 🟡 Cooperativa Obrera (ListPrice + Price)
# ============================================
with tab_coope:
    st.subheader("Cooperativa Obrera · Relevamiento por cod_coope")
    st.caption("Consulta el endpoint oficial y devuelve **ListPrice (precio_anterior)** y **Price (precio)**.")

    import requests
    import pandas as pd
    from datetime import datetime

    # ✅ nuevo origen del listado
    # listado_cooperativa.py debe exponer un dict (ej: productos = {...})
    from listado_cooperativa import productos

    HEADERS_COOPE = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
    }

    def _is_no_encontrado(cod: str) -> bool:
        """
        Normaliza casos tipo: 'NO_ENCONTRADO', 'no_encontrado ', 'No Encontrado', etc.
        """
        c = (cod or "").strip().upper()
        c = c.replace(" ", "_")
        return c == "NO_ENCONTRADO" or c == "NO" or c == "NO_ENCONTRADO,"  # tolerancia

    def _to_float(x):
        try:
            if x in (None, ""):
                return 0.0
            return float(str(x))
        except Exception:
            return 0.0

    if st.button("🟡 Ejecutar relevamiento (Cooperativa Obrera)"):
        with st.spinner("⏳ Relevando Cooperativa Obrera..."):
            resultados = []

            for nombre, meta in productos.items():
                empresa = str(meta.get("empresa", "")).strip()
                categoria = str(meta.get("categoría", "")).strip()
                subcategoria = str(meta.get("subcategoría", "")).strip()
                marca = str(meta.get("marca", "")).strip()
                ean = str(meta.get("ean", "")).strip()

                # ✅ soporta ambas llaves por robustez (cod_coope / cod_coop)
                cod = str(meta.get("cod_coope", meta.get("cod_coop", ""))).strip()

                # ✅ fila base requerida
                row = {
                    "Empresa": empresa,
                    "Categoría": categoria,
                    "Subcategoría": subcategoria,
                    "Marca": marca,
                    "Nombre": nombre,
                    "EAN": ean,
                    "ListPrice": "Revisar",  # precio_anterior
                    "Price": "Revisar",      # precio
                }

                # ✅ Regla: si NO_ENCONTRADO -> Revisar
                if (not cod) or _is_no_encontrado(cod):
                    resultados.append(row)
                    continue

                try:
                    url = "https://api.lacoopeencasa.coop/api/articulo/detalle"
                    params = {"cod_interno": cod, "simple": "false"}

                    r = requests.get(url, params=params, headers=HEADERS_COOPE, timeout=12)
                    r.raise_for_status()

                    ctype = (r.headers.get("content-type", "") or "").lower()
                    j = r.json() if ctype.startswith("application/json") else {}

                    datos_node = (j or {}).get("datos") or {}

                    # ✅ ListPrice = precio_anterior
                    lp_raw = datos_node.get("precio_anterior")
                    # ✅ Price = precio
                    pr_raw = datos_node.get("precio")

                    lp = _to_float(lp_raw)
                    pr = _to_float(pr_raw)

                    # Si vienen válidos, los mostramos formateados
                    if lp > 0:
                        row["ListPrice"] = format_ar_price_no_thousands(lp)
                    if pr > 0:
                        row["Price"] = format_ar_price_no_thousands(pr)

                except Exception:
                    # Si falla, se queda en "Revisar"
                    pass

                resultados.append(row)

            df = pd.DataFrame(
                resultados,
                columns=["Empresa", "Categoría", "Subcategoría", "Marca", "Nombre", "EAN", "ListPrice", "Price"],
            )

            st.success("✅ Relevamiento Cooperativa Obrera completado")
            st.dataframe(df, use_container_width=True)

            # (Opcional) descarga CSV, lo dejo porque ya estaba en tu flujo
            fecha = datetime.now().strftime("%Y-%m-%d")
            st.download_button(
                label="⬇ Descargar CSV (Cooperativa Obrera)",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"precios_cooperativa_{fecha}.csv",
                mime="text/csv",
            )


# ============================================
# 🔴 HiperLibertad (ListPrice por EAN)
# ============================================
with tab_hiper:
    st.subheader("HiperLibertad · ListPrice por EAN")

    BASE_HIPER = "https://www.hiperlibertad.com.ar"
    SC_DEFAULT = "1"  # política comercial usual (?sc=1)
    HEADERS_HIPER = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PythonRequests/2.x",
        "Accept": "application/json, text/plain, */*",
    }
    TIMEOUT = (3, 8)  # (connect, read) — timeouts optimizados

    def _fetch_catalog_by_ean(ean: str, sc: str = SC_DEFAULT):
        if not ean:
            return None
        url = f"{BASE_HIPER}/api/catalog_system/pub/products/search"
        params = {"fq": f"alternateIds_Ean:{ean}", "sc": sc}
        r = requests.get(url, headers=HEADERS_HIPER, params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        try:
            js = r.json()
            return js if isinstance(js, list) and js else None
        except Exception:
            return None

    def _extract_list_price_only(js) -> float:
        try:
            # Prioridad: primer ListPrice > 0
            for prod in js:
                for item in (prod.get("items") or []):
                    for seller in (item.get("sellers") or []):
                        co = seller.get("commertialOffer") or {}
                        lp = co.get("ListPrice")
                        if isinstance(lp, (int, float)) and lp > 0:
                            return float(lp)
            # Si no hubo >0, devolver 0 si hay numérico
            for prod in js:
                for item in (prod.get("items") or []):
                    for seller in (item.get("sellers") or []):
                        co = seller.get("commertialOffer") or {}
                        lp = co.get("ListPrice")
                        if isinstance(lp, (int, float)):
                            return float(lp)  # probablemente 0.0
        except Exception:
            pass
        return 0.0

    if st.button("🔎 Ejecutar relevamiento (HiperLibertad)"):
        with st.spinner("⏳ Relevando HiperLibertad..."):
            filas = []
            total = len(productos)
            prog = st.progress(0, text="Procesando…")

            for i, (nombre, meta) in enumerate(productos.items(), start=1):
                ean = str(meta.get("ean", "")).strip()
                try:
                    js = _fetch_catalog_by_ean(ean, sc=SC_DEFAULT)
                    if js:
                        lp = _extract_list_price_only(js)
                        precio_fmt = format_ar_price_no_thousands(lp) if lp is not None else "0,00"
                    else:
                        precio_fmt = "Revisar"
                except Exception:
                    precio_fmt = "Revisar"

                filas.append({"EAN": ean, "Nombre": nombre, "ListPrice": precio_fmt})
                prog.progress(i / max(1, total), text=f"Procesando… {i}/{total}")

            dfh = pd.DataFrame(filas, columns=["EAN", "Nombre", "ListPrice"])
            st.success("✅ Relevamiento HiperLibertad completado")
            st.dataframe(dfh, use_container_width=True)

            fecha = datetime.now().strftime("%Y-%m-%d")
            st.download_button(
                "⬇ Descargar CSV (HiperLibertad)",
                dfh.to_csv(index=False).encode("utf-8"),
                file_name=f"precios_hiperlibertad_{fecha}.csv",
                mime="text/csv",
            )







