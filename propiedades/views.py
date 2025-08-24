from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from .models import Propiedad
from .utils import normalizar_texto
from django.db.models import Q

def _aplicar_filtros(request, qs, skip: set | None = None):
    skip = skip or set()

    if "operacion" not in skip:
        op = request.GET.get("operacion") or ""
        if op:
            qs = qs.filter(tipo_operacion=op)

    if "tipo" not in skip:
        tipo = request.GET.get("tipo") or ""
        if tipo:
            qs = qs.filter(tipo=tipo)

    # (Quitamos "min": ya no se usa en UI; si igual te llegan params viejos, podés dejar esto comentado)
    # if "min" not in skip:
    #     try:
    #         mn = request.GET.get("min")
    #         if mn:
    #             qs = qs.filter(Q(precio_usd__gte=mn) | Q(precio_pesos__gte=mn))
    #     except (TypeError, ValueError):
    #         pass

    if "max" not in skip:
        try:
            mx = request.GET.get("max")
            if mx:
                qs = qs.filter(Q(precio_usd__lte=mx) | Q(precio_pesos__lte=mx))
        except (TypeError, ValueError):
            pass

    if "habitaciones" not in skip:
        hab = request.GET.get("habitaciones")
        if hab:
            try:
                qs = qs.filter(habitaciones__gte=int(hab))
            except ValueError:
                pass

    if "mascotas" not in skip and request.GET.get("mascotas"):
        qs = qs.filter(acepta_mascotas=True)

    if "localidad" not in skip:
        loc = (request.GET.get("localidad") or "").strip()
        if loc:
            qs = qs.filter(localidad=loc)

    return qs


#@cache_page(60*5)
def home(request):
    destacadas = Propiedad.objects.filter(destacada=True, estado='activa').order_by('-creado')[:10]
    return render(request, "propiedades/home.html", {"destacadas": destacadas})

#@cache_page(60*5)
def listado_propiedades(request):
    qs = Propiedad.objects.filter(estado='activa').order_by('-creado')
    qs = _aplicar_filtros(request, qs)
    page_obj = Paginator(qs, 18).get_page(request.GET.get("page"))
    return render(request, "propiedades/listado.html", {"page_obj": page_obj})

# views.py (fragmento)
from urllib.parse import urlencode
from django.db.models import Q
from .models import Propiedad
from .utils import normalizar_texto

# --- Mapa simple de sinónimos/abreviaturas (todo en minúsculas, sin tildes) ---
SYNONYMS = {
    # tipos
    "departamento": ["departamento", "depto", "dto","dpto", "apartamento", "apto"],
    "casa": ["casa", "chalet", "chalec"],  # chalec = por si recorta
    "ph": ["ph", "propiedad horizontal"],
    "local": ["local", "local comercial", "comercial"],
    "terreno": ["terreno", "lote", "lotes", "parcel"],

    # operaciones
    "venta": ["venta", "vender", "vende"],
    "alquiler": ["alquiler", "renta", "arriendo", "arrendar", "alquilar", "alquilo"],
    "temporario": ["temporario", "temporal", "temporada"],

    # features
    "mascotas": ["mascotas", "pet friendly", "petfriendly", "acepta mascotas", "permite mascotas"],
    "cochera": ["cochera", "garage", "garaje", "estacionamiento"],

    # otros términos frecuentes
    "ambientes": ["ambiente", "ambientes", "amb", "dormitorio", "dormitorios", "hab", "habitacion", "habitaciones"],
    "banio": ["baño", "bano", "toilette", "aseo"],
    "m2": ["m2", "m²", "metros", "metros cuadrados", "mts", "mt2", "mt^2"],
}

def _expand_query_groups(q_raw: str):
    """
    - Normaliza el texto
    - Reemplaza sinónimos de *frase* (multi-palabra) por su forma canónica (p.ej., 'propiedad horizontal' -> 'ph')
    - Devuelve una lista de *grupos* (set) de variantes por token.
      Ej.: "propiedad horizontal venta" -> [{ 'ph', 'propiedad horizontal' }, { 'venta','vender','vende' }]
    """
    q_norm = normalizar_texto(q_raw or "")

    # 1) Reemplazo de frases por su canónico (antes de partir en tokens)
    for canon, variants in SYNONYMS_NORM.items():
        for v in variants:
            if " " in v and v in q_norm:
                q_norm = q_norm.replace(v, canon)

    # 2) Tokenizo y expando cada token a su set de variantes
    tokens = [t for t in q_norm.split() if t]
    groups = [ _expand_token(t) for t in tokens ]  # usa tu _expand_token existente
    return groups


# normalizamos el diccionario (sin tildes, lower)
def _norm(s: str) -> str:
    return normalizar_texto(s or "")

SYNONYMS_NORM = { _norm(k): list({_norm(v) for v in vals}) for k, vals in SYNONYMS.items() }

