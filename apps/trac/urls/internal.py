from django.conf.urls import url

from trac.views import (
    user_views, session_views, tag_views, reader_views, team_views,
    split_views, auth_views
)


urlpatterns = [

    url(r'^edit_athletes/$', user_views.edit_athletes),
    url(r'^edit_split/$', session_views.edit_split),
    url(r'^raceregistration/$', session_views.create_race, name='racereg'),
    url(r'^upload_workouts/$', session_views.upload_workouts),

    url(r'^give_athlete_password/$', user_views.give_athlete_password),
    url(r'^individual_splits/$', session_views.add_individual_splits),
    url(r'^reset_password/$', auth_views.reset_password),
    url(r'^send_email/$', user_views.send_email),
    url(r'^stripe/$', user_views.subscribe),
    url(r'^token_validation/$', user_views.token_validation),
    url(r'^verifyLogin/$', user_views.verifyLogin.as_view()),
    url(r'^request_quote/$', user_views.request_quote),

    url(r'^updates/$', reader_views.post_splits, name='updates'),
]
