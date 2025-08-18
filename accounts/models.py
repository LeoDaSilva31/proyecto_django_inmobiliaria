from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.files.uploadedfile import InMemoryUploadedFile
from propiedades.validators import validar_imagen
from PIL import Image
import io

def _to_webp(file_field):
    if not file_field or not hasattr(file_field, 'file'):
        return file_field
    try:
        img = Image.open(file_field).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=85, method=6)
        buf.seek(0)
        name = file_field.name.rsplit('.', 1)[0] + ".webp"
        return InMemoryUploadedFile(buf, None, name, "image/webp", buf.getbuffer().nbytes, None)
    except Exception:
        return file_field

class User(AbstractUser):
    dni = models.CharField(max_length=15, unique=True)
    foto_perfil = models.ImageField(upload_to='usuarios/', blank=True, null=True, validators=[validar_imagen])

    def save(self, *args, **kwargs):
        if self.foto_perfil and hasattr(self.foto_perfil, 'file'):
            self.foto_perfil = _to_webp(self.foto_perfil)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.dni})"
