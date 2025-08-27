from django.contrib import admin

# Register your models here.
# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # mostrar columnas útiles en el listado
    list_display = ("username", "dni", "email", "is_staff", "is_active")
    search_fields = ("username", "dni", "email", "first_name", "last_name")

    # agrega el campo DNI en el formulario de edición
    fieldsets = BaseUserAdmin.fieldsets + (
        (_("Datos extra"), {"fields": ("dni",)}),
    )

    # agrega DNI en el formulario de alta
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {"fields": ("dni",)}),
    )
