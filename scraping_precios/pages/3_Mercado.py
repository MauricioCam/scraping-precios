# app_relevar_mercado.py
# Streamlit — “Relevar Mercado” (ListPrice por cadena)
# Cambios (última iteración):
# 1) TODAS las celdas con fondo blanco (sin bandas)
# 2) Resumen por Categoría (Index vs PSP): agrega círculo a la izquierda del número:
#    - Index >= 99  -> 🟢
#    - 95 <= Index < 99 -> 🟡
#    - Index < 95 -> 🔴
# FIX: evita el error "AttributeError: module 'pandas.io.formats' has no attribute 'style'"
#      removiendo el type-hint pd.io.formats.style.Styler (ruta interna no estable).

import time
import re
from datetime import datetime

import pandas as pd
import requests
import streamlit as st


# =========================
# Config
# =========================
st.set_page_config(page_title="📊 Relevamiento de Mercado", layout="wide")
st.title("📊 Relevar Mercado")
st.caption("Consulta el **ListPrice** del mismo listado de EANs en todas las cadenas.")

TIMEOUT = (4, 18)
DISPERSION_THRESHOLD_ARS = 500
WHITE_BG = "#FFFFFF"


# =========================
# Input único
# =========================
from consolidado_comparativos import productos
st.markdown(f"**Productos cargados:** {len(productos)}")


# =========================
# Utils comunes
# =========================
def format_ar_price_no_decimals(value):
    """1795.0 -> '1795' (sin miles, sin decimales)."""
    if value is None:
        return ""
    try:
        v = float(value)
        if v <= 0:
            return ""
        return str(int(round(v)))
    except Exception:
        return ""


def safe_float(x):
    try:
        if x is None or x == "":
            return None
        return float(x)
    except Exception:
        return None


def parse_price_int(s: str):
    """'3899' -> 3899 (int)"""
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    try:
        return int(float(s))
    except Exception:
        return None


def pick_item_by_ean(items, ean: str):
    ean = str(ean).strip()
    for it in items or []:
        if str(it.get("ean") or "").strip() == ean:
            return it
        for ref in (it.get("referenceId") or []):
            if str(ref.get("Value") or "").strip() == ean:
                return it
    return items[0] if items else None


