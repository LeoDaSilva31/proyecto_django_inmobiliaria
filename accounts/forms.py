from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms import inlineformset_factory

from .models import User
from propiedades.models import Propiedad, PropiedadImagen


# =========================
# Login (usuario o DNI)
# =========================
class LoginDNIForm(forms.Form):
    usuario_o_dni = forms.CharField(
        max_length=32,
        widget=forms.TextInput(attrs={
            "placeholder": "Usuario o DNI",
            "class": "form-input",
            "autocomplete": "username",
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Contraseña",
            "class": "form-input",
            "autocomplete": "current-password",
        })
    )

    error_messages = {
        "invalid": "Usuario/DNI o contraseña inválidos.",
        "inactive": "Tu usuario está desactivado.",
        "not_staff": "No tenés permisos de acceso al panel.",
    }

    def clean(self):
        cleaned = super().clean()
        ident = (cleaned.get("usuario_o_dni") or "").strip()
        pwd = cleaned.get("password")
        if not ident or not pwd:
            raise forms.ValidationError(self.error_messages["invalid"])

        user = None
        try:
            user = User.objects.get(dni=ident)
        except ObjectDoesNotExist:
            try:
                user = User.objects.get(username=ident)
            except ObjectDoesNotExist:
                pass

        if not user:
            raise forms.ValidationError(self.error_messages["invalid"])

        user_auth = authenticate(username=user.username, password=pwd)
        if not user_auth:
            raise forms.ValidationError(self.error_messages["invalid"])
        if not user_auth.is_active:
            raise forms.ValidationError(self.error_messages["inactive"])
        if not user_auth.is_staff:
            raise forms.ValidationError(self.error_messages["not_staff"])

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
            "titulo": forms.TextInput(attrs={
                "placeholder": "Ej: Departamento 2 ambientes en Quilmes Centro",
            }),
            "descripcion": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "Descripción para el aviso (comodidades, cercanías, estado, etc.)",
            }),
            "precio_usd": forms.NumberInput(attrs={
                "min": "0", "step": "1", "placeholder": "USD (opcional)",
            }),
            "precio_pesos": forms.NumberInput(attrs={
                "min": "0", "step": "1000", "placeholder": "Pesos (opcional)",
            }),
            "tipo": forms.Select(attrs={}),
            "tipo_operacion": forms.Select(attrs={}),
            "habitaciones": forms.NumberInput(attrs={
                "min": "0", "step": "1", "placeholder": "Dormitorios",
            }),
            "banos": forms.NumberInput(attrs={
                "min": "0", "step": "1", "placeholder": "Baños",
            }),
            "cochera": forms.CheckboxInput(attrs={}),
            "acepta_mascotas": forms.CheckboxInput(attrs={}),
            "superficie_total": forms.NumberInput(attrs={
                "min": "0", "step": "1", "placeholder": "m² totales",
            }),
            "superficie_cubierta": forms.NumberInput(attrs={
                "min": "0", "step": "1", "placeholder": "m² cubiertos",
            }),
            "estado": forms.Select(attrs={}),
            "direccion": forms.TextInput(attrs={
                "placeholder": "Calle y número (ej: Brown 3950)",
            }),
            "localidad": forms.TextInput(attrs={
                "placeholder": "Ej: Quilmes",
            }),
            "provincia": forms.TextInput(attrs={
                "placeholder": "Ej: Buenos Aires",
            }),
            "pais": forms.TextInput(attrs={
                "placeholder": "Ej: Argentina",
            }),
            "destacada": forms.CheckboxInput(attrs={}),
            "imagen_principal": forms.FileInput(attrs={
                "accept": "image/*",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar class="form-input" a textos/números/selects/file para estilo consistente
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.TextInput, forms.NumberInput, forms.Select, forms.FileInput, forms.Textarea)):
                css = widget.attrs.get("class", "")
                widget.attrs["class"] = (css + " form-input").strip()

    def clean(self):
        data = super().clean()

        # 1) Al menos un precio (o cambiá esta regla si permitís "Consultar")
        if not data.get("precio_usd") and not data.get("precio_pesos"):
            raise ValidationError("Ingresá al menos un precio en USD o en Pesos.")

        # 2) Precios no negativos
        for campo in ("precio_usd", "precio_pesos"):
            v = data.get(campo)
            if v is not None and v < 0:
                raise ValidationError("Los precios no pueden ser negativos.")

        # 3) Superficie coherente
        st = data.get("superficie_total")
        sc = data.get("superficie_cubierta")
        if st is not None and sc is not None and sc > st:
            raise ValidationError("La superficie cubierta no puede ser mayor a la total.")

        return data


# Formset de galería: 1 input inicial y el resto se agrega dinámicamente por JS
PropiedadImagenFormSet = inlineformset_factory(
    Propiedad,
    PropiedadImagen,
    fields=["imagen"],
    widgets={"imagen": forms.FileInput(attrs={"accept": "image/*", "class": "form-input"})},
    extra=1,
    can_delete=True,
    max_num=20,         # tope razonable
    validate_max=True,
)
