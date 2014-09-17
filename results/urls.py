from django.conf.urls import patterns, url
from results import views

urlpatterns = patterns('',
        url(r'^$', views.results_home, name='results_home'),
        url(r'^createworkout/$', views.create_workout, name='create_workout'),
        url(r'^addtag/$', views.add_tag, name='add_tag'),
        url(r'^workoutresults/(?P<wnum>[0-9])/$', views.workout_results,
            name='workout_results'),
        )
