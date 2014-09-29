from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'tracd.views.home', name='home'),
    url(r'^$', include('common.urls')),
    url(r'^updates/', include('updates.urls')),
    url(r'^users/', include('users.urls')),
    url(r'^results/', include('results.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
