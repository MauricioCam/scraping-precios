import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# ============================================
# Config app
# ============================================
st.set_page_config(page_title="📊 Relevamiento de Precios", layout="wide")
st.title("📊 Relevamiento de Precios")
st.caption("Esta herramienta tiene por objetivo relevar los precios de todo el portfolio de forma automática")

# ============================================
# Datos de entrada (Carrefour)
# ============================================
from listado_carrefour import productos  # {"Nombre": {"empresa": "...", "categoría": "...", ... , "ean": "..."}}

# ============================================
# Utilidades comunes
# ============================================
def format_ar_price_no_thousands(value):
    """1795.0 -> '1795,00' (sin separador de miles)."""
    if value is None:
        return None
    return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", "")

# ============================================
# Pestañas
# ============================================
tab_carrefour, tab_dia, tab_chango, tab_coto, tab_jumbo, tab_vea, tab_coope, tab_hiper = st.tabs(
    ["🛒 Carrefour", "🟥 Día", "🟢 ChangoMás", "🏷️ Coto", "🟢 Jumbo", "🟢 Vea", "🟡 Cooperativa", "🔴 Libertad"]
)

# ============================================
# 🛒 Carrefour (por EAN) — ListPrice + Oferta
# ============================================
with tab_carrefour:
    st.subheader("Carrefour · Hiper Olivos")
    st.write("Relevamiento automático de todos los SKUs, aplicando la sucursal **Hiper Olivos**. (Busca por **EAN**)")

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

    def _safe_float(x, default=0.0) -> float:
        try:
            return float(x)
        except Exception:
            return float(default)

    def _has_tarjeta_carrefour(commertial_offer: dict) -> bool:
        """Detecta promo 'Tarjeta Carrefour 15%' (case-insensitive)."""
        teasers = commertial_offer.get("PromotionTeasers") or []
        for t in teasers:
            name = (t or {}).get("Name") or ""
            if "tarjeta carrefour" in name.lower():
                return True
        return False

    def _extract_teaser_text(commertial_offer: dict) -> str:
        """
        'PROMO-2do al 70% Max 8 unidades ...' -> '2do al 70%'
        """
        teasers = commertial_offer.get("PromotionTeasers") or []
        if not teasers:
            return ""

        raw = str((teasers[0] or {}).get("Name") or "").strip()
        raw_l = raw.lower()

        promo_key = "promo-"
        max_key = " max"

        i = raw_l.find(promo_key)
        if i >= 0:
            start = i + len(promo_key)
            j = raw_l.find(max_key, start)
            if j > start:
                return raw[start:j].strip()

        return raw

    if st.button("🔍 Ejecutar relevamiento (Carrefour)"):
        with st.spinner("⏳ Relevando Carrefour..."):
            resultados = []

            for nombre_base, datos in productos.items():
                empresa = (datos.get("empresa") or "").strip()
                categoria = (datos.get("categoría") or "").strip()
                subcategoria = (datos.get("subcategoría") or "").strip()
                marca = (datos.get("marca") or "").strip()
                ean = str(datos.get("ean") or "").strip()

                row_base = {
                    "Empresa": empresa,
                    "Categoría": categoria,
                    "Subcategoría": subcategoria,
                    "Marca": marca,
                    "Nombre": nombre_base,
                    "EAN": ean,
                    "ListPrice": "Revisar",
                    "Oferta": "Revisar",
                }

                try:
                    if not ean:
                        resultados.append(row_base)
                        continue

                    url = f"https://www.carrefour.com.ar/api/catalog_system/pub/products/search?fq=alternateIds_Ean:{ean}"
                    r = requests.get(url, headers=HEADERS_CARR, timeout=12)
                    data = r.json()

                    if not data:
                        resultados.append(row_base)
                        continue

                    prod = data[0]
                    items = prod.get("items") or []

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
                        resultados.append(row_base)
                        continue

                    offer = item_sel["sellers"][0].get("commertialOffer", {})

                    # 🚨 REGLA PRIORITARIA: Tarjeta Carrefour
                    if _has_tarjeta_carrefour(offer):
                        resultados.append({
                            "Empresa": empresa,
                            "Categoría": categoria,
                            "Subcategoría": subcategoria,
                            "Marca": marca,
                            "Nombre": prod.get("productName") or nombre_base,
                            "EAN": ean,
                            "ListPrice": "Sin Precio",
                            "Oferta": "Sin Precio",
                        })
                        continue

                    list_price = _safe_float(offer.get("ListPrice"), 0)
                    price = _safe_float(offer.get("Price"), 0)

                    list_price_f = format_ar_price_no_thousands(list_price) if list_price > 0 else ""

                    # Lógica de Oferta
                    if price > 0 and list_price > 0 and price != list_price:
                        oferta = format_ar_price_no_thousands(price)
                    else:
                        oferta = _extract_teaser_text(offer)

                    if not list_price_f and not oferta:
                        resultados.append(row_base)
                        continue

                    resultados.append({
                        "Empresa": empresa,
                        "Categoría": categoria,
                        "Subcategoría": subcategoria,
                        "Marca": marca,
                        "Nombre": prod.get("productName") or nombre_base,
                        "EAN": ean,
                        "ListPrice": list_price_f if list_price_f else "Revisar",
                        "Oferta": oferta if oferta else "",
                    })

                except Exception:
                    resultados.append(row_base)

            df = pd.DataFrame(
                resultados,
                columns=["Empresa", "Categoría", "Subcategoría", "Marca", "Nombre", "EAN", "ListPrice", "Oferta"],
            )

            st.success("✅ Relevamiento Carrefour completado")
            st.dataframe(df, use_container_width=True)

            fecha = datetime.now().strftime("%Y-%m-%d")
            st.download_button(
                label="⬇ Descargar CSV (Carrefour)",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"precios_carrefour_{fecha}.csv",
                mime="text/csv",
            )



