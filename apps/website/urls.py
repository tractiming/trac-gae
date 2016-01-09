from django.conf.urls import url, include, patterns, handler404, handler500
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.generic import TemplateView

from website import views


urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='index.html'),
        name='index'),

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

    url(r'^liveview', TemplateView.as_view(template_name='live_view.html'),
        name='liveview'),
    url(r'^calendar', TemplateView.as_view(template_name='calendar.html'),
        name='calendar'),
    url(r'^create', TemplateView.as_view(template_name='create.html'),
        name='create'),
    url(r'^roster', TemplateView.as_view(template_name='roster.html'),
        name='roster'),
    url(r'^analyze', TemplateView.as_view(template_name='analyze.html'),
        name='analyze'),
    url(r'^readers', TemplateView.as_view(template_name='readers.html'),
        name='readers'),
    url(r'^tags', TemplateView.as_view(template_name='tags.html'),
        name='tags'),
    url(r'^account_settings/$',
        TemplateView.as_view(template_name='account_settings.html'),
        name='account_settings'),

    url(r'^score/$', views.score, name='score'),
    url(r'^score/(?P<org>.+)/$', views.score, name='score'),
    url(r'^individual/(?P<id>.+)/$', views.individual, name='individual_splits'),
    url(r'^Tutorial/(?P<page>.+)/$', views.tutorial, name='tutorial'),
    url(r'^UserSettings/(?P<pk>.+)/(?P<token>.+)/$', views.usersettings,
        name="UserSettings"),

    url(r'^google-signin/$',
        csrf_exempt(TemplateView.as_view(template_name='googlelogin.html')),
        name='googlesignin'),
    url(r'^google-auth/$', 'accounts.views.google_auth'),
)

handler404 = TemplateView.as_view(template_name='404.html')
handler500 = TemplateView.as_view(template_name='500.html')
