from django.conf.urls import patterns, url
from common import views

urlpatterns = patterns('',
        url(r'^createworkout/$', views.create_workout, name='create_workout'),
        url(r'^addtag/$', views.add_tag, name='add_tag'),
        url(r'^managetags/$', views.tag_manager, name='tag_manager'),
        url(r'^addreader/$', views.add_reader, name='add_reader'),
        url(r'^managereaders/$', views.reader_manager, name='reader_manager'),
)
