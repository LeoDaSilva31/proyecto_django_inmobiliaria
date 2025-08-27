from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class LoginTests(TestCase):
    def setUp(self):
        self.client = Client()
        # staff válido
        self.staff = User.objects.create_user(
            username="operador1",
            dni="12345678",
            password="Dpsn2025*",
            is_staff=True,
            is_active=True,
        )
        # no staff
        self.no_staff = User.objects.create_user(
            username="invitado",
            dni="99999999",
            password="Clave123*",
            is_staff=False,
            is_active=True,
        )
        self.login_url = reverse("login")

    def test_login_staff_ok_redirects_to_list(self):
        resp = self.client.post(self.login_url, {
            "usuario_o_dni": "operador1",
            "password": "Dpsn2025*",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("panel_propiedades_list"))

    def test_login_bad_credentials_stays_on_login(self):
        resp = self.client.post(self.login_url, {
            "usuario_o_dni": "operador1",
            "password": "malaclave",
        })
        self.assertEqual(resp.status_code, 200)  # se queda en login
        self.assertContains(resp, "Credenciales inválidas", status_code=200)

    def test_login_non_staff_denied(self):
        resp = self.client.post(self.login_url, {
            "usuario_o_dni": "invitado",
            "password": "Clave123*",
        })
        self.assertEqual(resp.status_code, 200)  # se queda en login
        self.assertContains(resp, "No tenés permisos de acceso al panel", status_code=200)
