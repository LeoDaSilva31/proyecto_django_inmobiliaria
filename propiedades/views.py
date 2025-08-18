from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.db.models.expressions import RawSQL
from .models import Propiedad
from .utils import normalizar_texto
from django.db.models import Q

def _aplicar_filtros(request, qs):
    op = request.GET.get("operacion") or ""
    if op: qs = qs.filter(tipo_operacion=op)

    tipo = request.GET.get("tipo") or ""
    if tipo: qs = qs.filter(tipo=tipo)

    # Nota: por ahora min/max son numéricos "ciegos" sin moneda.
    # Futuro: separar por USD/ARS con campos distintos.
    try:
        mn = request.GET.get("min")
        if mn:
            qs = qs.filter(Q(precio_usd__gte=mn) | Q(precio_pesos__gte=mn))
    except (TypeError, ValueError):
        pass

    try:
        mx = request.GET.get("max")
        if mx:
            qs = qs.filter(Q(precio_usd__lte=mx) | Q(precio_pesos__lte=mx))
    except (TypeError, ValueError):
        pass

    hab = request.GET.get("habitaciones")
    if hab:
        try:
            qs = qs.filter(habitaciones__gte=int(hab))
        except ValueError:
            pass

    if request.GET.get("mascotas"):
        qs = qs.filter(acepta_mascotas=True)

    return qs



@cache_page(60*5)
def home(request):
    destacadas = Propiedad.objects.filter(destacada=True, estado='activa').order_by('-creado')[:10]
    return render(request, "propiedades/home.html", {"destacadas": destacadas})

@cache_page(60*5)
def listado_propiedades(request):
    qs = Propiedad.objects.filter(estado='activa').order_by('-creado')
    qs = _aplicar_filtros(request, qs)
    page_obj = Paginator(qs, 18).get_page(request.GET.get("page"))
    return render(request, "propiedades/listado.html", {"page_obj": page_obj})

@cache_page(60*5)
def buscar_propiedades(request):
    q_raw = (request.GET.get("q") or "").strip()
    q_norm = normalizar_texto(q_raw)
    qs = Propiedad.objects.filter(estado='activa')
    if q_norm:
        for t in q_norm.split():
            qs = qs.filter(search_index__icontains=t)
    qs = _aplicar_filtros(request, qs)
    page_obj = Paginator(qs.order_by('-creado'), 18).get_page(request.GET.get("page"))
    return render(request, "propiedades/busqueda.html", {"page_obj": page_obj, "q": q_raw})


@cache_page(60*5)
def propiedades_cercanas(request):
    try:
        lat = float(request.GET.get("lat")); lng = float(request.GET.get("lng"))
    except (TypeError, ValueError):
        lat = lng = None
    radius_km = float(request.GET.get("r") or 20.0)

    qs = Propiedad.objects.filter(estado='activa').exclude(latitud__isnull=True, longitud__isnull=True)
    if lat is not None and lng is not None:
        delta = radius_km / 111.0
        qs = qs.filter(latitud__gte=lat-delta, latitud__lte=lat+delta,
                       longitud__gte=lng-delta, longitud__lte=lng+delta)
        sql = """
        6371 * acos(
           cos(radians(%s)) * cos(radians(latitud)) *
           cos(radians(longitud) - radians(%s)) +
           sin(radians(%s)) * sin(radians(latitud))
        )
        """
        params = [lat, lng, lat]
        qs = qs.annotate(dist_km=RawSQL(sql, params)).filter(dist_km__lte=radius_km).order_by("dist_km")
    page_obj = Paginator(qs, 18).get_page(request.GET.get("page"))
    return render(request, "propiedades/cercanas.html", {"page_obj": page_obj, "r": radius_km, "lat": lat, "lng": lng})

@cache_page(60*15)
def detalle_propiedad(request, codigo):
    p = get_object_or_404(Propiedad, codigo=codigo, estado='activa')
    imagenes = p.imagenes.all()[:10]
    return render(request, "propiedades/detalle.html", {"p": p, "imagenes": imagenes})

