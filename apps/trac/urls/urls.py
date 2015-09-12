from django.conf.urls import url, include
from rest_framework import routers
from trac.views import user_views, session_views, tag_views, reader_views, team_views

router = routers.DefaultRouter()
router.register(r'sessions', session_views.TimingSessionViewSet, 'Session')
router.register(r'readers', reader_views.ReaderViewSet, 'Reader')
router.register(r'coaches', user_views.CoachViewSet, 'Coach')
router.register(r'athletes', user_views.AthleteViewSet, 'Athlete')
router.register(r'tags', tag_views.TagViewSet, 'Tag')
router.register(r'score', team_views.ScoringViewSet, 'Score')
router.register(r'teams', team_views.TeamViewSet, 'Team')

urlpatterns = [
        url(r'^', include(router.urls)),

        # General endpoints.(?P<username>.+)/
        url(r'^register/$', user_views.RegistrationView.as_view()),
        url(r'^verifyLogin/$', user_views.verifyLogin.as_view()),
        url(r'^login/$', user_views.login),
        url(r'^userType/$', user_views.userType.as_view()),

        # Timing session functionality.
        url(r'^open_session/$', session_views.open_session),
        url(r'^close_session/$', session_views.close_session),
        url(r'^start_timer/$', session_views.start_session),
        url(r'^TimingSessionReset/$', session_views.reset_session),
        url(r'^raceregistration/$', session_views.create_race, name='racereg'),
        url(r'^filtered_results/$', session_views.filtered_results),
        url(r'^session_Pag/$', session_views.sessions_paginate),
        url(r'^reg_tag/$', tag_views.WorkoutTags),
        url(r'^reg_manytags/$', tag_views.ManyDefaultTags),
        url(r'^time_create/$', session_views.time_create),
        url(r'^edit_athletes/$', user_views.edit_athletes),
        url(r'^edit_split/$', session_views.edit_split),
        #url(r'^individual_splits/$', views.IndividualTimes),
        url(r'^edit_info/$', user_views.edit_info),
        url(r'^get_info/$', user_views.get_info),
        url(r'^team_results/$', session_views.team_results),
        url(r'^upload_workouts/$', session_views.upload_workouts),

        url(r'^token_validation/$', user_views.token_validation),
        url(r'^reset_password/$', user_views.reset_password),
        url(r'^change_password/$', user_views.change_password),
        url(r'^send_email/$', user_views.send_email),
        url(r'^tutorial_limiter/$', user_views.tutorial_limiter),
        #url(r'^VO2Max/$', views.VO2Max),
        #url(r'^est_distance/$', views.est_distance),
        #url(r'^analyze/$', views.analyze),
        #url(r'^IndividualTimes/$', views.IndividualTimes.as_view()),

        # Endpoint for readers.
        url(r'^updates/$', reader_views.post_splits, name='updates'),
        # Rest framework authentication.
        url(r'^api-auth/', include('rest_framework.urls',
                                   namespace='rest_framework'))
]
