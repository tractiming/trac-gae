from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

import views

urlpatterns = patterns('',
        url(r'^VO2Max/$', views.VO2Max),
        #url(r'^est_distance/$', views.est_distance),
        url(r'^analyze/$', views.analyze),
)
