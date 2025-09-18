# changomas_ean_to_refid.py
import requests
import csv
from datetime import datetime

# Carga tus productos ({"Nombre": {"ean": "...", ...}, ...})
from ean_mercado import productos_mercado

BASE = "https://www.masonline.com.ar"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) PythonRequests/2.x",
    "Accept": "application/json, text/plain, */*",
    # Si tenés un vtex_segment y lo necesitás:
    # "Cookie": "vtex_segment=...."
}
TIMEOUT = (3, 8)  # (connect, read)

def _extract_refid_from_item(item: dict) -> str | None:
    """Devuelve el Value de referenceId con Key=='RefId' si existe."""
    for ref in (item.get("referenceId") or []):
        if str(ref.get("Key", "")).lower() == "refid":
            val = str(ref.get("Value") or "").strip()
            if val:
                return val
    return None

def fetch_cod_maso_by_ean(ean: str) -> str | None:
    """
    Busca en VTEX por EAN y devuelve el RefId del ítem que matchee.
    Ese RefId es el 'código interno' que necesitás (p.ej. 15158190).
    """
    if not ean:
        return None
    url = f"{BASE}/api/catalog_system/pub/products/search"
    params = {"fq": f"alternateIds_Ean:{ean}"}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list) or not data:
            return None

        prod = data[0]
        items = prod.get("items") or []

        # 1) Intento con match exacto de EAN (item.ean o referenceId.Value == EAN)
        for it in items:
            if str(it.get("ean") or "").strip() == str(ean):
                refid = _extract_refid_from_item(it)
                if refid:
                    return refid
            for ref in (it.get("referenceId") or []):
                if str(ref.get("Value") or "").strip() == str(ean):
                    refid = _extract_refid_from_item(it)
                    if refid:
                        return refid

        # 2) Sin match exacto: devuelvo el primer RefId disponible
        for it in items:
            refid = _extract_refid_from_item(it)
            if refid:
                return refid

        return None
    except Exception:
        return None

def main():
    rows = []
    for nombre, meta in productos_mercado.items():
        ean = str((meta or {}).get("ean", "")).strip()
        refid = fetch_cod_maso_by_ean(ean) if ean else None
        print(f"{nombre} | EAN {ean} -> cod_maso (RefId): {refid or 'N/A'}")
        rows.append({"nombre": nombre, "ean": ean, "cod_maso": refid or ""})

    # Guardar CSV
    fname = f"cod_maso_desde_ean_{datetime.now().strftime('%Y-%m-%d')}.csv"
    with open(fname, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["nombre", "ean", "cod_maso"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nCSV guardado: {fname}")

if __name__ == "__main__":
    main()
