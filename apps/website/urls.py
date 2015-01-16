from django.conf.urls import url, include, patterns
from django.views.generic import TemplateView
import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^login', views.login, name='login'),
    # url(r'^register', views.register, name='register'),
    url(r'^liveview', views.live_view, name='liveview'),
    url(r'^calendar', views.calendar, name='calendar'),
    url(r'^create', views.create, name='create'),
    url(r'^home', views.home, name='home'),
    url(r'^settings', views.settings, name='settings'),
)
