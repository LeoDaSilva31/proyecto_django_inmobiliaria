# accounts/forms.py

from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist

from .models import User  # AUTH_USER_MODEL
# Formularios del panel (propiedades)
from propiedades.models import Propiedad, PropiedadImagen
from django.forms import inlineformset_factory


class LoginDNIForm(forms.Form):
    dni = forms.CharField(
        max_length=32,
        widget=forms.TextInput(attrs={"placeholder": "DNI o usuario"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Contraseña"})
    )

    def clean(self):
        cleaned = super().clean()
        dni = (cleaned.get("dni") or "").strip()
        pwd = cleaned.get("password")

        if not dni or not pwd:
            # Dejamos que los widgets marquen required si querés,
            # pero levantamos un mensaje claro si faltan ambos.
            raise forms.ValidationError("Ingresá DNI/usuario y contraseña.")

        # 1) Buscamos por DNI; si no existe, probamos por username
        user = None
        try:
            user = User.objects.get(dni=dni)
        except ObjectDoesNotExist:
            try:
                user = User.objects.get(username=dni)
            except ObjectDoesNotExist:
                pass

        if not user:
            raise forms.ValidationError("DNI o contraseña inválidos.")

        # 2) Autenticamos con username real del usuario
        user_auth = authenticate(username=user.username, password=pwd)

        # 3) Validamos credenciales y estado activo
        if not user_auth or not user_auth.is_active:
            raise forms.ValidationError("DNI o contraseña inválidos.")

        cleaned["user"] = user_auth
        return cleaned


# =========================
# Formularios del PANEL
# =========================

class PropiedadForm(forms.ModelForm):
    class Meta:
        model = Propiedad
        fields = [
            "titulo", "descripcion",
            "precio_usd", "precio_pesos",
            "tipo", "tipo_operacion",
            "habitaciones", "banos", "cochera", "acepta_mascotas",
            "superficie_total", "superficie_cubierta",
            "estado", "direccion", "localidad", "provincia", "pais",
            "destacada", "imagen_principal",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned = super().clean()
        # Ejemplo opcional: al menos un precio o dejar "Consultar"
        # if not cleaned.get("precio_usd") and not cleaned.get("precio_pesos"):
        #     raise forms.ValidationError("Ingresá al menos un precio o dejá 'Consultar'.")
        return cleaned


PropiedadImagenFormSet = inlineformset_factory(
    Propiedad,
    PropiedadImagen,
    fields=["imagen"],
    extra=1,
    can_delete=True,  # permite quitar imágenes de la galería (no borra Propiedad)
)
