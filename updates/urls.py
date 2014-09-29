from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt
import views

urlpatterns = patterns('',
    url(r'^$', views.session_data, name='session_data'),
)
