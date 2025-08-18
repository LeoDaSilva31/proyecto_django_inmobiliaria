# propiedades/management/commands/load_demo_propiedades.py
import os, random, itertools
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.db import transaction

from propiedades.models import Propiedad, PropiedadImagen

TIPOS = ["casa", "departamento", "ph", "local", "terreno", "otro"]
OPERACIONES = ["venta", "alquiler", "temporario"]

# Localidades/provincias de ejemplo (podés editar libremente)
LOCALIDADES_BA = [
    ("Quilmes", "Buenos Aires"),
    ("Berazategui", "Buenos Aires"),
    ("Avellaneda", "Buenos Aires"),
    ("Lanús", "Buenos Aires"),
    ("Lomas de Zamora", "Buenos Aires"),
    ("La Plata", "Buenos Aires"),
    ("Florencio Varela", "Buenos Aires"),
    ("Almirante Brown", "Buenos Aires"),
    ("San Isidro", "Buenos Aires"),
    ("Vicente López", "Buenos Aires"),
]

CALLES = [
    "San Martín", "Belgrano", "Rivadavia", "Mitre", "Sarmiento",
    "Alsina", "Lavalle", "Moreno", "Independencia", "9 de Julio",
    "25 de Mayo", "Dorrego", "Brown", "Alem", "Yrigoyen"
]

DESCRIPCIONES = [
    "Propiedad luminosa en excelente ubicación. Cercanía a comercios y transporte.",
    "Amplios ambientes y buena ventilación. Oportunidad.",
    "Ideal familia. Buen estado general y posibilidad de ampliación.",
    "Listo para habitar. Zona tranquila con acceso rápido a avenidas.",
    "Excelente relación precio/calidad. Opción de cochera.",
]

def _rand_precio(operacion: str):
    """Genera precio en USD o en ARS según operación."""
    if operacion == "venta":
        usd = random.randint(50000, 420000)  # US$ 50k - 420k
        return Decimal(usd), None
    elif operacion == "temporario":
        # alquiler temporario en ARS (valores ficticios)
        ars = random.randint(150000, 1200000)
        return None, Decimal(ars)
    else:  # alquiler
        ars = random.randint(200000, 2000000)
        return None, Decimal(ars)

def _rand_superficies():
    tot = random.randint(30, 400)
    cub = random.randint(25, tot)
    return tot, cub

def _rand_latlng():
    """
    Coordenadas aproximadas GBA sur (alrededores de Quilmes).
    ±0.05° ~ 5.5 km; perfecto para probar 'cercanas'.
    """
    base_lat, base_lng = -34.72, -58.25
    lat = base_lat + random.uniform(-0.05, 0.05)
    lng = base_lng + random.uniform(-0.05, 0.05)
    return round(lat, 6), round(lng, 6)

def _buscar_imagenes(img_dir: Path):
    """Devuelve lista de rutas a imágenes válidas dentro de img_dir."""
    exts = {".jpg", ".jpeg", ".png", ".webp", ".JPG", ".JPEG", ".PNG", ".WEBP"}
    files = []
    if not img_dir.exists():
        return files
    for name in os.listdir(img_dir):
        p = img_dir / name
        if p.is_file() and p.suffix in exts:
            files.append(p)
    # Damos prioridad a archivos que empiezan con 'foto'
    files.sort(key=lambda x: (not x.name.lower().startswith("foto"), x.name.lower()))
    return files