# ============================================
# 🟥 Día (VTEX) — ListPrice + Oferta (Price vs PromotionTeasers)
# ============================================
with tab_dia:
    st.subheader("Día · Relevamiento por cod_dia (skuId)")
    st.caption(
        "Consulta VTEX por **skuId (cod_dia)** y devuelve **ListPrice** y **Oferta**.\n"
        "Oferta: si **Price != ListPrice** → muestra **Price**; si no → muestra **PromotionTeasers[].Name**."
    )

    # ✅ Nuevo import (reemplaza productos_streamlit.py)
    from listado_dia import productos  # { "Nombre": {empresa,categoría,subcategoría,marca,ean,cod_dia} }

    HEADERS_DIA = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
    }

    def _get_offer_teasers(commertial_offer: dict) -> str:
        """Devuelve los nombres de PromotionTeasers (si existen) en un string."""
        teasers = commertial_offer.get("PromotionTeasers") or []
        names = []
        for t in teasers:
            n = (t or {}).get("Name")
            if n:
                names.append(str(n).strip())
        return " | ".join(names)

    def _safe_float(x, default=0.0) -> float:
        try:
            if x is None:
                return float(default)
            return float(x)
        except Exception:
            return float(default)

    if st.button("🔴 Ejecutar relevamiento (Día)"):
        with st.spinner("⏳ Relevando Día..."):
            resultados = []

            for nombre, datos in productos.items():
                empresa = (datos.get("empresa") or "").strip()
                categoria = (datos.get("categoría") or "").strip()
                subcategoria = (datos.get("subcategoría") or "").strip()
                marca = (datos.get("marca") or "").strip()
                ean = (datos.get("ean") or "").strip()
                cod_dia = str(datos.get("cod_dia") or "").strip()

                # Base row (fallback ante fallas)
                row = {
                    "Empresa": empresa,
                    "Categoría": categoria,
                    "Subcategoría": subcategoria,
                    "Marca": marca,
                    "Nombre": nombre,
                    "EAN": ean,
                    "ListPrice": 0,
                    "Oferta": "Revisar",
                }

                try:
                    if not cod_dia:
                        resultados.append(row)
                        continue

                    # VTEX search por skuId (cod_dia)
                    url = (
                        "https://diaonline.supermercadosdia.com.ar/"
                        f"api/catalog_system/pub/products/search?fq=skuId:{cod_dia}"
                    )

                    r = requests.get(url, headers=HEADERS_DIA, timeout=12)
                    r.raise_for_status()
                    data = r.json()

                    if not data:
                        resultados.append(row)
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
                        resultados.append(row)
                        continue

                    sellers = item_sel.get("sellers") or []
                    if not sellers:
                        resultados.append(row)
                        continue

                    # VTEX lo escribe así: "commertialOffer"
                    comm_offer = sellers[0].get("commertialOffer") or {}

                    list_price = _safe_float(comm_offer.get("ListPrice", 0), 0)
                    price = _safe_float(comm_offer.get("Price", 0), 0)

                    # Guardamos ListPrice (numérico)
                    row["ListPrice"] = list_price

                    # ✅ LÓGICA DE OFERTA
                    # 1) Si Price != ListPrice → Oferta = Price (formateado)
                    # 2) Si Price == ListPrice → Oferta = PromotionTeasers[].Name
                    # (si no hay teasers, queda vacío)
                    if price > 0 and list_price > 0 and price != list_price:
                        row["Oferta"] = format_ar_price_no_thousands(price)
                    else:
                        teasers_txt = _get_offer_teasers(comm_offer)
                        row["Oferta"] = teasers_txt if teasers_txt else ""

                    resultados.append(row)

                except Exception:
                    resultados.append(row)

            df = pd.DataFrame(
                resultados,
                columns=["Empresa", "Categoría", "Subcategoría", "Marca", "Nombre", "EAN", "ListPrice", "Oferta"],
            )

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
# 🟢 ChangoMás (por EAN + Oferta optimizada + Cache checkout por EAN)
# ============================================
with tab_chango:
    st.subheader("ChangoMás · Relevamiento por EAN (VTEX + Checkout)")
    st.caption(
        "Busca por **EAN** en VTEX Search. "
        "**ListPrice** sale de `commertialOffer.ListPrice`. "
        "**Oferta**: si `Price < ListPrice` muestra `% off`; si no, detecta mecánicas vía Checkout (2da al %, 3x2 y opcional 4x2). "
        "Incluye **cache por EAN** del resultado de Checkout (dependiente de vtex_segment/sc)."
    )

    # Datos de entrada (ChangoMás)
    from listado_chango import productos  # {"Nombre": {"empresa": "...", "categoría": "...", "subcategoría": "...", "marca": "...", "ean": "..."}}

    # Parámetros
    DEFAULT_SEGMENT = (
        "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZWwiOiIxIiwicHJpY2VUYWJsZXMiOm51bGwsInJlZ2lvbklkIjoidjIuNDdERkY5REI3QkE5NEEyMEI1ODRGRjYzQTA3RUIxQ0EiLCJ1dG1fY2FtcGFpZ24iOm51bGwsInV0bV9zb3VyY2UiOm51bGwsInV0bWlfY2FtcGFpZ24iOm51bGwsImN1cnJlbmN5Q29kZSI6IkFSUyIsImN1cnJlbmN5U3ltYm9sIjoiJCIsImNvdW50cnlDb2RlIjoiQVJHIiwiY3VsdHVyZUluZm8iOiJlcy1BUiIsImNoYW5uZWxQcml2YWN5IjoicHVibGljIn0"
    )
    vtex_segment = st.text_input("vtex_segment (ChangoMás)", value=DEFAULT_SEGMENT, type="password")
    sc_primary = st.text_input("Sales channel (sc)", value="1", help="Canal de ventas VTEX, ej: 1")

    # Performance knobs
    try_4x2 = st.checkbox("Detectar ofertas 4x2 (1 request extra por producto sin oferta)", value=True)
    show_debug_cm = st.checkbox("Mostrar requests (debug)", value=False)

    # ✅ Cache de ofertas (checkout) por EAN + vtex_segment + sc + try_4x2
    if "chango_checkout_cache" not in st.session_state:
        st.session_state["chango_checkout_cache"] = {}  # {(ean, vtex_segment, sc, try_4x2): oferta_str}

    if st.button("🧹 Limpiar cache de ofertas (ChangoMás)"):
        st.session_state["chango_checkout_cache"] = {}
        st.success("Cache de checkout limpiada.")

    # Constantes
    BASE_CM = "https://www.masonline.com.ar"
    TIMEOUTS = (3, 20)  # (connect, read)

    # --------------------------------------------
    # Helpers
    # --------------------------------------------
    def compute_percent_off(list_price: float, price: float):
        """Devuelve % off entero si price < list_price."""
        try:
            if list_price > 0 and price > 0 and price < list_price:
                pct = round((1 - (price / list_price)) * 100)
                return int(pct) if pct > 0 else None
        except Exception:
            pass
        return None

    def simplify_offer_text(text: str) -> str:
        """
        Resumen:
        - NxM (3x2, 4x2) -> '3x2'
        - '2da/2do al XX%' -> '2da al 50%'
        - fallback -> texto completo
        """
        import re
        if not text:
            return ""

        m = re.search(r"\b(\d+\s*x\s*\d+)\b", text, flags=re.IGNORECASE)
        if m:
            return m.group(1).replace(" ", "")

        m2 = re.search(r"\b(2da|2do)\b.*?\b(al)\b.*?(\d{1,3}\s*%)", text, flags=re.IGNORECASE)
        if m2:
            frag = m2.group(0)
            frag = re.split(r"\b(Reg|SURTIDO|NACIONAL|Max|LLEVANDO)\b", frag, flags=re.IGNORECASE)[0]
            return " ".join(frag.split()).strip()

        return text.strip()

    def vt_search_by_ean(session: requests.Session, ean: str, sc: str, headers: dict):
        url = f"{BASE_CM}/api/catalog_system/pub/products/search"

        # 1) alternateIds_Ean
        params = {"fq": f"alternateIds_Ean:{ean}", "sc": sc}
        r = session.get(url, headers=headers, params=params, timeout=TIMEOUTS)
        if show_debug_cm:
            st.text(f"SEARCH altEan: {r.url} | {r.status_code}")
        r.raise_for_status()
        data = r.json()
        if data:
            return data, r.url

        # 2) fallback ean
        params = {"fq": f"ean:{ean}", "sc": sc}
        r = session.get(url, headers=headers, params=params, timeout=TIMEOUTS)
        if show_debug_cm:
            st.text(f"SEARCH ean: {r.url} | {r.status_code}")
        r.raise_for_status()
        return r.json(), r.url

    def pick_item_by_ean(items: list, ean: str):
        ean = str(ean).strip()
        for it in items or []:
            if str(it.get("ean") or "").strip() == ean:
                return it
            for ref in (it.get("referenceId") or []):
                if str(ref.get("Value") or "").strip() == ean:
                    return it
        return items[0] if items else None

    # --------------------------------------------
    # ✅ Checkout optimizado (1 carrito + updates)
    # --------------------------------------------
    def create_orderform(session: requests.Session, headers: dict):
        url = f"{BASE_CM}/api/checkout/pub/orderForm"
        r = session.post(url, headers=headers, json={}, timeout=TIMEOUTS)
        if show_debug_cm:
            st.text(f"ORDERFORM create: {r.status_code}")
        r.raise_for_status()
        return r.json()

    def add_item_orderform(session: requests.Session, orderform_id: str, sku_id: str, seller_id: str, qty: int, headers: dict):
        url = f"{BASE_CM}/api/checkout/pub/orderForm/{orderform_id}/items"
        payload = {"orderItems": [{"id": str(sku_id), "quantity": int(qty), "seller": str(seller_id)}]}
        r = session.post(url, headers=headers, json=payload, timeout=TIMEOUTS)
        if show_debug_cm:
            st.text(f"ORDERFORM add qty={qty}: {r.status_code}")
        r.raise_for_status()
        return r.json()

    def update_item_qty(session: requests.Session, orderform_id: str, index: int, qty: int, headers: dict):
        url = f"{BASE_CM}/api/checkout/pub/orderForm/{orderform_id}/items/update"
        payload = {"orderItems": [{"index": int(index), "quantity": int(qty)}]}
        r = session.post(url, headers=headers, json=payload, timeout=TIMEOUTS)
        if show_debug_cm:
            st.text(f"ORDERFORM update idx={index} qty={qty}: {r.status_code}")
        r.raise_for_status()
        return r.json()

    def extract_promos(of: dict):
        rbd = (of.get("ratesAndBenefitsData") or {})
        ids = rbd.get("rateAndBenefitsIdentifiers") or []
        names = []
        for x in ids:
            if isinstance(x, dict):
                n = x.get("name") or x.get("id") or x.get("description")
                if n:
                    names.append(str(n).strip())

        out, seen = [], set()
        for n in names:
            if n not in seen:
                out.append(n)
                seen.add(n)
        return out

    def detect_offer_via_checkout_fast(session: requests.Session, sku_id: str, seller_id: str, headers: dict, try_4: bool):
        """
        Optimización:
        - 1 orderForm por producto
        - add qty=2 (detecta 2da al %)
        - si no hay promo, update qty=3 (detecta 3x2)
        - opcional: update qty=4 (detecta 4x2)
        """
        of0 = create_orderform(session, headers=headers)
        of_id = of0.get("orderFormId")
        if not of_id:
            return ""

        # 1) qty=2
        of = add_item_orderform(session, of_id, sku_id, seller_id, qty=2, headers=headers)
        promos = extract_promos(of)
        if promos:
            simp = [simplify_offer_text(p) for p in promos]
            return " | ".join(dict.fromkeys([s for s in simp if s]))

        # Index del item agregado
        items = of.get("items") or []
        idx = 0
        if items:
            for i, it in enumerate(items):
                if str(it.get("id") or "").strip() == str(sku_id):
                    idx = i
                    break

        # 2) qty=3
        of = update_item_qty(session, of_id, index=idx, qty=3, headers=headers)
        promos = extract_promos(of)
        if promos:
            simp = [simplify_offer_text(p) for p in promos]
            return " | ".join(dict.fromkeys([s for s in simp if s]))

        # 3) qty=4
        if try_4:
            of = update_item_qty(session, of_id, index=idx, qty=4, headers=headers)
            promos = extract_promos(of)
            if promos:
                simp = [simplify_offer_text(p) for p in promos]
                return " | ".join(dict.fromkeys([s for s in simp if s]))

        return ""

    # --------------------------------------------
    # ✅ Cache wrapper (no cambia lógica, solo memoiza)
    # --------------------------------------------
    def get_checkout_offer_cached(
        session: requests.Session,
        ean: str,
        sku_id: str,
        seller_id: str,
        headers: dict,
        sc: str,
        try_4: bool,
    ):
        cache = st.session_state["chango_checkout_cache"]
        key = (str(ean).strip(), str(vtex_segment), str(sc).strip(), bool(try_4))

        if key in cache:
            return cache[key]

        oferta = detect_offer_via_checkout_fast(
            session,
            sku_id=sku_id,
            seller_id=seller_id,
            headers=headers,
            try_4=try_4,
        )
        cache[key] = oferta
        return oferta

    st.markdown(f"**Productos cargados:** {len(productos)} (se espera `ean` en cada ítem)")

    if st.button("🟢 Ejecutar relevamiento (ChangoMás por EAN)"):
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

            sc = sc_primary.strip() or "1"

            for nombre_base, datos in productos.items():
                empresa = (datos.get("empresa") or "").strip()
                categoria = (datos.get("categoría") or "").strip()
                subcategoria = (datos.get("subcategoría") or "").strip()
                marca = (datos.get("marca") or "").strip()
                ean = str(datos.get("ean") or "").strip()

                row = {
                    "Empresa": empresa,
                    "Categoría": categoria,
                    "Subcategoría": subcategoria,
                    "Marca": marca,
                    "Nombre": nombre_base,
                    "EAN": ean,
                    "ListPrice": "Sin Precio",
                    "Oferta": "",
                }

                try:
                    if not ean:
                        resultados.append(row)
                        done += 1
                        prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")
                        continue

                    data, used_url = vt_search_by_ean(s, ean, sc, headers_cm)
                    if not data:
                        resultados.append(row)
                        done += 1
                        prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")
                        continue

                    prod = data[0]
                    items = prod.get("items") or []
                    item_sel = pick_item_by_ean(items, ean)

                    if not item_sel or not item_sel.get("sellers"):
                        resultados.append(row)
                        done += 1
                        prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")
                        continue

                    # Nombre: preferimos API
                    nombre_api = (prod.get("productName") or "").strip()
                    row["Nombre"] = nombre_api if nombre_api else nombre_base

                    seller0 = (item_sel.get("sellers") or [{}])[0]
                    seller_id = str(seller0.get("sellerId") or "1").strip() or "1"
                    co = seller0.get("commertialOffer") or {}

                    list_price = float(co.get("ListPrice") or 0)
                    price = float(co.get("Price") or 0)

                    # ListPrice (columna pedida)
                    row["ListPrice"] = format_ar_price_no_thousands(list_price) if list_price > 0 else "Sin Precio"

                    # 1) Oferta por descuento unitario (% off) si Price < ListPrice
                    pct = compute_percent_off(list_price, price)
                    if pct:
                        row["Oferta"] = f"{pct}% off"
                    else:
                        # 2) Mecánicas vía checkout (optimizado + cacheado): qty=2 -> qty=3 -> opcional qty=4
                        sku_id = str(item_sel.get("itemId") or "").strip()
                        if sku_id:
                            row["Oferta"] = get_checkout_offer_cached(
                                s,
                                ean=ean,
                                sku_id=sku_id,
                                seller_id=seller_id,
                                headers=headers_cm,
                                sc=sc,
                                try_4=try_4x2,
                            )

                    if show_debug_cm:
                        st.text(f"OK {ean} | {used_url}")

                except Exception:
                    pass  # dejamos ListPrice = Sin Precio, Oferta vacío

                resultados.append(row)
                done += 1
                prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")

            df = pd.DataFrame(
                resultados,
                columns=["Empresa", "Categoría", "Subcategoría", "Marca", "Nombre", "EAN", "ListPrice", "Oferta"]
            )

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
# 🧩 Utilidades comunes (necesarias para Coto)
# ============================================
from urllib.parse import urljoin
import requests

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
        if any(k in node for k in ("record.id", "product.repositoryId", "product.displayName", "product.eanPrincipal")):
            yield node
        for v in node.values():
            yield from iter_records(v)
    elif isinstance(node, list):
        for it in node:
            yield from iter_records(it)

