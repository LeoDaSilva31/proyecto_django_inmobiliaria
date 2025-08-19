from django.contrib import admin
from django.urls import path, include
from propiedades.views import home, listado_propiedades, detalle_propiedad, buscar_propiedades, nosotros 

urlpatterns = [
    path("admin/", admin.site.urls),

    # login independiente (template lo haremos luego)
    path("cuentas/", include("accounts.urls")),

    # público
    path("", home, name="home"),
    path("propiedades/", listado_propiedades, name="propiedades_listado"),
    path("propiedades/<str:codigo>/", detalle_propiedad, name="propiedad_detalle"),
    path("buscar/", buscar_propiedades, name="buscar_propiedades"),
    path("nosotros/", nosotros, name="nosotros"),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)