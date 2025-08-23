# django_inmobiliaria/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from propiedades.sitemaps import PropiedadSitemap

class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return ["home", "nosotros", "propiedades_listado"]

    def location(self, item):
        return reverse(item)

sitemaps = {
    "static": StaticViewSitemap,
    "propiedades": PropiedadSitemap,
}