# =========================
# Fetchers por cadena (ListPrice)
# =========================
def fetch_carrefour_listprice(session: requests.Session, ean: str) -> str:
    COOKIE_SEGMENT = (
        "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZWwiOiIxIiwicHJpY2VUYWJsZXMiOm51bGwsInJlZ2lvbklkIjpudWxsLCJ1dG1fY2FtcGFpZ24iOm51bGws"
        "InV0bV9zb3VyY2UiOm51bGwsInV0bWlfY2FtcGFpZ24iOm51bGwsImN1cnJlbmN5Q29kZSI6IkFSUyIsImN1cnJlbmN5U3ltYm9sIjoiJCIsImNvdW50"
        "cnlDb2RlIjoiQVJHIiwiY3VsdHVyZUluZm8iOiJlcy1BUiIsImFkbWluX2N1dHR1cmVJbmZvIjoiZXMtQVIiLCJjaGFubmVsUHJpdmFjeSI6InB1YmxpYyJ9"
    )
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Cookie": f"vtex_segment={COOKIE_SEGMENT}",
    }
    url = "https://www.carrefour.com.ar/api/catalog_system/pub/products/search"
    r = session.get(url, headers=headers, params={"fq": f"alternateIds_Ean:{ean}"}, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if not data:
        return ""
    prod = data[0]
    item = pick_item_by_ean(prod.get("items") or [], ean)
    if not item:
        return ""
    sellers = item.get("sellers") or []
    if not sellers:
        return ""
    co = sellers[0].get("commertialOffer") or {}
    lp = safe_float(co.get("ListPrice"))
    return format_ar_price_no_decimals(lp)


def fetch_dia_listprice(session: requests.Session, cod_dia: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json,text/plain,*/*"}
    url = "https://diaonline.supermercadosdia.com.ar/api/catalog_system/pub/products/search"
    r = session.get(url, headers=headers, params={"fq": f"skuId:{cod_dia}"}, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if not data:
        return ""
    prod = data[0]
    items = prod.get("items") or []
    item = None
    for it in items:
        if str(it.get("itemId") or "").strip() == str(cod_dia).strip():
            item = it
            break
    if not item and items:
        item = items[0]
    if not item:
        return ""
    sellers = item.get("sellers") or []
    if not sellers:
        return ""
    co = sellers[0].get("commertialOffer") or {}
    lp = safe_float(co.get("ListPrice"))
    return format_ar_price_no_decimals(lp)


def fetch_chango_listprice(session: requests.Session, ean: str) -> str:
    BASE_CM = "https://www.masonline.com.ar"
    DEFAULT_SEGMENT = (
        "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZWwiOiIxIiwicHJpY2VUYWJsZXMiOm51bGwsInJlZ2lvbklkIjoidjIuNDdERkY5REI3QkE5NEEyMEI1ODRGRjYzQTA3RUIxQ0EiLCJ1dG1fY2FtcGFpZ24iOm51bGwsInV0bV9zb3VyY2UiOm51bGwsInV0bWlfY2FtcGFpZ24iOm51bGwsImN1cnJlbmN5Q29kZSI6IkFSUyIsImN1cnJlbmN5U3ltYm9sIjoiJCIsImNvdW50cnlDb2RlIjoiQVJHIiwiY3VsdHVyZUluZm8iOiJlcy1BUiIsImNoYW5uZWxQcml2YWN5IjoicHVibGljIn0"
    )
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Cookie": f"vtex_segment={DEFAULT_SEGMENT}",
    }

    url = f"{BASE_CM}/api/catalog_system/pub/products/search"
    ean = str(ean).strip()
    sc = "1"

    attempts = [
        {"fq": f"alternateIds_Ean:{ean}", "sc": sc},
        {"fq": f"alternateIds_RefId:{ean}", "sc": sc},
        {"ft": ean, "sc": sc},
    ]

    for params in attempts:
        r = session.get(url, headers=headers, params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            continue
        try:
            data = r.json()
        except Exception:
            continue
        if not isinstance(data, list) or not data:
            continue

        prod = data[0] or {}
        items = prod.get("items") or []
        item = pick_item_by_ean(items, ean) or (items[0] if items else None)
        if not item:
            return ""

        sellers = item.get("sellers") or []
        if not sellers:
            return ""

        co = sellers[0].get("commertialOffer") or {}
        lp = safe_float(co.get("ListPrice"))
        return format_ar_price_no_decimals(lp)

    return ""


# ---- Coto helpers ----
def cast_price(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)

    s = str(val).strip()
    if not s:
        return None

    s = s.replace("c/u", "").replace("c\\u002fu", "")
    s = re.sub(r"[^\d\.,-]", "", s)
    if not s:
        return None

    if s.count(",") == 1 and s.count(".") >= 1 and s.rfind(",") > s.rfind("."):
        s = s.replace(".", "").replace(",", ".")
    elif s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")

    try:
        return float(s)
    except Exception:
        return None


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


def coerce_first(x):
    return (x[0] if isinstance(x, list) and x else x)


def iter_records(node):
    if isinstance(node, dict):
        if any(k in node for k in ("record.id", "product.repositoryId", "product.displayName", "product.eanPrincipal")):
            yield node
        for v in node.values():
            yield from iter_records(v)
    elif isinstance(node, list):
        for it in node:
            yield from iter_records(it)


def fetch_coto_listprice(session: requests.Session, ean: str, sucursal: str = "200") -> str:
    BASE = "https://www.cotodigital.com.ar"
    SEARCH = f"{BASE}/sitios/cdigi/categoria"

    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "DNT": "1",
        "Referer": BASE + "/",
        "Origin": BASE,
    })

    # warm-up cookies
    try:
        session.get(BASE + "/", timeout=TIMEOUT)
    except Exception:
        pass

    params = {"Dy": "1", "Ntt": ean, "Ntk": "product.eanPrincipal", "idSucursal": sucursal, "format": "json"}
    r = session.get(SEARCH, params=params, timeout=TIMEOUT)
    if r.status_code == 403:
        return ""
    r.raise_for_status()
    data = r.json()

    record_id = None
    for rec in iter_records(data):
        e = coerce_first(find_key_recursive(rec, "product.eanPrincipal"))
        if str(e) == str(ean):
            record_id = coerce_first(find_key_recursive(rec, "record.id"))
            break
    if not record_id:
        return ""

    product_url = f"{BASE}/sitios/cdigi/productos/_/R-{record_id}"
    detail_url = f"{product_url}?Dy=1&idSucursal={sucursal}&format=json"

    headers_detail = dict(session.headers)
    headers_detail["Referer"] = product_url

    r2 = session.get(detail_url, headers=headers_detail, timeout=TIMEOUT)
    if r2.status_code == 403:
        return ""
    r2.raise_for_status()

    det = r2.json()
    raw_list = coerce_first(find_key_recursive(det, "sku.activePrice"))
    lp = cast_price(raw_list)
    return format_ar_price_no_decimals(lp)


def fetch_jumbo_listprice(session: requests.Session, ean: str) -> str:
    BASE = "https://www.jumbo.com.ar"
    SC = "32"
    VTEX_SEGMENT = (
        "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZWwiOiIzMiIsInByaWNlVGFibGVzIjpudWxsLCJyZWdpb25JZCI6bnVsbCwidXRtX2NhbXBhaWduIjpudWxsLCJ1dG1fc291cmNlIjpudWxsLCJ1dG1pX2NhbXBhaWduIjpudWxsLCJjdXJyZW5jeUNvZGUiOiJBUlMiLCJjdXJyZW5jeVN5bWJvbCI6IiQiLCJjb3VudHJ5Q29kZSI6IkFSRyIsImN1bHR1cmVJbmZvIjoiZXMtQVIiLCJjaGFubmVsUHJpdmFjeSI6InB1YmxpYyJ9"
    )
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Cookie": f"vtex_segment={VTEX_SEGMENT}",
    }
    url = f"{BASE}/api/catalog_system/pub/products/search"

    for fq in (f"alternateIds_Ean:{ean}", f"ean:{ean}"):
        r = session.get(url, headers=headers, params={"fq": fq, "sc": SC}, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if data:
            prod = data[0]
            item = pick_item_by_ean(prod.get("items") or [], ean)
            if not item:
                return ""
            sellers = item.get("sellers") or []
            if not sellers:
                return ""
            co = sellers[0].get("commertialOffer") or {}
            pwd = safe_float(co.get("PriceWithoutDiscount"))
            price = safe_float(co.get("Price"))
            lp = pwd if (pwd and pwd > 0) else price
            return format_ar_price_no_decimals(lp)
    return ""


def fetch_vea_listprice(session: requests.Session, ean: str) -> str:
    BASE = "https://www.vea.com.ar"
    SC = "34"
    VTEX_SEGMENT = (
        "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZWwiOiIzNCIsInByaWNlVGFibGVzIjpudWxsLCJyZWdpb25JZCI6IlUxY2phblZ0WW05aGNtZGxiblJwYm1GMk56QXdZMjl5Wkc5aVlUY3dNQT09IiwidXRtX2NhbXBhaWduIjpudWxsLCJ1dG1fc291cmNlIjpudWxsLCJ1dG1pX2NhbXBhaWduIjpudWxsLCJjdXJyZW5jeUNvZGUiOiJBUlMiLCJjdXJyZW5jeVN5bWJvbCI6IiQiLCJjb3VudHJ5Q29kZSI6IkFSRyIsImN1bHR1cmVJbmZvIjoiZXMtQVIiLCJhZG1pbl9jdWx0dXJlSW5mbyI6ImVzLUFSIiwiY2hhbm5lbFByaXZhY3kiOiJwdWJsaWMifQ"
    )
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Cookie": f"vtex_segment={VTEX_SEGMENT}",
    }
    url = f"{BASE}/api/catalog_system/pub/products/search"

    r = session.get(url, headers=headers, params={"fq": f"alternateIds_Ean:{ean}", "sc": SC}, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if not data:
        return ""
    prod = data[0]
    item = pick_item_by_ean(prod.get("items") or [], ean)
    if not item:
        return ""
    sellers = item.get("sellers") or []
    if not sellers:
        return ""
    co = sellers[0].get("commertialOffer") or {}
    pwd = safe_float(co.get("PriceWithoutDiscount"))
    price = safe_float(co.get("Price"))
    lp = pwd if (pwd and pwd > 0) else price
    return format_ar_price_no_decimals(lp)


def fetch_coope_listprice(session: requests.Session, cod_coope: str) -> str:
    url = "https://api.lacoopeencasa.coop/api/articulo/detalle"
    params = {"cod_interno": cod_coope, "simple": "false"}
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json,text/plain,*/*"}

    r = session.get(url, params=params, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    j = r.json() if "application/json" in (r.headers.get("content-type") or "").lower() else {}
    datos = (j or {}).get("datos") or {}
    lp = safe_float(datos.get("precio_anterior"))
    return format_ar_price_no_decimals(lp)


def fetch_libertad_listprice(session: requests.Session, ean: str) -> str:
    BASE = "https://www.hiperlibertad.com.ar"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Content-Type": "application/json",
    }

    url = f"{BASE}/api/catalog_system/pub/products/search"
    r = session.get(url, headers=headers, params={"fq": f"alternateIds_Ean:{ean}", "sc": "1"}, timeout=TIMEOUT)
    if r.status_code != 200:
        return ""
    data = r.json()
    if not data:
        return ""
    prod = data[0]
    item = pick_item_by_ean(prod.get("items") or [], ean)
    if not item:
        return ""
    sku_id = str(item.get("itemId") or "").strip()
    if not sku_id:
        return ""

    sim_url = f"{BASE}/api/checkout/pub/orderForms/simulation"
    payload = {"items": [{"id": sku_id, "quantity": 1, "seller": "1"}], "country": "ARG"}
    rs = session.post(sim_url, headers=headers, params={"sc": "1"}, json=payload, timeout=TIMEOUT)
    if rs.status_code != 200:
        return ""
    sim = rs.json()
    items = sim.get("items") or []
    if not items:
        return ""
    lp_cents = items[0].get("listPrice")
    try:
        lp = float(lp_cents) / 100.0 if lp_cents else None
    except Exception:
        lp = None
    return format_ar_price_no_decimals(lp)


# =========================
# Runner
# =========================
CHAIN_ORDER = ("Carrefour", "Día", "ChangoMas", "Coto", "Jumbo", "Vea", "Cooperativa", "Hiperlibertad")


def compute_dispersion_row(row: dict):
    vals = []
    for k in CHAIN_ORDER:
        n = parse_price_int(row.get(k))
        if n is not None and n > 0:
            vals.append(n)
    if len(vals) < 2:
        return {"min": None, "max": None, "delta": None}
    mn, mx = min(vals), max(vals)
    return {"min": mn, "max": mx, "delta": mx - mn}


# ✅ FIX: sin type-hint interno (evita AttributeError al cargar el script)
def style_white_base(sty):
    """Fondo blanco para todo (header + celdas)."""
    return (
        sty.set_properties(**{"background-color": WHITE_BG})
          .set_table_styles([
              {"selector": "th", "props": [("background-color", WHITE_BG)]},
              {"selector": "td", "props": [("background-color", WHITE_BG)]},
          ])
    )


def style_prices_table_white(df: pd.DataFrame, chain_cols: list[str]):
    """Fondo blanco + negrita mínimo por fila (solo cadenas)."""
    def _bold_min(row: pd.Series):
        nums = []
        for c in chain_cols:
            n = parse_price_int(row.get(c))
            if n is not None and n > 0:
                nums.append(n)
        mn = min(nums) if nums else None

        styles = ["background-color: #FFFFFF;"] * len(row)
        if mn is None:
            return styles

        for i, col in enumerate(row.index):
            if col in chain_cols:
                n = parse_price_int(row.get(col))
                if n is not None and n == mn:
                    styles[i] += " font-weight: 700;"
        return styles

    sty = df.style.apply(_bold_min, axis=1)
    return style_white_base(sty)


def style_white_only(df: pd.DataFrame):
    """Solo fondo blanco."""
    return style_white_base(df.style)


def build_pct_vs_carrefour_table(df_prices: pd.DataFrame, chain_cols: list[str]) -> pd.DataFrame:
    base_cols = ["Categoría", "Marca", "EAN", "Nombre"]
    out_rows = []

    def fmt_pct(x):
        if x is None:
            return ""
        try:
            return f"{x:+.1%}"
        except Exception:
            return ""

    for _, r in df_prices.iterrows():
        car = parse_price_int(r.get("Carrefour"))
        out = {k: r.get(k, "") for k in base_cols}

        for c in chain_cols:
            if c == "Carrefour":
                out[c] = ""
                continue
            p = parse_price_int(r.get(c))
            if car is None or car <= 0 or p is None:
                out[c] = ""
            else:
                out[c] = fmt_pct((p / car) - 1.0)

        out_rows.append(out)

    return pd.DataFrame(out_rows, columns=base_cols + chain_cols)


def build_resumen_por_categoria_psp(df_prices: pd.DataFrame, chain_cols: list[str]) -> pd.DataFrame:
    """
    Resumen por Categoría: índice vs PSP (precio sugerido).
    Salida: enteros tipo 108 (= 1.08 * 100). Vacío si no hay datos.
    """
    psp_map = {}
    for _, meta in productos.items():
        meta = meta or {}
        ean = str(meta.get("ean") or "").strip()
        psp = parse_price_int(meta.get("psp"))
        if ean:
            psp_map[ean] = psp

    df = df_prices.copy()
    df["_psp"] = df["EAN"].map(psp_map)

    for c in chain_cols:
        def _idx(row):
            p = parse_price_int(row.get(c))
            s = row.get("_psp")
            if p is None or s is None or s <= 0:
                return None
            return p / float(s)
        df[f"_idx_{c}"] = df.apply(_idx, axis=1)

    rows = []
    cats = sorted([x for x in df["Categoría"].dropna().unique().tolist() if str(x).strip() != ""])
    for cat in cats:
        dcat = df[df["Categoría"] == cat]
        out = {"Categoría": cat}
        for c in chain_cols:
            vals = dcat[f"_idx_{c}"].dropna()
            out[c] = "" if len(vals) == 0 else str(int(round(vals.mean() * 100)))
        rows.append(out)

    return pd.DataFrame(rows, columns=["Categoría"] + list(chain_cols))


def decorate_index_with_dot(df_cat: pd.DataFrame, chain_cols: list[str]) -> pd.DataFrame:
    """
    Agrega 🟢/🟡/🔴 a la izquierda del número según umbral:
      >=99 🟢 | >=95 y <99 🟡 | <95 🔴
    """
    df2 = df_cat.copy()

    def deco(val):
        s = str(val).strip()
        if not s:
            return ""
        try:
            n = int(float(s))
        except Exception:
            return s

        if n >= 99:
            dot = "🟢"
        elif n >= 95:
            dot = "🟡"
        else:
            dot = "🔴"
        return f"{dot} {n}"

    for c in chain_cols:
        df2[c] = df2[c].apply(deco)

    return df2


def run_market_scan():
    s = requests.Session()
    base_cols = ["Categoría", "Marca", "EAN", "Nombre"]

    chain_funcs = [
        ("Carrefour", lambda meta: fetch_carrefour_listprice(s, meta["ean"])),
        ("Día", lambda meta: fetch_dia_listprice(s, meta["cod_dia"])),
        ("ChangoMas", lambda meta: fetch_chango_listprice(s, meta["ean"])),
        ("Coto", lambda meta: fetch_coto_listprice(s, meta["ean"])),
        ("Jumbo", lambda meta: fetch_jumbo_listprice(s, meta["ean"])),
        ("Vea", lambda meta: fetch_vea_listprice(s, meta["ean"])),
        ("Cooperativa", lambda meta: fetch_coope_listprice(s, meta["cod_coope"])),
        ("Hiperlibertad", lambda meta: fetch_libertad_listprice(s, meta["ean"])),
    ]
    chain_cols = [name for name, _ in chain_funcs]

    total_steps = len(productos) * len(chain_funcs)
    prog = st.progress(0, text="Iniciando relevamiento…")
    done = 0

    rows = []
    t0 = time.time()

    for nombre, meta in productos.items():
        meta = meta or {}
        ean = str(meta.get("ean") or "").strip()
        cod_dia = str(meta.get("cod_dia") or "").strip()
        cod_coope = str(meta.get("cod_coope") or meta.get("cod_coop") or "").strip()

        row = {
            "Categoría": str(meta.get("categoría") or "").strip(),
            "Marca": str(meta.get("marca") or "").strip(),
            "EAN": ean,
            "Nombre": str(nombre or "").strip(),
            "ean": ean,
            "cod_dia": cod_dia,
            "cod_coope": cod_coope,
        }

        for chain_name, fn in chain_funcs:
            val = ""
            try:
                val = fn({"ean": ean, "cod_dia": cod_dia, "cod_coope": cod_coope})
                if val == "NO_ENCONTRADO":
                    val = ""
            except Exception:
                val = ""
            row[chain_name] = val

            done += 1
            prog.progress(min(done / max(1, total_steps), 1.0), text=f"Relevando… {done}/{total_steps}")

        rows.append(row)

    elapsed = time.time() - t0
    prog.progress(1.0, text=f"Relevamiento completado en {elapsed:.1f}s")

    df = pd.DataFrame(rows)
    df_out = df[base_cols + chain_cols].copy()

    # alerta de dispersión
    deltas = []
    for _, r in df_out.iterrows():
        d = compute_dispersion_row(r.to_dict())
        deltas.append(d["delta"] if d["delta"] is not None else 0)
    max_delta = max(deltas) if deltas else 0
    if max_delta and max_delta > DISPERSION_THRESHOLD_ARS:
        st.warning(f"⚠️ Dispersión alta detectada en al menos 1 ítem: Δ máx = {max_delta} ARS (umbral {DISPERSION_THRESHOLD_ARS})")

    return df_out, chain_cols


# =========================
# UI
# =========================
if st.button("🔍 Relevar Mercado"):
    with st.spinner("⏳ Ejecutando relevamiento…"):
        df_result, chain_cols = run_market_scan()

    st.success("✅ Relevamiento finalizado")

    # ✅ Resumen por categoría (Index vs PSP) con círculos + fondo blanco
    st.markdown("### Resumen por Categoría (Index vs PSP)")
    df_cat_raw = build_resumen_por_categoria_psp(df_result, chain_cols=chain_cols)
    df_cat = decorate_index_with_dot(df_cat_raw, chain_cols=chain_cols)
    st.dataframe(style_white_only(df_cat), use_container_width=True)

    # ✅ Precios (fondo blanco + mínimos en negrita)
    st.markdown("### Precios (ListPrice)")
    st.dataframe(style_prices_table_white(df_result, chain_cols=chain_cols), use_container_width=True)

    # ✅ % vs Carrefour (fondo blanco)
    st.markdown("### Diferencia % vs Carrefour")
    df_pct = build_pct_vs_carrefour_table(df_result, chain_cols=chain_cols)
    st.dataframe(style_white_only(df_pct), use_container_width=True)

    # ✅ CSVs
    fecha = datetime.now().strftime("%Y-%m-%d_%H%M")

    st.download_button(
        label="⬇ Descargar CSV (Resumen Categoría - Index vs PSP)",
        data=df_cat_raw.to_csv(index=False).encode("utf-8"),
        file_name=f"relevar_mercado_resumen_categoria_psp_{fecha}.csv",
        mime="text/csv",
    )
    st.download_button(
        label="⬇ Descargar CSV (Mercado - Precios)",
        data=df_result.to_csv(index=False).encode("utf-8"),
        file_name=f"relevar_mercado_precios_{fecha}.csv",
        mime="text/csv",
    )
    st.download_button(
        label="⬇ Descargar CSV (Mercado - % vs Carrefour)",
        data=df_pct.to_csv(index=False).encode("utf-8"),
        file_name=f"relevar_mercado_pct_vs_carrefour_{fecha}.csv",
        mime="text/csv",
    )
else:
    st.info("Presioná **Relevar Mercado** para consultar el ListPrice en todas las cadenas.")
