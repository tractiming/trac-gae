from django.conf.urls import patterns, include, url
from django.contrib import admin
from rest_framework_nested import routers

admin.autodiscover()

import views

router = routers.DefaultRouter()
router.register(r'performancerecords', views.PerformanceRecordViewSet, 'PerformanceRecord')

urlpatterns = patterns('',
        url(r'^VO2Max/$', views.VO2Max),
        #url(r'^est_distance/$', views.est_distance),
        url(r'^analyze/$', views.analyze),
		url(r'^', include(router.urls)),
)
