from django.contrib import sitemaps
from django.core.urlresolvers import reverse

class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['website:index', 'website:login', 'website:register','website:demo','website:score', 'website:tutorial']

    def location(self, item):
        return reverse(item)