# ============================================
# 🏷️ Coto (ListPrice + Oferta texto)
# Oferta = textoDescuento dentro de product.dtoDescuentos
# ============================================
from urllib.parse import urljoin
import requests
import json
import re

# --------------------------------------------
# Utilidades comunes (necesarias para Coto)
# --------------------------------------------
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
        if any(k in node for k in ("record.id", "product.repositoryId", "product.displayName", "product.eanPrincipal")):
            yield node
        for v in node.values():
            yield from iter_records(v)
    elif isinstance(node, list):
        for it in node:
            yield from iter_records(it)

def cast_price(val):
    """Convierte distintos formatos a float. Soporta '1.795,00', '1126.72', '$1126.72c/u', etc."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)

    s = str(val).strip()
    if not s:
        return None

    s = s.replace("c/u", "").replace("c\\u002fu", "")
    s = re.sub(r"[^\d\.,-]", "", s)  # deja solo dígitos y separadores
    if not s:
        return None

    # Caso AR típico: '1.795,00' (miles '.' y decimales ',')
    if s.count(",") == 1 and s.count(".") >= 1 and s.rfind(",") > s.rfind("."):
        s = s.replace(".", "").replace(",", ".")
    # Caso coma decimal sin miles: '649,35'
    elif s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")

    try:
        return float(s)
    except Exception:
        return None

def format_ar_price_no_thousands(value):
    """1795.0 -> '1795,00' (sin separador de miles)."""
    if value is None:
        return None
    return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", "")

def extract_texto_descuento_from_dto_descuentos(dto_descuentos) -> str:
    """
    product.dtoDescuentos suele venir como:
      ["[{\"textoDescuento\":\"70% 2da\", ...}]"]
    Devuelve textoDescuento (string) o "" si no encuentra / viene vacío.
    """
    if dto_descuentos is None:
        return ""

    chunks = dto_descuentos if isinstance(dto_descuentos, list) else [dto_descuentos]

    for ch in chunks:
        if ch is None:
            continue
        s = str(ch).strip()
        if not s:
            continue

        try:
            promos = json.loads(s)
        except Exception:
            continue

        if isinstance(promos, dict):
            promos = [promos]

        if isinstance(promos, list):
            for p in promos:
                if not isinstance(p, dict):
                    continue
                txt = (p.get("textoDescuento") or "").strip()
                # ✅ pedido: si está vacío, devolver vacío (no "Revisar")
                if txt != "":
                    return txt

    return ""


# ============================================
# 🏷️ TAB COTO
# ============================================
with tab_coto:
    st.subheader("Coto · Relevamiento por EAN")
    st.caption("Flujo: búsqueda → record.id → detalle (json) → ListPrice=sku.activePrice | Oferta=textoDescuento (si vacío, vacío)")

    # Datos de entrada (Coto)
    from listado_coto import productos  # {"Nombre": {"empresa": "...", "categoría": "...", "subcategoría": "...", "marca": "...", "ean": "..."}}

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
    show_diag = st.checkbox("Mostrar diagnóstico de items/EAN", value=True)

    def get_record_id_by_ean(session: requests.Session, ean: str, sucursal: str):
        params = {"Dy": "1", "Ntt": ean, "Ntk": "product.eanPrincipal", "idSucursal": sucursal, "format": "json"}
        r = session.get(urljoin(BASE, SEARCH_CATEGORIA), params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

        for rec in iter_records(data):
            e = coerce_first(find_key_recursive(rec, "product.eanPrincipal"))
            if str(e) == str(ean):
                rid = coerce_first(find_key_recursive(rec, "record.id"))
                name = (
                    coerce_first(find_key_recursive(rec, "product.displayName"))
                    or coerce_first(find_key_recursive(rec, "record.title"))
                )
                return rid, (str(name) if name else None)
        return None, None

    def fetch_detail_by_record_id(session: requests.Session, record_id: str, sucursal: str):
        product_url = f"{BASE}/sitios/cdigi/productos/_/R-{record_id}"
        detail_url = f"{product_url}?Dy=1&idSucursal={sucursal}&format=json"

        headers = dict(session.headers)
        headers["Referer"] = product_url
        r = session.get(detail_url, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()

        ean = coerce_first(find_key_recursive(data, "product.eanPrincipal"))
        name = coerce_first(find_key_recursive(data, "product.displayName"))

        # ListPrice = sku.activePrice
        raw_list = coerce_first(find_key_recursive(data, "sku.activePrice"))
        list_price = cast_price(raw_list)

        # ✅ Oferta = textoDescuento dentro de product.dtoDescuentos (si vacío, "")
        dto_desc = coerce_first(find_key_recursive(data, "product.dtoDescuentos"))
        oferta_txt = extract_texto_descuento_from_dto_descuentos(dto_desc)

        return {
            "ean": ean,
            "name": name,
            "list_price": format_ar_price_no_thousands(list_price) if list_price is not None else None,
            "oferta": oferta_txt,  # string, puede ser ""
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

        for it in items:
            nombre_ref = str(it.get("nombre_ref", "")).strip()
            ean = str(it.get("ean", "")).strip()

            empresa = str(it.get("empresa", "") or "").strip()
            categoria = str(it.get("categoría", "") or "").strip()
            subcategoria = str(it.get("subcategoría", "") or "").strip()
            marca = str(it.get("marca", "") or "").strip()

            row = {
                "Empresa": empresa,
                "Categoría": categoria,
                "Subcategoría": subcategoria,
                "Marca": marca,
                "Nombre": nombre_ref,
                "EAN": ean,
                "ListPrice": "Revisar",
                "Oferta": "Revisar",
            }

            try:
                if ean:
                    record_id, name_hint = get_record_id_by_ean(s, ean, sucursal)
                    if record_id:
                        det = fetch_detail_by_record_id(s, record_id, sucursal)

                        row["EAN"] = det.get("ean") or ean
                        row["Nombre"] = det.get("name") or name_hint or nombre_ref

                        if det.get("list_price") is not None:
                            row["ListPrice"] = det.get("list_price")

                        # ✅ Oferta: si viene "", debe quedar ""
                        if det.get("oferta") is not None:
                            row["Oferta"] = det.get("oferta")

                        if return_debug:
                            debug_rows.append({"EAN": row["EAN"], "detail_url": det.get("detail_url")})
            except Exception:
                pass

            out.append(row)
            done += 1
            prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")

        return (out, debug_rows) if return_debug else (out, None)

    if st.button("⚡ Ejecutar relevamiento (Coto)"):
        items = []
        for nombre, meta in productos.items():
            meta = meta or {}
            items.append({
                "nombre_ref": nombre,
                "ean": str(meta.get("ean", "")).strip(),
                "empresa": meta.get("empresa", ""),
                "categoría": meta.get("categoría", ""),
                "subcategoría": meta.get("subcategoría", ""),
                "marca": meta.get("marca", ""),
            })

        if show_diag:
            total_items = len(items)
            with_ean = sum(1 for it in items if str(it.get("ean", "")).strip())
            st.write("Diagnóstico")
            st.write("Total items:", total_items)
            st.write("Items con EAN no vacío:", with_ean)
            st.write("Ejemplo item:", items[0] if items else None)

        if not items:
            st.warning("No hay items válidos en listado_coto.py")
            st.stop()

        # -------------------------
        # PREFLIGHT (1 EAN)
        # -------------------------
        try:
            test = next((it for it in items if str(it.get("ean", "")).strip()), None)
            if not test:
                st.warning("No hay EANs no vacíos para preflight.")
                st.stop()

            st.write("Preflight")
            st.write("EAN:", test["ean"])
            st.write("Sucursal:", (suc or DEFAULT_SUCURSAL))

            sess = requests.Session()
            sess.headers.update(HEADERS_COTO)

            rid, nh = get_record_id_by_ean(sess, test["ean"], (suc or DEFAULT_SUCURSAL))
            st.write("record_id:", rid)
            st.write("name_hint:", nh)

            if rid:
                det = fetch_detail_by_record_id(sess, rid, (suc or DEFAULT_SUCURSAL))
                st.write("Preflight ListPrice:", det.get("list_price"))
                st.write("Preflight Oferta (textoDescuento):", det.get("oferta"))
            else:
                st.warning("Preflight: no se encontró record_id para este EAN.")
        except Exception as ex:
            st.error(f"Preflight error: {type(ex).__name__} -> {ex}")
            st.stop()

        # Relevamiento completo
        rows, dbg = scrape_coto_by_items(items, sucursal=(suc or DEFAULT_SUCURSAL), return_debug=show_debug)

        df = pd.DataFrame(
            rows,
            columns=["Empresa", "Categoría", "Subcategoría", "Marca", "Nombre", "EAN", "ListPrice", "Oferta"]
        )

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
# 🟢 Jumbo (Cencosud / VTEX) — ListPrice + Oferta (unit discount OR search-promotions)
#   ✅ ListPrice = PriceWithoutDiscount (siempre que exista)
#   ✅ Oferta = "% off" si Price < PriceWithoutDiscount; si no, /_v/search-promotions
#   ✅ Ignora commertialOffer.ListPrice (viene en escala errónea en algunos SKUs)
#   ✅ Cachea SOLO checkout/promotions por EAN (no cambia lógica del scraping)
# ============================================
with tab_jumbo:
    st.subheader("Jumbo · Relevamiento por EAN (VTEX + search-promotions)")
    st.caption(
        "ListPrice = **PriceWithoutDiscount**. "
        "Oferta = **% off** si hay descuento unitario (Price < PWD); si no, se obtiene desde **/_v/search-promotions**."
    )

    # Datos de entrada (Cencosud: Jumbo/Vea, etc.)
    from listado_cencosud import productos  # {"Nombre": {"empresa": "...", "categoría": "...", "subcategoría": "...", "marca": "...", "ean": "..."}}

    import json
    import requests

    # 🔒 Config fija (validada)
    BASE_JUMBO = "https://www.jumbo.com.ar"
    SC_JUMBO = "32"
    SELLER_PROMO = "jumboargentinaj5202martinez"
    VTEX_SEGMENT_JUMBO = (
        "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZWwiOiIzMiIsInByaWNlVGFibGVzIjpudWxsLCJyZWdpb25JZCI6bnVsbCwidXRtX2NhbXBhaWduIjpudWxsLCJ1dG1fc291cmNlIjpudWxsLCJ1dG1pX2NhbXBhaWduIjpudWxsLCJjdXJyZW5jeUNvZGUiOiJBUlMiLCJjdXJyZW5jeVN5bWJvbCI6IiQiLCJjb3VudHJ5Q29kZSI6IkFSRyIsImN1bHR1cmVJbmZvIjoiZXMtQVIiLCJjaGFubmVsUHJpdmFjeSI6InB1YmxpYyJ9"
    )

    TIMEOUTS = (4, 18)
    SHOW_DEBUG_JUMBO = st.checkbox("Mostrar debug (Jumbo)", value=False)

    HEADERS_JUMBO = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Cookie": f"vtex_segment={VTEX_SEGMENT_JUMBO}",
    }

    # ✅ Cache SOLO del endpoint /_v/search-promotions (por EAN)
    if "jumbo_promos_cache" not in st.session_state:
        st.session_state["jumbo_promos_cache"] = {}  # {ean: oferta_str}

    if st.button("🧹 Limpiar cache de ofertas (Jumbo)"):
        st.session_state["jumbo_promos_cache"] = {}
        st.success("Cache de search-promotions limpiada.")

    def normalize_money(val):
        """
        Jumbo: Price y PriceWithoutDiscount vienen en pesos (float).
        Aun así, dejamos un normalizador defensivo por si algún caso viene en centavos.
        """
        if val is None:
            return None
        try:
            v = float(val)
        except Exception:
            return None
        if v <= 0:
            return None

        # Heurística defensiva: si parece centavos (muy grande e integer), dividir por 100
        if v > 10000 and float(v).is_integer():
            return v / 100

        return v

    def pct_off(price: float, list_price: float):
        """% off entero si price < list_price."""
        try:
            if price and list_price and price > 0 and list_price > 0 and price < list_price:
                pct = round((1 - (price / list_price)) * 100)
                return int(pct) if pct > 0 else None
        except Exception:
            pass
        return None

    def vt_search_by_ean(session: requests.Session, ean: str):
        """Busca producto por EAN en VTEX catalog_system (alternateIds_Ean y fallback ean)."""
        url = f"{BASE_JUMBO}/api/catalog_system/pub/products/search"

        # 1) alternateIds_Ean
        params = {"fq": f"alternateIds_Ean:{ean}", "sc": SC_JUMBO}
        r = session.get(url, headers=HEADERS_JUMBO, params=params, timeout=TIMEOUTS)
        if SHOW_DEBUG_JUMBO:
            st.text(f"CATALOG altEan: {r.url} | {r.status_code}")
        r.raise_for_status()
        data = r.json()

        # 2) fallback ean
        if not data:
            params = {"fq": f"ean:{ean}", "sc": SC_JUMBO}
            r = session.get(url, headers=HEADERS_JUMBO, params=params, timeout=TIMEOUTS)
            if SHOW_DEBUG_JUMBO:
                st.text(f"CATALOG ean: {r.url} | {r.status_code}")
            r.raise_for_status()
            data = r.json()

        if not data:
            return None, None, None

        prod = data[0]
        items = prod.get("items") or []

        # Elegimos item que matchee EAN (ean o referenceId.Value). Si no, el primero.
        item_sel = None
        for it in items:
            if str(it.get("ean") or "").strip() == str(ean).strip():
                item_sel = it
                break
            for ref in (it.get("referenceId") or []):
                if str(ref.get("Value") or "").strip() == str(ean).strip():
                    item_sel = it
                    break
            if item_sel:
                break
        if not item_sel and items:
            item_sel = items[0]

        return prod, item_sel, (r.url if hasattr(r, "url") else None)

    def fetch_search_promotions(session: requests.Session, sku_id: str, referer: str):
        """POST /_v/search-promotions con {seller, skus:[skuId]}"""
        url = f"{BASE_JUMBO}/_v/search-promotions"
        headers = dict(HEADERS_JUMBO)
        headers["Content-Type"] = "application/json"
        headers["Origin"] = BASE_JUMBO
        headers["Referer"] = referer or (BASE_JUMBO + "/")

        payload = {"seller": SELLER_PROMO, "skus": [str(sku_id)]}
        r = session.post(url, headers=headers, data=json.dumps(payload), timeout=TIMEOUTS)
        if SHOW_DEBUG_JUMBO:
            st.text(f"PROMOS: {url} | {r.status_code} | sku={sku_id}")
        r.raise_for_status()
        return r.json()

    def parse_promo(resp_json: dict, sku_id: str) -> str:
        """Extrae code/name desde promotions.*.promotions[skuId]."""
        sku_id = str(sku_id)
        promos_root = (resp_json.get("promotions") or {})

        for bucket in promos_root.values():
            bucket_promos = (bucket.get("promotions") or {})
            if sku_id in bucket_promos:
                p = bucket_promos[sku_id] or {}
                code = (p.get("code") or "").strip()
                name = (p.get("name") or "").strip()

                if code:
                    return code
                if name:
                    return name.split("|")[0].strip()
        return ""

    def get_offer_cached(session: requests.Session, ean: str, sku_id: str, referer: str) -> str:
        cache = st.session_state["jumbo_promos_cache"]
        ean_key = str(ean).strip()

        if ean_key in cache:
            return cache[ean_key]

        resp = fetch_search_promotions(session, sku_id=sku_id, referer=referer)
        oferta = parse_promo(resp, sku_id=sku_id)

        cache[ean_key] = oferta
        return oferta

    st.markdown(f"**Productos cargados:** {len(productos)} (se espera `ean` en cada ítem)")

    if st.button("🟢 Ejecutar relevamiento (Jumbo)"):
        with st.spinner("⏳ Relevando Jumbo..."):
            s = requests.Session()

            resultados = []
            total = len(productos)
            prog = st.progress(0, text="Procesando…")
            done = 0

            for nombre_base, datos in productos.items():
                # Metadatos del listado
                empresa = (datos.get("empresa") or "").strip()
                categoria = (datos.get("categoría") or "").strip()
                subcategoria = (datos.get("subcategoría") or "").strip()
                marca = (datos.get("marca") or "").strip()
                ean = str(datos.get("ean") or "").strip()

                row = {
                    "Empresa": empresa,
                    "Categoría": categoria,
                    "Subcategoría": subcategoria,
                    "Marca": marca,
                    "Nombre": nombre_base,
                    "EAN": ean,
                    "ListPrice": "Sin Precio",
                    "Oferta": "",
                }

                try:
                    if not ean:
                        resultados.append(row)
                        done += 1
                        prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")
                        continue

                    prod, item_sel, used_url = vt_search_by_ean(s, ean)
                    if not prod or not item_sel or not item_sel.get("sellers"):
                        resultados.append(row)
                        done += 1
                        prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")
                        continue

                    # Nombre: priorizamos API
                    nombre_api = (prod.get("productName") or "").strip()
                    row["Nombre"] = nombre_api if nombre_api else nombre_base

                    co = (item_sel.get("sellers") or [{}])[0].get("commertialOffer") or {}

                    # ✅ Jumbo: PWD es la fuente oficial del precio regular (ListPrice)
                    pwd = normalize_money(co.get("PriceWithoutDiscount"))
                    price = normalize_money(co.get("Price"))

                    list_price_num = pwd if (pwd is not None and pwd > 0) else price
                    row["ListPrice"] = format_ar_price_no_thousands(list_price_num) if list_price_num else "Sin Precio"

                    # ✅ Oferta:
                    oferta = ""

                    # A) Si hay descuento unitario (Price < PWD): mostrar % off
                    if price is not None and pwd is not None and price > 0 and pwd > 0 and price < pwd:
                        p = pct_off(price, pwd)
                        if p:
                            oferta = f"{p}% off"

                    # B) Si no hay descuento unitario: buscar promo externa (search-promotions)
                    if not oferta:
                        sku_id = str(item_sel.get("itemId") or "").strip()
                        link_text = (prod.get("linkText") or "").strip()
                        referer = f"{BASE_JUMBO}/{link_text}/p" if link_text else f"{BASE_JUMBO}/"

                        if sku_id:
                            oferta = get_offer_cached(s, ean=ean, sku_id=sku_id, referer=referer)

                    row["Oferta"] = oferta

                    if SHOW_DEBUG_JUMBO:
                        raw_lp = co.get("ListPrice")
                        st.text(
                            f"OK {ean} | sku={item_sel.get('itemId')} | "
                            f"PWD={co.get('PriceWithoutDiscount')} Price={co.get('Price')} rawLP={raw_lp} | "
                            f"ListPrice(out)={row['ListPrice']} Oferta='{row['Oferta']}'"
                        )
                        st.text(f"URL: {used_url}")

                except Exception:
                    pass  # dejamos ListPrice = Sin Precio, Oferta vacío

                resultados.append(row)
                done += 1
                prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")

            df = pd.DataFrame(
                resultados,
                columns=["Empresa", "Categoría", "Subcategoría", "Marca", "Nombre", "EAN", "ListPrice", "Oferta"]
            )

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
# 🟢 Vea (Cencosud) — Catálogo (VTEX) + Promos (search-promotions)
# ============================================
with tab_vea:
    st.subheader("Vea · Relevamiento por EAN (VTEX + Promos)")
    st.caption(
        "1) Catálogo VTEX por **EAN** (sc=34, con vtex_segment) → **Price** y **PriceWithoutDiscount**.\n"
        "2) Promos por SKU vía **POST /_v/search-promotions** (seller fijo) → **Oferta**.\n"
        "ListPrice = PriceWithoutDiscount. Si hay descuento unitario, Oferta muestra el %."
    )

    # Datos de entrada (Vea) — listado_cencosud.py
    from listado_cencosud import productos  # {"Nombre": {"empresa": "...", "categoría": "...", "subcategoría": "...", "marca": "...", "ean": "..."}}

    # -------------------------
    # Constantes Vea (predeterminadas)
    # -------------------------
    BASE_VEA = "https://www.vea.com.ar"
    SC_VEA = "34"

    # vtex_segment (el que ya nos pasaste para Vea)
    VTEX_SEGMENT_VEA = (
        "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZWwiOiIzNCIsInByaWNlVGFibGVzIjpudWxsLCJyZWdpb25JZCI6IlUxY2phblZ0WW05aGNtZGxiblJwYm1GMk56QXdZMjl5Wkc5aVlUY3dNQT09IiwidXRtX2NhbXBhaWduIjpudWxsLCJ1dG1fc291cmNlIjpudWxsLCJ1dG1pX2NhbXBhaWduIjpudWxsLCJjdXJyZW5jeUNvZGUiOiJBUlMiLCJjdXJyZW5jeVN5bWJvbCI6IiQiLCJjb3VudHJ5Q29kZSI6IkFSRyIsImN1bHR1cmVJbmZvIjoiZXMtQVIiLCJhZG1pbl9jdWx0dXJlSW5mbyI6ImVzLUFSIiwiY2hhbm5lbFByaXZhY3kiOiJwdWJsaWMifQ"
    )

    # Seller promos (reutilizado)
    SELLER_PROMOS_VEA = "jumboargentinaj5202martinez"

    HEADERS_VEA = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Cookie": f"vtex_segment={VTEX_SEGMENT_VEA}",
    }

    PROMOS_HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Content-Type": "application/json",
    }

    TIMEOUT = 12

    # -------------------------
    # Helpers
    # -------------------------
    def _pick_item_by_ean(items: list, ean: str):
        """Selecciona item que matchee por item.ean o por referenceId.Value; fallback: primero."""
        if not items:
            return None
        ean = str(ean).strip()
        for it in items:
            if str(it.get("ean") or "").strip() == ean:
                return it
            for ref in (it.get("referenceId") or []):
                if str(ref.get("Value") or "").strip() == ean:
                    return it
        return items[0]

    def _extract_offer_from_promotions_json(promos_json: dict, sku_id: str):
        """
        Busca la promo para el SKU dentro de:
        promotions -> generic/sgc/jumbo_prime -> promotions -> {sku_id: {...}}
        Devuelve texto de oferta (str) o "".
        """
        if not isinstance(promos_json, dict):
            return ""

        promotions = promos_json.get("promotions") or {}
        if not isinstance(promotions, dict):
            return ""

        for bucket_name in ("generic", "sgc", "jumbo_prime"):
            bucket = promotions.get(bucket_name) or {}
            bpromos = bucket.get("promotions") or {}
            if isinstance(bpromos, dict) and str(sku_id) in bpromos:
                p = bpromos.get(str(sku_id)) or {}
                # Preferimos "code" (ej: "2do al 80%"), si no "name"
                code = (p.get("code") or "").strip()
                name = (p.get("name") or "").strip()
                return code or name or ""
        return ""

    def _compute_unit_discount_pct(list_price: float, price: float) -> str:
        """
        Si hay descuento unitario (Price < PriceWithoutDiscount), devuelve "35%".
        Si no, "".
        """
        try:
            if list_price and price and float(list_price) > 0 and float(price) > 0 and float(price) < float(list_price):
                pct = round((1 - float(price) / float(list_price)) * 100)
                if pct > 0:
                    return f"{pct}%"
        except Exception:
            pass
        return ""

    def fetch_vea_catalog_and_offer(session: requests.Session, ean: str):
        """
        Devuelve:
        - nombre_api
        - sku_id (itemId)
        - list_price_num (PriceWithoutDiscount)
        - offer_text (promo code/name o % descuento unitario)
        """
        # 1) Catálogo (VTEX)
        url = f"{BASE_VEA}/api/catalog_system/pub/products/search"
        params = {"fq": f"alternateIds_Ean:{ean}", "sc": SC_VEA}
        r = session.get(url, headers=HEADERS_VEA, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()

        if not data:
            return None, None, None, ""

        prod = data[0]
        items = prod.get("items") or []
        item_sel = _pick_item_by_ean(items, ean)
        if not item_sel or not item_sel.get("sellers"):
            return (prod.get("productName") or None), None, None, ""

        sku_id = str(item_sel.get("itemId") or "").strip()
        co = (item_sel.get("sellers") or [{}])[0].get("commertialOffer", {}) or {}

        # ✔️ ListPrice real = PriceWithoutDiscount (según tus ejemplos)
        price = co.get("Price")
        pwd = co.get("PriceWithoutDiscount")

        # Normalizamos a float
        try:
            price_num = float(price) if price is not None else None
        except Exception:
            price_num = None
        try:
            pwd_num = float(pwd) if pwd is not None else None
        except Exception:
            pwd_num = None

        # 2) Oferta:
        #   - Si hay descuento unitario: Oferta = "% descuento"
        #   - Si no hay descuento unitario: ir a /_v/search-promotions y buscar promo por SKU
        offer_text = ""
        unit_pct = _compute_unit_discount_pct(pwd_num or 0.0, price_num or 0.0)
        if unit_pct:
            offer_text = unit_pct
        else:
            if sku_id:
                promos_url = f"{BASE_VEA}/_v/search-promotions"
                payload = {"seller": SELLER_PROMOS_VEA, "skus": [sku_id]}
                rp = session.post(promos_url, headers=PROMOS_HEADERS, json=payload, timeout=TIMEOUT)
                rp.raise_for_status()
                offer_text = _extract_offer_from_promotions_json(rp.json(), sku_id)

        nombre_api = (prod.get("productName") or "").strip() or None
        return nombre_api, sku_id, pwd_num, (offer_text or "")

    # -------------------------
    # UI acción
    # -------------------------
    if st.button("🟢 Ejecutar relevamiento (Vea)"):
        with st.spinner("⏳ Relevando Vea..."):
            s = requests.Session()

            resultados = []
            total = len(productos)
            prog = st.progress(0, text="Procesando…")
            done = 0

            for nombre_base, datos in productos.items():
                # Metadatos del listado
                empresa = (datos.get("empresa") or "").strip()
                categoria = (datos.get("categoría") or "").strip()
                subcategoria = (datos.get("subcategoría") or "").strip()
                marca = (datos.get("marca") or "").strip()
                ean = str(datos.get("ean") or "").strip()

                row = {
                    "Empresa": empresa,
                    "Categoría": categoria,
                    "Subcategoría": subcategoria,
                    "Marca": marca,
                    "Nombre": nombre_base,
                    "EAN": ean,
                    "ListPrice": "Sin Precio",
                    "Oferta": "",
                }

                try:
                    if not ean:
                        resultados.append(row)
                        done += 1
                        prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")
                        continue

                    nombre_api, sku_id, list_price_num, offer_text = fetch_vea_catalog_and_offer(s, ean)

                    # Nombre: prioriza API
                    if nombre_api:
                        row["Nombre"] = nombre_api

                    # ListPrice real = PriceWithoutDiscount
                    if list_price_num is not None and float(list_price_num) > 0:
                        row["ListPrice"] = format_ar_price_no_thousands(list_price_num)
                    else:
                        row["ListPrice"] = "Sin Precio"

                    # Oferta (puede ser "", "2do al 80%", "35%")
                    row["Oferta"] = offer_text or ""

                except Exception:
                    # Mantenemos "Sin Precio" y Oferta ""
                    pass

                resultados.append(row)
                done += 1
                prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")

            df = pd.DataFrame(
                resultados,
                columns=["Empresa", "Categoría", "Subcategoría", "Marca", "Nombre", "EAN", "ListPrice", "Oferta"]
            )

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
# 🟡 Cooperativa Obrera (ListPrice + Oferta)
# ============================================
with tab_coope:
    st.subheader("Cooperativa Obrera · Relevamiento por cod_coope")
    st.caption("Consulta el endpoint oficial y devuelve **ListPrice (precio_anterior)** y **Oferta** (texto interpretado: 3x2 / % off / etc.).")

    import re
    import requests
    import pandas as pd
    from datetime import datetime

    # ✅ listado_cooperativa.py debe exponer: productos = { "Nombre": {...} }
    from listado_cooperativa import productos

    HEADERS_COOPE = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
    }

    # -------------------------
    # Helpers
    # -------------------------
    def _is_no_encontrado(cod: str) -> bool:
        c = (cod or "").strip().upper().replace(" ", "_")
        return c in ("NO_ENCONTRADO", "NO", "NO_ENCONTRADO,")

    def _to_float(x):
        try:
            if x in (None, ""):
                return None
            return float(str(x))
        except Exception:
            return None

    def format_ar_price_no_thousands(value):
        """1795.0 -> '1795,00' (sin separador de miles)."""
        if value is None:
            return ""
        return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", "")

    RE_LLEVANDO = re.compile(r"llevando\s+(\d+)", re.I)
    RE_PCT = re.compile(r"(\d+(?:[.,]\d+)?)\s*%", re.I)
    RE_NXM = re.compile(r"\b(\d+)\s*x\s*(\d+)\b", re.I)

    def extract_oferta(datos: dict) -> str:
        """
        Prioridad para 'Oferta':
        1) Inferir Nx(N-1) (ej: n=3 y pct ~ 100/n => 3x2)
        2) % off explícito (campo o texto)
        3) % off implícito por precios (precio vs precio_anterior)
        4) NxM literal en texto
        5) Promo por precio (precio_promo distinto) -> 'Precio promo'
        6) fallback descripcion_promo
        7) si no hay promo -> ''
        """
        if not isinstance(datos, dict):
            return ""

        existe = datos.get("existe_promo")
        existe_bool = str(existe).strip().lower() in ("1", "true", "si", "sí", "s")
        if not existe_bool:
            return ""

        desc = str(datos.get("descripcion_promo") or "").strip()

        # precios para cálculo
        precio = _to_float(datos.get("precio"))
        precio_ant = _to_float(datos.get("precio_anterior"))

        # cantidad_promo (N)
        n = _to_float(datos.get("cantidad_promo"))
        if (n is None or n <= 0) and desc:
            m_n = RE_LLEVANDO.search(desc)
            if m_n:
                n = _to_float(m_n.group(1))

        # descuento % (campo o texto)
        pct = _to_float(datos.get("descuento_porcentaje_promo"))
        if pct is None and desc:
            m_pct = RE_PCT.search(desc)
            if m_pct:
                pct = _to_float(m_pct.group(1).replace(",", "."))

        # 1) Inferir Nx(N-1)
        if n and n >= 2 and pct:
            target = 100.0 / float(n)
            if abs(float(pct) - target) <= 1.0:  # tolerancia
                return f"{int(n)}x{int(n)-1}"

        # 2) % off explícito
        if pct is not None and pct > 0:
            pct_str = str(int(round(pct))) if abs(pct - round(pct)) < 0.05 else f"{pct:.2f}".rstrip("0").rstrip(".")
            return f"{pct_str}% off"

        # 3) % off implícito por precios
        if precio_ant and precio and precio_ant > 0 and precio < precio_ant:
            pct_calc = (1.0 - (precio / precio_ant)) * 100.0
            pct_calc_round = int(round(pct_calc))
            if pct_calc_round > 0:
                return f"{pct_calc_round}% off"

        # 4) NxM literal en texto
        if desc:
            m = RE_NXM.search(desc)
            if m:
                return f"{m.group(1)}x{m.group(2)}"

        # 5) promo por precio
        precio_promo = _to_float(datos.get("precio_promo"))
        if precio_promo is not None and precio_promo > 0:
            if (precio is None) or (abs(precio_promo - precio) > 0.001):
                return "Precio promo"

        # 6) fallback
        return desc or ""

    # -------------------------
    # Run
    # -------------------------
    if st.button("🟡 Ejecutar relevamiento (Cooperativa Obrera)"):
        with st.spinner("⏳ Relevando Cooperativa Obrera..."):
            resultados = []

            for nombre, meta in productos.items():
                meta = meta or {}

                empresa = str(meta.get("empresa", "")).strip()
                categoria = str(meta.get("categoría", "")).strip()
                subcategoria = str(meta.get("subcategoría", "")).strip()
                marca = str(meta.get("marca", "")).strip()
                ean = str(meta.get("ean", "")).strip()

                # ✅ soporta cod_coope o cod_coop
                cod = str(meta.get("cod_coope", meta.get("cod_coop", ""))).strip()

                row = {
                    "Empresa": empresa,
                    "Categoría": categoria,
                    "Subcategoría": subcategoria,
                    "Marca": marca,
                    "Nombre": nombre,
                    "EAN": ean,
                    "ListPrice": "Revisar",
                    "Oferta": "",
                }

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

                    lp = _to_float(datos_node.get("precio_anterior"))
                    pr = _to_float(datos_node.get("precio"))  # no se muestra, pero sirve para calcular % implícito

                    if lp and lp > 0:
                        row["ListPrice"] = format_ar_price_no_thousands(lp)
                    else:
                        row["ListPrice"] = "Revisar"

                    # ✅ Oferta interpretada (3x2, % off, etc.)
                    row["Oferta"] = extract_oferta(datos_node)

                except Exception:
                    pass

                resultados.append(row)

            df = pd.DataFrame(
                resultados,
                columns=["Empresa", "Categoría", "Subcategoría", "Marca", "Nombre", "EAN", "ListPrice", "Oferta"],
            )

            st.success("✅ Relevamiento Cooperativa Obrera completado")
            st.dataframe(df, use_container_width=True)

            fecha = datetime.now().strftime("%Y-%m-%d")
            st.download_button(
                label="⬇ Descargar CSV (Cooperativa Obrera)",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"precios_cooperativa_{fecha}.csv",
                mime="text/csv",
            )




# ============================================
# 🔴 HiperLibertad (VTEX) — ListPrice + Oferta por EAN (catalog + checkout simulation)
# ============================================
with tab_hiper:
    st.subheader("HiperLibertad · Relevamiento por EAN (ListPrice + Oferta)")
    st.caption(
        "1) Busca SKU por **EAN** en catálogo VTEX. "
        "2) Simula checkout (qty=1/2/3) para obtener **ListPrice/Price** y detectar **ofertas** (messages/benefits o % off)."
    )

    import requests
    import pandas as pd
    from datetime import datetime

    # ✅ listado
    from listado_libertad import productos

    BASE_HIPER = "https://www.hiperlibertad.com.ar"
    SC_DEFAULT = "1"  # política comercial usual (?sc=1)

    HEADERS_HIPER = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PythonRequests/2.x",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    }

    TIMEOUT = (3, 10)  # (connect, read)

    # ----------------------------
    # Helpers
    # ----------------------------
    def _safe_int(x, default=0):
        try:
            return int(x)
        except Exception:
            return default

    def _safe_float(x, default=0.0):
        try:
            return float(x)
        except Exception:
            return default

    def _pct_off(list_price: float, selling_price: float) -> int:
        """Devuelve % off redondeado (entero)."""
        try:
            if list_price <= 0 or selling_price <= 0:
                return 0
            if selling_price >= list_price:
                return 0
            return int(round((1.0 - (selling_price / list_price)) * 100))
        except Exception:
            return 0

    def _fetch_catalog_by_ean(session: requests.Session, ean: str, sc: str = SC_DEFAULT):
        """Devuelve (prod, item_sel) o (None, None)."""
        if not ean:
            return None, None

        url = f"{BASE_HIPER}/api/catalog_system/pub/products/search"
        params = {"fq": f"alternateIds_Ean:{ean}", "sc": sc}

        r = session.get(url, headers=HEADERS_HIPER, params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            return None, None

        try:
            data = r.json()
        except Exception:
            return None, None

        if not isinstance(data, list) or not data:
            return None, None

        prod = data[0]
        items = prod.get("items") or []

        # pick: match item.ean; fallback first
        item_sel = None
        for it in items:
            if str(it.get("ean") or "").strip() == ean:
                item_sel = it
                break
        if not item_sel and items:
            item_sel = items[0]

        return prod, item_sel

    def _simulate_checkout(session: requests.Session, sku_id: str, seller_id: str = "1", sc: str = SC_DEFAULT, qty: int = 1):
        """
        VTEX checkout simulation.
        Devuelve json o None.
        """
        url = f"{BASE_HIPER}/api/checkout/pub/orderForms/simulation"
        params = {"sc": sc}
        payload = {"items": [{"id": str(sku_id), "quantity": int(qty), "seller": str(seller_id)}], "country": "ARG"}

        r = session.post(url, headers=HEADERS_HIPER, params=params, json=payload, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        try:
            return r.json()
        except Exception:
            return None

    def _extract_offer_text_from_sim(sim_json) -> str:
        """
        Oferta desde:
        - messages[]
        - ratesAndBenefitsData.rateAndBenefitsIdentifiers[].name
        """
        if not isinstance(sim_json, dict):
            return ""

        # 1) messages (lo más directo)
        msgs = sim_json.get("messages")
        if isinstance(msgs, list) and msgs:
            clean = [str(m).strip() for m in msgs if str(m).strip()]
            if clean:
                # evitamos textos repetidos
                uniq = []
                for x in clean:
                    if x not in uniq:
                        uniq.append(x)
                return " | ".join(uniq)

        # 2) rateAndBenefitsIdentifiers
        rbd = sim_json.get("ratesAndBenefitsData") or {}
        ids = rbd.get("rateAndBenefitsIdentifiers")
        if isinstance(ids, list) and ids:
            names = []
            for it in ids:
                if isinstance(it, dict):
                    nm = str(it.get("name") or "").strip()
                    if nm:
                        names.append(nm)
            if names:
                uniq = []
                for x in names:
                    if x not in uniq:
                        uniq.append(x)
                return " | ".join(uniq)

        return ""

    def _extract_unit_prices_from_sim(sim_json):
        """
        En simulation, items vienen en centavos:
        - items[0].listPrice
        - items[0].sellingPrice
        - items[0].price (a veces = listPrice)
        Devuelve (list_price, selling_price) en ARS (float).
        """
        if not isinstance(sim_json, dict):
            return 0.0, 0.0

        items = sim_json.get("items")
        if not isinstance(items, list) or not items:
            return 0.0, 0.0

        it0 = items[0] if isinstance(items[0], dict) else {}
        lp_cents = _safe_int(it0.get("listPrice"), 0)
        sp_cents = _safe_int(it0.get("sellingPrice"), 0)

        # pasar a ARS
        lp = lp_cents / 100.0 if lp_cents else 0.0
        sp = sp_cents / 100.0 if sp_cents else 0.0
        return lp, sp

    # ----------------------------
    # UI
    # ----------------------------
    if st.button("🔴 Ejecutar relevamiento (HiperLibertad)"):
        with st.spinner("⏳ Relevando HiperLibertad..."):
            s = requests.Session()

            resultados = []
            total = len(productos)
            prog = st.progress(0, text="Procesando…")
            done = 0

            for nombre, meta in productos.items():
                empresa = str(meta.get("empresa", "")).strip()
                categoria = str(meta.get("categoría", "")).strip()
                subcategoria = str(meta.get("subcategoría", "")).strip()
                marca = str(meta.get("marca", "")).strip()
                ean = str(meta.get("ean", "")).strip()

                row = {
                    "Empresa": empresa,
                    "Categoría": categoria,
                    "Subcategoría": subcategoria,
                    "Marca": marca,
                    "Nombre": nombre,
                    "EAN": ean,
                    "ListPrice": "Revisar",
                    "Oferta": "",
                }

                try:
                    if not ean:
                        resultados.append(row)
                        done += 1
                        prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")
                        continue

                    prod, item_sel = _fetch_catalog_by_ean(s, ean, sc=SC_DEFAULT)
                    if not prod or not item_sel:
                        resultados.append(row)
                        done += 1
                        prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")
                        continue

                    sku_id = str(item_sel.get("itemId") or "").strip()
                    if not sku_id:
                        resultados.append(row)
                        done += 1
                        prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")
                        continue

                    # Nombre real si existe
                    row["Nombre"] = str(prod.get("productName") or nombre).strip()

                    # 1) checkout qty=1: base prices
                    sim1 = _simulate_checkout(s, sku_id, seller_id="1", sc=SC_DEFAULT, qty=1)
                    lp1, sp1 = _extract_unit_prices_from_sim(sim1)

                    if lp1 > 0:
                        row["ListPrice"] = format_ar_price_no_thousands(lp1)

                    # 2) checkout qty=2/3: buscar mensajes de promo
                    sim2 = _simulate_checkout(s, sku_id, seller_id="1", sc=SC_DEFAULT, qty=2)
                    sim3 = _simulate_checkout(s, sku_id, seller_id="1", sc=SC_DEFAULT, qty=3)

                    offer_txt = _extract_offer_text_from_sim(sim2) or _extract_offer_text_from_sim(sim3)

                    # 3) si no hay mensajes/beneficios, inferir % off por diferencia lp vs sp en qty=1
                    if not offer_txt:
                        pct = _pct_off(lp1, sp1)
                        if pct > 0:
                            offer_txt = f"{pct}% off"

                    row["Oferta"] = offer_txt

                except Exception:
                    # dejar Revisar / vacío
                    pass

                resultados.append(row)
                done += 1
                prog.progress(done / max(1, total), text=f"Procesando… {done}/{total}")

            df = pd.DataFrame(
                resultados,
                columns=["Empresa", "Categoría", "Subcategoría", "Marca", "Nombre", "EAN", "ListPrice", "Oferta"],
            )

            st.success("✅ Relevamiento HiperLibertad completado")
            st.dataframe(df, use_container_width=True)

            fecha = datetime.now().strftime("%Y-%m-%d")
            st.download_button(
                label="⬇ Descargar CSV (HiperLibertad)",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"precios_hiperlibertad_{fecha}.csv",
                mime="text/csv",
            )

















