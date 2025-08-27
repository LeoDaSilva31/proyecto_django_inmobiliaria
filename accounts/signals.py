from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.conf import settings
from django.apps import apps

User = settings.AUTH_USER_MODEL  # "accounts.User"
UserModel = apps.get_model(*User.split("."))

@receiver(post_save, sender=UserModel)
def add_staff_to_group(sender, instance, created, **kwargs):
    """
    Si está habilitado por settings y el usuario es staff+activo,
    al CREARSE lo agrega al grupo 'Cargadores'.
    (No re-agrega en cada save, evita sorpresas en tests y en admin.)
    """
    # Permite desactivar en tests u otros entornos
    if not getattr(settings, "AUTO_ADD_STAFF_TO_CARGADORES", True):
        return

    # Solo al crear, y solo si es staff activo
    if created and instance.is_staff and getattr(instance, "is_active", True):
        grupo, _ = Group.objects.get_or_create(name="Cargadores")
        instance.groups.add(grupo)
