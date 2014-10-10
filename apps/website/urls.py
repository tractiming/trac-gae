from django.conf.urls import url, include, patterns
from django.views.generic import TemplateView
import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
)
