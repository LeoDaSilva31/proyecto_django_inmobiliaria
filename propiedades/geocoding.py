# propiedades/geocoding.py
import json
from django.core.cache import cache

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

try:
    import requests  # opcional
except ImportError:
    requests = None

def _http_get(url, params, headers, timeout):
    if requests is not None:
        r = requests.get(url, params=params, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.text
    # Fallback sin requests
    from urllib.parse import urlencode
    from urllib.request import urlopen, Request
    qs = urlencode(params)
    req = Request(f"{url}?{qs}", headers=headers or {})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")

def geocode_address(address: str, *, countrycodes="ar", timeout=8):
    if not address or not address.strip():
        return None
    key = f"geo:{address.strip().lower()}"
    hit = cache.get(key)
    if hit:
        return hit
    params = {
        "format": "json",
        "q": address,
        "limit": 1,
        "addressdetails": 0,
    }
    if countrycodes:
        params["countrycodes"] = countrycodes
    headers = {
        "User-Agent": "tu-inmobiliaria/1.0 (contacto@tu-dominio.com)",
        "Accept": "application/json",
    }
    try:
        text = _http_get(NOMINATIM_URL, params, headers, timeout)
        data = json.loads(text)
        if data:
            lat, lon = data[0]["lat"], data[0]["lon"]
            cache.set(key, (lat, lon), 60 * 60 * 24 * 30)  # 30 días
            return lat, lon
        return None
    except Exception:
        return None
