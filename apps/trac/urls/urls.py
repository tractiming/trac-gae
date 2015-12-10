from django.conf.urls import url, include
from rest_framework import routers

from trac.views import (
    user_views, session_views, tag_views, reader_views, team_views,
    split_views, auth_views
)


router = routers.DefaultRouter()
router.register(r'sessions', session_views.TimingSessionViewSet, 'Session')
router.register(r'readers', reader_views.ReaderViewSet, 'Reader')
router.register(r'coaches', user_views.CoachViewSet, 'Coach')
router.register(r'athletes', user_views.AthleteViewSet, 'Athlete')
router.register(r'tags', tag_views.TagViewSet, 'Tag')
router.register(r'score', team_views.ScoringViewSet, 'Score')
router.register(r'teams', team_views.TeamViewSet, 'Team')
router.register(r'splits', split_views.SplitViewSet, 'Split')
router.register(r'users', user_views.UserViewSet, 'User')

urlpatterns = [
        url(r'^', include(router.urls)),

        # General endpoints.
        url(r'^verifyLogin/$', user_views.verifyLogin.as_view()),

        # Timing session functionality.
        url(r'^raceregistration/$', session_views.create_race, name='racereg'),
        url(r'^reg_tag/$', tag_views.WorkoutTags),
        url(r'^reg_manytags/$', tag_views.ManyDefaultTags),
        url(r'^edit_athletes/$', user_views.edit_athletes),
        url(r'^edit_split/$', session_views.edit_split),
        url(r'^upload_workouts/$', session_views.upload_workouts),

        url(r'^token_validation/$', user_views.token_validation),
        url(r'^reset_password/$', auth_views.reset_password),
        url(r'^send_email/$', user_views.send_email),
        url(r'^stripe/$', user_views.subscribe),
        url(r'^give_athlete_password/$', user_views.give_athlete_password),
        url(r'^individual_splits/$', session_views.add_individual_splits),
        url(r'^RegisterDefaultRunners/$', tag_views.RegisterDefaultRunners),

        url(r'^register/$', auth_views.register),
        url(r'^login/$', auth_views.login),
        url(r'^logout/$', auth_views.logout),

        # Endpoint for readers.
        url(r'^updates/$', reader_views.post_splits, name='updates'),

        # Rest framework authentication.
        url(r'^api-auth/', include('rest_framework.urls',
                                   namespace='rest_framework'))
]
