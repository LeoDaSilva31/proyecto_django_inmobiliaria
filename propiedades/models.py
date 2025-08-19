from django.db import models
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from .validators import validar_imagen
from .utils import normalizar_texto

from PIL import Image  # usado por _to_webp
import io
import random
import string


def _generar_codigo():
    letras = ''.join(random.choices(string.ascii_uppercase, k=4))
    numeros = ''.join(random.choices(string.digits, k=4))
    return f"{letras}{numeros}"


def _to_webp(file_field):
    """
    Convierte la imagen a WEBP (quality=85). Si algo falla, devuelve el original.
    """
    if not file_field or not hasattr(file_field, 'file'):
        return file_field
    try:
        img = Image.open(file_field).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=85, method=6)
        buf.seek(0)
        name = file_field.name.rsplit('.', 1)[0] + ".webp"

        from django.core.files.uploadedfile import InMemoryUploadedFile
        webp = InMemoryUploadedFile(
            buf, None, name, "image/webp", buf.getbuffer().nbytes, None
        )
        return webp
    except Exception:
        return file_field


class Propiedad(models.Model):
    TIPO_PROPIEDAD_CHOICES = [
        ('casa', 'Casa'),
        ('departamento', 'Departamento'),
        ('ph', 'PH'),
        ('local', 'Local'),
        ('terreno', 'Terreno'),
        ('otro', 'Otro'),
    ]
    TIPO_OPERACION_CHOICES = [
        ('venta', 'Venta'),
        ('alquiler', 'Alquiler'),
        ('temporario', 'Temporario'),
    ]
    ESTADO_PUBLICACION = [
        ('activa', 'Activa'),
        ('pausada', 'Pausada'),
        ('finalizada', 'Finalizada'),
    ]

    codigo = models.CharField(max_length=8, unique=True, editable=False)

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()

    precio_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    precio_pesos = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    tipo = models.CharField(max_length=20, choices=TIPO_PROPIEDAD_CHOICES)
    tipo_operacion = models.CharField(max_length=20, choices=TIPO_OPERACION_CHOICES)

    habitaciones = models.PositiveSmallIntegerField(default=0)
    banos = models.PositiveSmallIntegerField(default=0)
    cochera = models.BooleanField(default=False)
    acepta_mascotas = models.BooleanField(default=False)

    superficie_total = models.PositiveIntegerField(null=True, blank=True, help_text="m²")
    superficie_cubierta = models.PositiveIntegerField(null=True, blank=True, help_text="m²")

    estado = models.CharField(max_length=12, choices=ESTADO_PUBLICACION, default='activa')

    direccion = models.CharField(max_length=255, help_text="Ej.: Av. Siempre Viva 742")
    localidad = models.CharField(max_length=120, help_text="Ej.: Quilmes")
    provincia = models.CharField(max_length=100, help_text="Ej.: Buenos Aires")
    pais = models.CharField(max_length=80, default="Argentina")

    localidad_norm = models.CharField(max_length=140, editable=False)
    provincia_norm = models.CharField(max_length=120, editable=False)
    pais_norm = models.CharField(max_length=100, editable=False)

    destacada = models.BooleanField(default=False, help_text="Mostrar en el home (máx. 10).")

    imagen_principal = models.ImageField(upload_to='propiedades/portadas/', validators=[validar_imagen])

    search_index = models.TextField(editable=False, blank=True)

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creado']
        indexes = [
            models.Index(fields=["localidad_norm"]),
            models.Index(fields=["provincia_norm"]),
        ]

    # ----------------- Validaciones -----------------
    def clean(self):
        if not self.localidad or not self.provincia or not self.pais:
            raise ValidationError("Completá localidad, provincia y país.")

    # ----------------- Guardado -----------------
    def save(self, *args, **kwargs):
        # Generar código único si no está
        if not self.codigo:
            nuevo = _generar_codigo()
            while Propiedad.objects.filter(codigo=nuevo).exists():
                nuevo = _generar_codigo()
            self.codigo = nuevo

        # Convertir portada a webp si corresponde
        if self.imagen_principal and hasattr(self.imagen_principal, 'file'):
            self.imagen_principal = _to_webp(self.imagen_principal)

        # Presentación y normalizados
        self.localidad = (self.localidad or "").strip().title()
        self.provincia = (self.provincia or "").strip().title()
        self.pais = (self.pais or "").strip().title() or "Argentina"

        self.localidad_norm = normalizar_texto(self.localidad)
        self.provincia_norm = normalizar_texto(self.provincia)
        self.pais_norm = normalizar_texto(self.pais)

        partes = [
            self.titulo, self.descripcion, self.direccion,
            self.localidad, self.provincia, self.pais,
            self.tipo, self.tipo_operacion,
            ("cochera" if self.cochera else "no cochera"),
            ("acepta mascotas" if self.acepta_mascotas else "no mascotas"),
        ]
        self.search_index = normalizar_texto(" ".join([p for p in partes if p]))

        super().save(*args, **kwargs)

    # ----------------- Presentación -----------------
    @property
    def precio_display(self):
        if self.precio_usd is not None:
            return f"US$ {self.precio_usd:,.0f}"
        if self.precio_pesos is not None:
            return f"$ {self.precio_pesos:,.0f}"
        return "Consultar"

    def __str__(self):
        return f"{self.codigo} — {self.titulo}"


class PropiedadImagen(models.Model):
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='propiedades/galeria/', validators=[validar_imagen])

    def clean(self):
        if not self.propiedad_id:
            return
        if not self.pk and self.propiedad.imagenes.count() >= 10:
            raise ValidationError("Solo se permiten hasta 10 imágenes secundarias por propiedad.")

    def save(self, *args, **kwargs):
        if self.imagen and hasattr(self.imagen, 'file'):
            self.imagen = _to_webp(self.imagen)
        super().save(*args, **kwargs)

    def miniatura_admin(self):
        try:
            return format_html('<img src="{}" style="height:60px;border-radius:6px;"/>', self.imagen.url)
        except Exception:
            return "(sin imagen)"
    miniatura_admin.short_description = "Preview"

    def __str__(self):
        return f"Imagen de {self.propiedad.codigo}"
