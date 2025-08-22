# propiedades/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.conf import settings
from .models import Propiedad

class PropiedadSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    protocol = "https" if not settings.DEBUG else "http"

    def items(self):
        # Ajustá el filtro si tenés un flag de publicación
        return Propiedad.objects.all().order_by("-id")[:5000]

    def lastmod(self, obj):
        for attr in ("updated_at", "modified", "fecha_publicacion", "created_at"):
            if hasattr(obj, attr) and getattr(obj, attr):
                return getattr(obj, attr)
        return None

    def location(self, obj):
        # Si tu modelo implementa get_absolute_url, esto lo usa automáticamente.
        if hasattr(obj, "get_absolute_url"):
            return obj.get_absolute_url()
        # Si tu URL de detalle usa el código:
        if hasattr(obj, "codigo"):
            return reverse("propiedad_detalle", args=[obj.codigo])
        # Fallback por pk (ajustá si tu pattern no usa pk)
        return reverse("propiedad_detalle", args=[obj.pk])


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    protocol = "https" if not settings.DEBUG else "http"

    def items(self):
        # Nombres de las rutas estáticas
        return ["home", "nosotros", "propiedades_listado"]

    def location(self, name):
        return reverse(name)
