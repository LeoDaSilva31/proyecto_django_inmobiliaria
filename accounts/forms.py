from django import forms
from django.contrib.auth import authenticate
from .models import User

class LoginDNIForm(forms.Form):
    dni = forms.CharField(max_length=15, widget=forms.TextInput(attrs={"placeholder":"DNI"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder":"Contraseña"}))

    def clean(self):
        cleaned = super().clean()
        dni = cleaned.get("dni"); pwd = cleaned.get("password")
        if dni and pwd:
            try:
                user = User.objects.get(dni=dni)
            except User.DoesNotExist:
                raise forms.ValidationError("DNI o contraseña inválidos.")
            user_auth = authenticate(username=user.username, password=pwd)
            if not user_auth:
                raise forms.ValidationError("DNI o contraseña inválidos.")
            cleaned["user"] = user_auth
        return cleaned


from django.contrib.auth import authenticate
from .models import User
from django.core.exceptions import ObjectDoesNotExist

def clean(self):
    cleaned = super().clean()
    dni = (cleaned.get("dni") or "").strip()
    pwd = cleaned.get("password")
    if dni and pwd:
        user = None
        try:
            user = User.objects.get(dni=dni)
        except ObjectDoesNotExist:
            # fallback: quizás ingresó el username en el campo DNI
            try:
                user = User.objects.get(username=dni)
            except ObjectDoesNotExist:
                pass
        if not user:
            raise forms.ValidationError("DNI o contraseña inválidos.")

        user_auth = authenticate(username=user.username, password=pwd)
        if not user_auth or not user_auth.is_active:
            raise forms.ValidationError("DNI o contraseña inválidos.")
        cleaned["user"] = user_auth
    return cleaned
