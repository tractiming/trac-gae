from django.conf.urls import url, include, patterns, handler404, handler500
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap

from website import views
from website.sitemaps import StaticViewSitemap


sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='index.html'),
        name='index'),
    url(r'^product', TemplateView.as_view(template_name='product.html'),
        name='product'),
    url(r'^quote', TemplateView.as_view(template_name='quote.html'),
        name='quote'),

    url(r'^home', csrf_exempt(
        TemplateView.as_view(template_name='home.html')),
        name='home'),
    url(r'^login', ensure_csrf_cookie(
        TemplateView.as_view(template_name='login.html')),
        name='login'),
    url(r'^register', TemplateView.as_view(template_name='register.html'),
        name='register'),

    url(r'^demo', TemplateView.as_view(template_name='blog.html'),
        name='demo'),
    url(r'^mile_demo', TemplateView.as_view(template_name='ignatius.html'),
        name='mile_demo'),
    url(r'^cinci_demo', TemplateView.as_view(template_name='cinci.html'),
        name='cinci_demo'),
    url(r'^caramile', TemplateView.as_view(template_name='caramile.html'),
        name='caramile'),
    url(r'^lakeforest', TemplateView.as_view(template_name='lakeforest.html'),
        name='lakeforest'),
    url(r'^badwater', TemplateView.as_view(template_name='badwater.html'),
        name='badwater'),

    url(r'^liveview', TemplateView.as_view(template_name='live_view.html'),
        name='liveview'),
    url(r'^create', TemplateView.as_view(template_name='create.html'),
        name='create'),
    url(r'^roster', TemplateView.as_view(template_name='roster.html'),
        name='roster'),
    url(r'^analyze', TemplateView.as_view(template_name='analyze.html'),
        name='analyze'),
    url(r'^readers', TemplateView.as_view(template_name='readers.html'),
        name='readers'),
    #url(r'^tags', TemplateView.as_view(template_name='tags.html'),
    #    name='tags'),
    url(r'^faqs', TemplateView.as_view(template_name='faqs.html'),
        name='faqs'),
    url(r'^privacy', TemplateView.as_view(template_name='privacy.html'),
        name='privacy'),
    url(r'^terms', TemplateView.as_view(template_name='terms.html'),
        name='terms'),
    url(r'^text', TemplateView.as_view(template_name='messaging.html'),
        name='text'),

    url(r'^payments/change_card',
        TemplateView.as_view(template_name='change_card.html'),
        name='change_card'),
    url(r'^payments/history',
        TemplateView.as_view(template_name='history.html'),
        name='history'),
    url(r'^payments/subscribe',
        TemplateView.as_view(template_name='subscribe_form.html'),
        name='subscribe'),

    url(r'^account_settings/(?P<page>.+)/$', views.account_settings, name='account_settings'),
    url(r'^score/$', views.score, name='score'),
    url(r'^score/(?P<org>.+)/$', views.score, name='score'),
    url(r'^individual/(?P<id>.+)/$', views.individual, name='individual_splits'),
    url(r'^tutorial/(?P<page>.+)/$', views.tutorial2, name='tutorial2'),
    url(r'^UserSettings/(?P<pk>.+)/(?P<token>.+)/$', views.usersettings,
        name="UserSettings"),

    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap')
)

handler404 = TemplateView.as_view(template_name='404.html')
handler500 = TemplateView.as_view(template_name='500.html')
