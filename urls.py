from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    url(r'^', include('website.urls', namespace='website')),
    url(r'^api/', include('trac.urls.api', app_name='trac', namespace='api')),
    url(r'^api/', include('trac.urls.internal', app_name='trac',
                          namespace='internal')),
    url(r'^stats/', include('stats.urls', app_name='stats', namespace='stats')),
    url(r'^', include('accounts.urls', app_name='accounts',
                      namespace='accounts')),
    url(r'^notifications/', include('notifications.urls',
                                    app_name='notifications',
                                    namespace='notifications')),
    url(r'^oauth2/', include('oauth2_provider.urls', app_name='oauth2',
                             namespace='oauth2_provider')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^payments/', include('payments.api.urls', namespace='payments')),
    url(r'^docs/', include('trac.urls.docs'))
)
