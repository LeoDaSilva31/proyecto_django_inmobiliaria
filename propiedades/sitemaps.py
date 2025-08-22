# propiedades/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.conf import settings
from .models import Propiedad

class PropiedadSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    protocol = "https" if not settings.DEBUG else "http"
    # Django pagina por defecto en 50 items; con 40 te entran todas en /sitemap.xml
    # (Si algún día tenés miles, Django sirve /sitemap.xml?p=2, etc.)
    limit = 1000

    def items(self):
        # Si tenés un flag tipo `publicada`, podrías usar:
        # return Propiedad.objects.filter(publicada=True).order_by("-id")[:5000]
        return Propiedad.objects.all().order_by("-id")[:5000]

    def lastmod(self, obj):
        for attr in ("updated_at", "modified", "fecha_publicacion", "created_at"):
            val = getattr(obj, attr, None)
            if val:
                return val
        return None

    def location(self, obj):
        if hasattr(obj, "get_absolute_url"):
            return obj.get_absolute_url()
        if hasattr(obj, "codigo"):
            return reverse("propiedad_detalle", args=[obj.codigo])
        return reverse("propiedad_detalle", args=[obj.pk])


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    protocol = "https" if not settings.DEBUG else "http"

    def items(self):
        return ["home", "nosotros", "propiedades_listado"]

    def location(self, name):
        return reverse(name)
