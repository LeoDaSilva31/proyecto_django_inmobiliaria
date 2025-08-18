from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat

ALLOWED_EXTS = {"jpg","jpeg","png","webp"}
MAX_MB = 3

def validar_imagen(file):
    ext = (file.name.rsplit('.',1)[-1] or "").lower()
    if ext not in ALLOWED_EXTS:
        raise ValidationError("Formato no permitido. Usá JPG, PNG o WEBP.")
    if file.size > MAX_MB * 1024 * 1024:
        raise ValidationError(f"Imagen > {MAX_MB} MB (actual: {filesizeformat(file.size)}).")
