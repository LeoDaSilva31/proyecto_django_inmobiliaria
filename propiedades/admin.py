from django.contrib import admin
from .models import Propiedad, PropiedadImagen

class PropiedadImagenInline(admin.TabularInline):
    model = PropiedadImagen
    extra = 1
    fields = ("imagen","miniatura_admin")
    readonly_fields = ("miniatura_admin",)

@admin.register(Propiedad)
class PropiedadAdmin(admin.ModelAdmin):
    list_display = ("codigo","titulo","tipo","tipo_operacion","precio_display","estado","localidad","provincia","destacada")
    list_filter  = ("tipo","tipo_operacion","estado","destacada","provincia")
    search_fields= ("codigo","titulo","direccion","localidad","provincia")
    inlines = [PropiedadImagenInline]
