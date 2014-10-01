from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

import common.views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'tracd.views.home', name='home'),
    url(r'^$', common.views.index, name='index'),
    url(r'^common/', include('common.urls')),
    url(r'^updates/', include('updates.urls')),
    url(r'^users/', include('users.urls')),
    url(r'^results/', include('results.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
