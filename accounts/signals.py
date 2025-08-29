# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.conf import settings
from django.apps import apps

UserModel = apps.get_model(*settings.AUTH_USER_MODEL.split("."))


AUTO_ADD_ENABLED = getattr(settings, "AUTO_ADD_STAFF_TO_CARGADORES", True)
DEFAULT_GROUP_NAME = "AdministradorCliente"  

@receiver(post_save, sender=UserModel)
def add_staff_to_group(sender, instance, created, **kwargs):
    if not AUTO_ADD_ENABLED:
        return
    if instance.is_staff:
        grupo, _ = Group.objects.get_or_create(name=DEFAULT_GROUP_NAME)
        instance.groups.add(grupo)
