from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

import views

urlpatterns = patterns('',
        url(r'^TFFRS_query/$', views.TFFRS_query),
	url(r'^TFFRS_team_query/$', views.TFFRS_team_query),
        url(r'^TFFRS_fetch/$', views.TFFRS_fetch),
	url(r'^TFFRS_scrape_team/$', views.TFFRS_scrape_team),
        url(r'^AdotNet_query/$', views.AdotNet_query),
        url(r'^AdotNet_fetch/$', views.AdotNet_fetch),
        url(r'^Po10_query/$', views.Po10_query),
        url(r'^Po10_fetch/$', views.Po10_fetch),
)
