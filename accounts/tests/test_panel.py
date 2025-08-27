# accounts/tests/test_panel.py
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import Group, Permission, ContentType
from django.contrib.auth import get_user_model

from propiedades.models import Propiedad

User = get_user_model()

def ensure_cargadores_group():
    """Crea el grupo 'Cargadores' con permisos de Propiedad si no existe."""
    grupo, _ = Group.objects.get_or_create(name="Cargadores")
    ct = ContentType.objects.get_for_model(Propiedad)
    perms = Permission.objects.filter(
        content_type=ct,
        codename__in=["view_propiedad", "add_propiedad", "change_propiedad"]
    )
    grupo.permissions.set(perms)
    grupo.save()
    return grupo

@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class PanelPermissionsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.list_url   = reverse("panel_propiedades_list")
        self.create_url = reverse("panel_propiedad_crear")

        # Usuarios
        self.staff_no_group = User.objects.create_user(
            username="staff_sin_grupo",
            dni="11111111",
            password="Clave123*",
            is_staff=True,
            is_active=True,
        )
        # Garantizar SIN permisos/grupos (por si hay signals)
        self.staff_no_group.groups.clear()
        self.staff_no_group.user_permissions.clear()

        self.no_staff = User.objects.create_user(
            username="no_staff",
            dni="22222222",
            password="Clave123*",
            is_staff=False,
            is_active=True,
        )

        self.staff_cargador = User.objects.create_user(
            username="cargador",
            dni="33333333",
            password="Clave123*",
            is_staff=True,
            is_active=True,
        )
        grupo = ensure_cargadores_group()
        self.staff_cargador.groups.add(grupo)

        # Propiedad dummy para edición (ajustá choices si difieren)
        self.prop = Propiedad.objects.create(
            codigo="TEST001",
            titulo="Prop de prueba",
            descripcion="desc",
            precio_usd=100000,
            tipo="departamento",
            tipo_operacion="venta",
            habitaciones=2,
            banos=1,
            cochera=False,
            acepta_mascotas=True,
            superficie_total=50,
            superficie_cubierta=45,
            estado="activa",
            direccion="Calle 123",
            localidad="Quilmes",
            provincia="Buenos Aires",
            pais="Argentina",
            destacada=False,
        )
        self.edit_url = reverse("panel_propiedad_editar", args=[self.prop.pk])

    def test_list_requires_login(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp["Location"])

    def test_list_requires_staff_and_view_perm(self):
        # logueado pero NO staff → redirige por guardia de staff
        self.client.force_login(self.no_staff)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 302)
        self.client.logout()

        # staff SIN permiso view_propiedad → 403 (no hay signals en force_login)
        self.client.force_login(self.staff_no_group)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 403)
        self.client.logout()

        # staff con grupo Cargadores → 200
        self.client.force_login(self.staff_cargador)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)

    def test_create_requires_add_perm(self):
        # staff SIN add → 403
        self.client.force_login(self.staff_no_group)
        resp = self.client.get(self.create_url)
        self.assertEqual(resp.status_code, 403)
        self.client.logout()

        # staff CON add → 200
        self.client.force_login(self.staff_cargador)
        resp = self.client.get(self.create_url)
        self.assertEqual(resp.status_code, 200)

    def test_edit_requires_change_perm(self):
        # staff SIN change → 403
        self.client.force_login(self.staff_no_group)
        resp = self.client.get(self.edit_url)
        self.assertEqual(resp.status_code, 403)
        self.client.logout()

        # staff CON change → 200
        self.client.force_login(self.staff_cargador)
        resp = self.client.get(self.edit_url)
        self.assertEqual(resp.status_code, 200)
