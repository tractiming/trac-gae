from django.conf.urls import url, include
from rest_framework import routers

from trac.views import (
    user_views, session_views, reader_views, team_views, auth_views
)


router = routers.DefaultRouter()
router.register(r'users', user_views.UserViewSet, 'User')
router.register(r'score', team_views.ScoringViewSet, 'Score')


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^register/$', auth_views.register),
    url(r'^login/$', auth_views.login),
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),

    url(r'^edit_split/$', session_views.edit_split),
    url(r'^raceregistration/$', session_views.create_race, name='racereg'),
    url(r'^upload_workouts/$', session_views.upload_workouts),

    url(r'^give_athlete_password/$', user_views.give_athlete_password),
    url(r'^reset_password/$', auth_views.reset_password),
    url(r'^send_email/$', user_views.send_email),
    url(r'^verifyLogin/$', auth_views.verify_login),
    url(r'^request_quote/$', user_views.request_quote),

    url(r'^updates/$', reader_views.post_splits, name='updates'),
]
