from django.core.management.base import BaseCommand
from propiedades.models import Propiedad

class Command(BaseCommand):
    help = "Completa lat/long a partir de la dirección en Propiedad (usa save() con geocodificación)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Geocodificar aunque ya tenga lat/long")

    def handle(self, *args, **opts):
        qs = Propiedad.objects.all().order_by("id")
        done = 0
        for p in qs.iterator():
            # save(geocode=True) ya decide internamente si hace falta
            if opts["force"] or p.latitud is None or p.longitud is None:
                p.save()  # dispara el hook del save
                done += 1
                self.stdout.write(f"OK {p.codigo}: {p.latitud}, {p.longitud}")
        self.stdout.write(self.style.SUCCESS(f"Listo: {done} propiedades actualizadas"))
