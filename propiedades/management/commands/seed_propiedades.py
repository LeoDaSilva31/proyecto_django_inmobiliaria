# propiedades/management/commands/seed_propiedades.py
import os
import random
import string
from datetime import datetime
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.apps import apps

# ---------- Helpers de introspección ----------
def has_field(model, name: str) -> bool:
    try:
        model._meta.get_field(name)
        return True
    except Exception:
        return False

def set_if_has(model, data: dict, name: str, value):
    if has_field(model, name):
        data[name] = value

def pick_existing_file(base_dir: Path, idx: int):
    """
    Busca 'foto (idx).<ext>' con ext en [jpg, jpeg, png, webp] dentro de base_dir.
    Devuelve Path o None si no existe.
    """
    exts = ("jpg", "jpeg", "png", "webp")
    for ext in exts:
        p = base_dir / f"foto ({idx}).{ext}"
        if p.exists():
            return p
    return None

def generate_code(existing_codes: set) -> str:
    # Formato tipo UVBP6491: 4 letras + 4 dígitos
    while True:
        code = "".join(random.choice(string.ascii_uppercase) for _ in range(4)) + str(random.randint(1000, 9999))
        if code not in existing_codes:
            existing_codes.add(code)
            return code

class Command(BaseCommand):
    help = "Crea propiedades de prueba con imágenes locales."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=50, help="Cantidad de propiedades a crear")
        parser.add_argument("--img-dir", type=str, required=True, help=r'Carpeta con "foto (1..20).jpg|png|jpeg|webp"')
        parser.add_argument("--images-per", type=int, default=3, help="Cantidad de fotos por propiedad (si hay modelo de imágenes)")
        parser.add_argument("--dry-run", action="store_true", help="No guarda nada; solo muestra qué haría")

    def handle(self, *args, **opts):
        count = int(opts["count"])
        img_dir = Path(opts["img_dir"])
        images_per = int(opts["images_per"])
        dry = bool(opts["dry_run"])

        if not img_dir.exists():
            raise CommandError(f"La carpeta de imágenes no existe: {img_dir}")

        # Modelos (ajusta si tenés otros nombres)
        Propiedad = apps.get_model("propiedades", "Propiedad")
        ImagenModel = None
        for candidate in ("PropiedadImagen", "Imagen", "Foto", "PropiedadFoto"):
            try:
                ImagenModel = apps.get_model("propiedades", candidate)
                break
            except Exception:
                continue

        self.stdout.write(self.style.NOTICE(f"Usando modelo Propiedad: {Propiedad}"))
        self.stdout.write(self.style.NOTICE(f"Modelo de imágenes: {ImagenModel or 'no encontrado (se intentará ImageField dentro de Propiedad)'}"))

        # Catálogos simples (sin dependencias externas)
        ciudades = [
            ("Quilmes", "Buenos Aires", "Centro"), ("Bernal", "Buenos Aires", "Oeste"),
            ("Wilde", "Buenos Aires", "Centro"), ("Avellaneda", "Buenos Aires", "Gerli"),
            ("Lanús", "Buenos Aires", "Lanús Este"), ("Banfield", "Buenos Aires", "Este"),
            ("Lomas de Zamora", "Buenos Aires", "Lomas Centro"),
            ("Palermo", "CABA", "Palermo Soho"),
            ("Caballito", "CABA", "Caballito Norte"),
            ("Recoleta", "CABA", "Recoleta"),
        ]
        calles = [
            "Av. Mitre", "Rivadavia", "Sarmiento", "Belgrano", "San Martín", "Corrientes",
            "Lavalle", "Urquiza", "Suipacha", "Alsina", "Moreno", "Laprida", "Armenia",
            "Guatemala", "Gorriti", "Honduras", "Scalabrini Ortiz", "Callao", "Pueyrredón",
        ]
        tipos = ["Departamento", "Casa", "PH", "Lote", "Local", "Galpón"]
        operaciones = ["Venta", "Alquiler"]

        # Colectar campos presentes en Propiedad para setear solo lo existente
        prop_fields = {f.name for f in Propiedad._meta.get_fields() if hasattr(f, "name")}
        self.stdout.write(self.style.SUCCESS(f"Campos detectados en Propiedad: {sorted(prop_fields)}"))

        # Recolectar códigos ya existentes (si hubiera un campo 'codigo' o 'code' o 'slug')
        existing_codes = set()
        code_field = None
        for candidate in ("codigo", "code", "slug"):
            if has_field(Propiedad, candidate):
                code_field = candidate
                existing_codes.update(
                    Propiedad.objects.exclude(**{candidate: None}).values_list(candidate, flat=True)
                )
                self.stdout.write(self.style.NOTICE(f"Se utilizará el campo '{candidate}' para el código único"))
                break

        # Detectar posibles ImageField dentro de Propiedad
        single_image_field = None
        for candidate in ("imagen", "imagen_principal", "foto", "foto_principal", "cover", "portada"):
            if has_field(Propiedad, candidate):
                single_image_field = candidate
                self.stdout.write(self.style.NOTICE(f"Se usará ImageField interno: {candidate}"))
                break

        creadas = 0
        for i in range(count):
            tipo = random.choice(tipos)
            operacion = random.choice(operaciones)

            ciudad, provincia, barrio = random.choice(ciudades)
            calle = random.choice(calles)
            altura = random.randint(100, 4900)
            direccion = f"{calle} {altura}"

            ambientes = random.randint(1, 5)
            dormitorios = max(0, ambientes - random.choice([0, 1, 2]))
            banos = random.randint(1, max(1, ambientes))
            cochera = random.choice([True, False])

            m2_cub = random.randint(28, 180)
            m2_total = m2_cub + random.choice([0, 10, 20, 30, 50])

            # Precio según operación
            if operacion == "Venta":
                moneda = "USD"
                precio = random.randint(35000, 350000)
            else:
                moneda = "ARS"
                precio = random.randint(220000, 2200000)

            titulo = f"{tipo} {ambientes} amb. en {ciudad}"
            desc = (
                f"Propiedad de {ambientes} ambientes en {barrio}, {ciudad}. "
                f"{dormitorios} dormitorios, {banos} baño(s), "
                f"{'con cochera' if cochera else 'sin cochera'}. "
                f"Sup. cubierta {m2_cub} m², sup. total {m2_total} m². "
                f"Operación: {operacion} ({moneda})."
            )

            data = {}
            set_if_has(Propiedad, data, "titulo", titulo)
            set_if_has(Propiedad, data, "nombre", titulo)  # por si usan 'nombre' en lugar de 'titulo'
            set_if_has(Propiedad, data, "descripcion", desc)
            set_if_has(Propiedad, data, "direccion", direccion)
            set_if_has(Propiedad, data, "ciudad", ciudad)
            set_if_has(Propiedad, data, "provincia", provincia)
            set_if_has(Propiedad, data, "barrio", barrio)
            set_if_has(Propiedad, data, "tipo", tipo)
            set_if_has(Propiedad, data, "tipo_propiedad", tipo)
            set_if_has(Propiedad, data, "operacion", operacion)
            set_if_has(Propiedad, data, "ambientes", ambientes)
            set_if_has(Propiedad, data, "dormitorios", dormitorios)
            set_if_has(Propiedad, data, "banos", banos)
            set_if_has(Propiedad, data, "cochera", cochera)
            set_if_has(Propiedad, data, "cocheras", 1 if cochera else 0)
            set_if_has(Propiedad, data, "superficie_cubierta", m2_cub)
            set_if_has(Propiedad, data, "superficie_total", m2_total)
            set_if_has(Propiedad, data, "precio", precio)
            set_if_has(Propiedad, data, "moneda", moneda)
            set_if_has(Propiedad, data, "fecha_publicacion", timezone.now())

            if code_field:
                data[code_field] = generate_code(existing_codes)

            # Crear Propiedad
            if dry:
                self.stdout.write(self.style.WARNING(f"[DRY-RUN] Crearía Propiedad: {data}"))
                prop = None
            else:
                prop = Propiedad.objects.create(**data)
                self.stdout.write(self.style.SUCCESS(f"Propiedad creada id={prop.pk}"))

            # Asignar imágenes
            # - Si hay modelo de imágenes relacionado (ImagenModel), crear 'images_per' registros.
            # - Si no, y hay un ImageField en Propiedad (single_image_field), asignar una.
            if not dry:
                # Elegimos índices de 1..20, sin repetir
                img_indices = random.sample(range(1, 21), k=min(images_per, 20))

                if ImagenModel and prop:
                    # Detectar nombre del FK a Propiedad (comúnmente 'propiedad' o 'inmueble')
                    fk_name = None
                    for candidate in ("propiedad", "inmueble", "propiedad_fk", "prop", "owner"):
                        if has_field(ImagenModel, candidate):
                            fk_name = candidate
                            break
                    if not fk_name:
                        # Buscar el primer FK que apunte a Propiedad
                        for f in ImagenModel._meta.get_fields():
                            try:
                                if getattr(f, "related_model", None) == Propiedad:
                                    fk_name = f.name
                                    break
                            except Exception:
                                pass

                    # Detectar el campo de imagen
                    img_field_name = None
                    for candidate in ("imagen", "foto", "archivo", "image", "picture"):
                        if has_field(ImagenModel, candidate):
                            img_field_name = candidate
                            break

                    for idx in img_indices:
                        pth = pick_existing_file(img_dir, idx)
                        if pth and fk_name and img_field_name:
                            obj = ImagenModel()
                            setattr(obj, fk_name, prop)
                            with open(pth, "rb") as fh:
                                getattr(obj, img_field_name).save(pth.name, File(fh), save=False)
                            obj.save()
                    self.stdout.write(self.style.NOTICE(f"  → {len(img_indices)} imagen(es) relacionadas"))

                elif single_image_field and prop:
                    # Asignar una sola imagen a la Propiedad
                    idx = img_indices[0]
                    pth = pick_existing_file(img_dir, idx)
                    if pth:
                        with open(pth, "rb") as fh:
                            getattr(prop, single_image_field).save(pth.name, File(fh), save=True)
                        self.stdout.write(self.style.NOTICE("  → Imagen principal asignada"))
                    else:
                        self.stdout.write(self.style.WARNING("  → No se encontró archivo de imagen para asignar"))

            creadas += 1

        self.stdout.write(self.style.SUCCESS(f"Listo. Propiedades procesadas: {creadas}"))
