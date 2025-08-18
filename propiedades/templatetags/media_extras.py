from django import template
from django.core.files.storage import default_storage
register = template.Library()

@register.filter
def safe_image_url(image_field, placeholder='/static/img/placeholder.webp'):
    try:
        if image_field and hasattr(image_field, 'name') and default_storage.exists(image_field.name):
            return image_field.url
    except Exception:
        pass
    return placeholder
