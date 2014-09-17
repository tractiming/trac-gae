from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt
from views import workout_data

urlpatterns = patterns('',
    url(r'^$', csrf_exempt(workout_data)),
)
