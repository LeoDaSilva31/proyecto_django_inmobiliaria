from django.contrib.sitemaps import Sitemap

class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return ["/", "/nosotros/", "/propiedades/"]

    def location(self, item):
        return item