# invertimos para encontrar expansiones rápido a partir del término de búsqueda
VARIANT_TO_GROUPS = {}
for canon, variants in SYNONYMS_NORM.items():
    for v in variants + [canon]:
        VARIANT_TO_GROUPS.setdefault(v, set()).add(canon)

def _expand_token(token: str):
    """
    Devuelve un set de términos equivalentes (sinónimos) incluyendo el propio token.
    Trabaja sobre texto normalizado (sin tildes, lower).
    """
    t = _norm(token)
    expanded = set([t])
    # si el token pertenece a uno o más grupos, agregamos todos los sinónimos de esos grupos
    for group in VARIANT_TO_GROUPS.get(t, []):
        expanded.update(SYNONYMS_NORM.get(group, []))
        expanded.add(group)
    return expanded


def buscar_propiedades(request):
    q_raw = (request.GET.get("q") or "").strip()
    qs_base = Propiedad.objects.filter(estado='activa')

    qs = qs_base
    if q_raw:
        groups = _expand_query_groups(q_raw)  # lista de sets
        from django.db.models import Q
        for variants in groups:
            or_q = Q()
            for term in variants:
                or_q |= Q(search_index__icontains=term)
            qs = qs.filter(or_q)

    # --- Localidades disponibles (aplico todos los filtros menos 'localidad') ---
    qs_for_loc = _aplicar_filtros(request, qs, skip={"localidad"})
    localidades_disponibles = (qs_for_loc.values_list("localidad", flat=True)
                               .distinct().order_by("localidad"))

    # --- Ahora sí, aplico todos los filtros (incluida 'localidad') ---
    qs = _aplicar_filtros(request, qs)

    page_obj = Paginator(qs.order_by('-creado'), 18).get_page(request.GET.get("page"))

    # --- chips “lindos” para filtros aplicados ---
    tipo_map = dict(Propiedad.TIPO_PROPIEDAD_CHOICES)
    op_map = dict(Propiedad.TIPO_OPERACION_CHOICES)

    params = request.GET.copy()
    applied_filters = []
    if q_raw:
        applied_filters.append({"key": "q", "label": "Búsqueda", "value": q_raw})
    if params.get("operacion"):
        applied_filters.append({"key": "operacion", "label": "Operación",
                                "value": op_map.get(params["operacion"], params["operacion"])})
    if params.get("tipo"):
        applied_filters.append({"key": "tipo", "label": "Tipo",
                                "value": tipo_map.get(params["tipo"], params["tipo"])})
    if params.get("habitaciones"):
        applied_filters.append({"key": "habitaciones", "label": "Habitaciones",
                                "value": f"≥ {params['habitaciones']}"})
    if params.get("max"):
        applied_filters.append({"key": "max", "label": "Precio máx.", "value": params["max"]})
    if params.get("mascotas"):
        applied_filters.append({"key": "mascotas", "label": "Acepta mascotas", "value": ""})
    if params.get("localidad"):
        applied_filters.append({"key": "localidad", "label": "Localidad", "value": params["localidad"]})

    context = {
        "page_obj": page_obj,
        "q": q_raw,
        "params": params,
        "applied_filters": applied_filters,
        "tipos": Propiedad.TIPO_PROPIEDAD_CHOICES,
        "operaciones": Propiedad.TIPO_OPERACION_CHOICES,
        "localidades": localidades_disponibles,  # <-- NUEVO
    }
    return render(request, "propiedades/busqueda.html", context)

#@cache_page(60*15)
def detalle_propiedad(request, codigo):
    p = get_object_or_404(Propiedad, codigo=codigo, estado='activa')
    imagenes = p.imagenes.all()[:10]
    return render(request, "propiedades/detalle.html", {"p": p, "imagenes": imagenes})


# propiedades/views.py
from django.conf import settings
from django.shortcuts import render

def nosotros(request):
    ctx = {
        "company_name": getattr(settings, "COMPANY_NAME", "Inmobiliaria"),
        "phone_display": getattr(settings, "COMPANY_PHONE_DISPLAY", "+54 11 6804-4215"),
        "phone_wa": getattr(settings, "COMPANY_PHONE_WA", "541168044215"),  # sin "+" ni espacios
        "email": getattr(settings, "COMPANY_EMAIL", "contacto@inmobiliaria.com"),
        "address": getattr(settings, "COMPANY_ADDRESS", "Brown 3950, Quilmes, Buenos Aires, Argentina"),
        "social": {
            "instagram": getattr(settings, "COMPANY_INSTAGRAM", "#"),
            "facebook": getattr(settings, "COMPANY_FACEBOOK", "#"),
            "x": getattr(settings, "COMPANY_X", "#"),
        },
    }
    return render(request, "propiedades/nosotros.html", ctx)
