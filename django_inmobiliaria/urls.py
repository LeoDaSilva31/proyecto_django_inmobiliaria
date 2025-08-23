from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

from propiedades.views import (
    home, listado_propiedades, detalle_propiedad, buscar_propiedades, nosotros
)

from django.contrib.sitemaps.views import sitemap
from propiedades.sitemaps import PropiedadSitemap, StaticViewSitemap

sitemaps = {
    "static": StaticViewSitemap,
    "propiedades": PropiedadSitemap,
}

def robots_txt(_request):
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Sitemap: https://leods-blog.org/sitemap.xml\n"
    )
    return HttpResponse(content, content_type="text/plain")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("accounts.urls")),

    path("", home, name="home"),
    path("propiedades/", listado_propiedades, name="propiedades_listado"),
    path("propiedades/<str:codigo>/", detalle_propiedad, name="propiedad_detalle"),
    path("buscar/", buscar_propiedades, name="buscar_propiedades"),
    path("nosotros/", nosotros, name="nosotros"),

    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
