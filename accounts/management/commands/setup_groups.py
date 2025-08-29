from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = "Crea/actualiza el grupo AdministradorCliente con permisos mínimos para gestionar propiedades."

    def handle(self, *args, **options):
        grupo, _ = Group.objects.get_or_create(name="AdministradorCliente")

        # Permisos requeridos
        perms_codename = [
            # Propiedad
            "view_propiedad", "add_propiedad", "change_propiedad",
            # PropiedadImagen
            "view_propiedadimagen", "add_propiedadimagen", "change_propiedadimagen",
        ]

        # Buscar permisos por codename
        perms = Permission.objects.filter(codename__in=perms_codename)
        faltantes = set(perms_codename) - set(perms.values_list("codename", flat=True))

        if faltantes:
            self.stdout.write(self.style.WARNING(
                f"⚠ No se encontraron algunos permisos (quizás faltan migraciones de 'propiedades'): {', '.join(faltantes)}"
            ))

        grupo.permissions.set(perms)  
        grupo.save()

        self.stdout.write(self.style.SUCCESS(
            f"✓ Grupo 'AdministradorCliente' actualizado con {perms.count()} permisos."
        ))
