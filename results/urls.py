from django.conf.urls import patterns, url
from results import views

urlpatterns = patterns('',
        url(r'^$', views.results_home, name='results_home'),
        url(r'^workoutresults/(?P<wnum>[0-9])/$', views.workout_results,
            name='workout_results'),
        )
