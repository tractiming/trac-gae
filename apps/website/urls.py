from django.conf.urls import url, include, patterns
from django.views.generic import TemplateView
import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^demo', views.demo, name='demo'),
    url(r'^mile_demo', views.mile_demo, name='mile_demo'),
    url(r'^cinci_demo', views.cinci_demo, name='cinci_demo'),
    url(r'^home', views.home, name='home'),
    url(r'^login', views.login, name='login'),
    url(r'^register', views.register, name='register'),
    url(r'^liveview', views.live_view, name='liveview'),
    url(r'^calendar', views.calendar, name='calendar'),
    url(r'^create', views.create, name='create'),
    url(r'^settings', views.settings, name='settings'),
    url(r'^analyze', views.analyze, name='analyze'),
    url(r'^readers', views.readers, name='readers'),
    url(r'^tags', views.tags, name='tags'),    
    url(r'^caramile', views.caramile, name='caramile'),
    url(r'^lakeforest', views.lakeforest, name='lakeforest'),
    url(r'^score/$', views.score, name='score'),
    url(r'^score/(?P<org>.+)/$', views.score, name='score'),
    url(r'^individual/(?P<id>.+)/$', views.individual, name='individual_splits'),
    url(r'^Tutorial/(?P<page>.+)/$', views.tutorial, name='tutorial'),
    url(r'^UserSettings/(?P<pk>.+)/(?P<token>.+)/$', views.usersettings, name="UserSettings"),
    url(r'^account_settings/$', views.account_settings, name='account_settings'),
    url(r'^ipntest/$', views.ipntest, name='ipnTest'),
    )
