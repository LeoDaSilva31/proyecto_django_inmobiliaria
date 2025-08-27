from django.urls import path
from . import views as v

urlpatterns = [
    path("login/", v.login_view, name="login"),
    path("logout/", v.logout_view, name="logout"),

    path("panel/", v.panel_home, name="panel_home"),

    path("panel/propiedades/", v.panel_propiedades_list, name="panel_propiedades_list"),
    path("panel/propiedades/nueva/", v.panel_propiedad_crear, name="panel_propiedad_crear"),
    path("panel/propiedades/<int:pk>/editar/", v.panel_propiedad_editar, name="panel_propiedad_editar"),

    path("panel/propiedades/<int:pk>/pausar/", v.panel_propiedad_pausar, name="panel_propiedad_pausar"),
    path("panel/propiedades/<int:pk>/activar/", v.panel_propiedad_activar, name="panel_propiedad_activar"),
    path("panel/propiedades/<int:pk>/finalizar/", v.panel_propiedad_finalizar, name="panel_propiedad_finalizar"),
]
