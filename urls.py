from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    url(r'^', include('website.urls', namespace='website')),
    url(r'^api/', include('trac.urls.api', app_name='trac', namespace='api')),
    url(r'^api/', include('trac.urls.internal', app_name='trac',
                          namespace='internal')),
    url(r'^stats/', include('stats.urls', app_name='stats', namespace='stats')),
    url(r'^oauth2/', include('oauth2_provider.urls', app_name='oauth2',
                             namespace='oauth2_provider')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^payments/', include('djstripe.urls', namespace='djstripe')),
    url(r'^docs/', include('rest_framework_swagger.urls'))
)