class Command(BaseCommand):
    help = "Carga propiedades de prueba usando imágenes locales."

    def add_arguments(self, parser):
        parser.add_argument(
            "--img-dir",
            default=r"C:\Users\ldasi\Pictures\ejemplo",
            help="Carpeta local con imágenes (default: C:\\Users\\ldasi\\Pictures\\ejemplo)",
        )
        parser.add_argument(
            "--count", type=int, default=20,
            help="Cantidad de propiedades a crear (default: 20)",
        )
        parser.add_argument(
            "--max-secundarias", type=int, default=4,
            help="Máximo de imágenes secundarias por propiedad (default: 4, tope real 10)",
        )
        parser.add_argument(
            "--seed", type=int, default=None,
            help="Semilla para resultados repetibles (opcional)",
        )
        parser.add_argument(
            "--destacadas", type=int, default=10,
            help="Cantidad deseada de destacadas en total (default: 10, se respeta el tope ya existente)",
        )

    def handle(self, *args, **opts):
        img_dir = Path(opts["img_dir"])
        count = opts["count"]
        max_sec = min(10, max(0, opts["max_secundarias"]))
        seed = opts.get("seed")
        desired_destacadas = max(0, min(10, opts.get("destacadas", 10)))

        if seed is not None:
            random.seed(seed)

        imgs = _buscar_imagenes(img_dir)
        if not imgs:
            raise CommandError(f"No encontré imágenes en: {img_dir}")

        self.stdout.write(self.style.NOTICE(f"Usando {len(imgs)} imágenes de {img_dir}"))

        # Calcular cuántas destacadas podemos marcar
        ya_destacadas = Propiedad.objects.filter(destacada=True).count()
        para_marcar = max(0, desired_destacadas - ya_destacadas)

        # Ciclar imágenes si hay menos que 'count'
        img_cycle = itertools.cycle(imgs)

        creadas = 0
        destacadas_marcadas = 0

        with transaction.atomic():
            for i in range(count):
                tipo = random.choice(TIPOS)
                operacion = random.choices(OPERACIONES, weights=[0.55, 0.4, 0.05], k=1)[0]
                (loc, prov) = random.choice(LOCALIDADES_BA)

                hab = random.randint(1, 5)
                banos = random.randint(1, max(1, min(3, hab)))
                cochera = random.random() < 0.45
                mascotas = random.random() < 0.6

                precio_usd, precio_ars = _rand_precio(operacion)
                sup_tot, sup_cub = _rand_superficies()
                lat, lng = _rand_latlng()

                # Título y texto
                titulo = f"{tipo.capitalize()} en {loc} - {hab} amb, {sup_tot} m²"
                descripcion = random.choice(DESCRIPCIONES)

                # Dirección simple
                calle = random.choice(CALLES)
                numero = random.randint(100, 5900)
                direccion = f"{calle} {numero}"

                # Crear la instancia (sin guardar todavía portada)
                p = Propiedad(
                    titulo=titulo,
                    descripcion=descripcion,
                    precio_usd=precio_usd,
                    precio_pesos=precio_ars,
                    tipo=tipo,
                    tipo_operacion=operacion,
                    habitaciones=hab,
                    banos=banos,
                    cochera=cochera,
                    acepta_mascotas=mascotas,
                    superficie_total=sup_tot,
                    superficie_cubierta=sup_cub,
                    estado="activa",
                    direccion=direccion,
                    localidad=loc,
                    provincia=prov,
                    pais="Argentina",
                    latitud=lat,
                    longitud=lng,
                )

                # Portada (obligatoria)
                portada_path = next(img_cycle)
                with open(portada_path, "rb") as fh:
                    # No guardamos aún para que pase por tu save() y convierta a WEBP
                    p.imagen_principal.save(portada_path.name, File(fh), save=False)

                # ¿Destacada?
                if para_marcar > 0:
                    p.destacada = True
                    para_marcar -= 1
                    destacadas_marcadas += 1

                # Guardar (dispara conversion a webp, normalizaciones y código)
                p.save()

                # Secundarias (hasta max 10)
                n_sec = random.randint(0, max_sec)
                if n_sec > 0:
                    # Evitamos repetir exactamente la portada como primera secundaria
                    usadas = {portada_path}
                    for _ in range(n_sec):
                        sec_path = next(img_cycle)
                        # Podría tocar la misma; lo cambiamos si coincide
                        if sec_path in usadas:
                            sec_path = next(img_cycle)
                        usadas.add(sec_path)
                        with open(sec_path, "rb") as fh2:
                            pi = PropiedadImagen(propiedad=p)
                            # Guardamos directo en el field para que pase por save() y convierta a WEBP
                            pi.imagen.save(sec_path.name, File(fh2), save=True)

                creadas += 1

        self.stdout.write(self.style.SUCCESS(
            f"OK: creadas {creadas} propiedades (destacadas nuevas: {destacadas_marcadas})."
        ))
