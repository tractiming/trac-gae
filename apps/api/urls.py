from django.conf.urls import url, include
from rest_framework import routers
import views

router = routers.DefaultRouter()
router.register(r'sessions', views.TimingSessionViewSet, 'Session')
router.register(r'readers', views.ReaderViewSet, 'Reader')
router.register(r'coaches', views.CoachViewSet, 'Coach')
router.register(r'athletes', views.AthleteViewSet, 'Athlete')
router.register(r'tags', views.TagViewSet, 'Tag')
router.register(r'score', views.ScoringViewSet, 'Score')
#router.register(r'score/(?P<org>.+)', views.ScoringViewSet, 'Score')

urlpatterns = [
        url(r'^', include(router.urls)),

        #url(r'^score/(?P<org>.+)/$', views.ScoringViewSet.as_view()),

        # General endpoints.(?P<username>.+)/
        url(r'^register/$', views.RegistrationView.as_view()),
        url(r'^verifyLogin/$', views.verifyLogin.as_view()),
        url(r'^userType/$', views.userType.as_view()),
        #url(r'^auth_verify/$', views.verify_login, name='auth_verify'),

        # Timing session functionality.
        url(r'^open_session/$', views.open_session),
        url(r'^close_session/$', views.close_session),
        url(r'^start_timer/$', views.start_session),
        url(r'^TimingSessionReset/$', views.reset_session),
        url(r'^raceregistration/$', views.create_race, name='racereg'),
        url(r'^filtered_results/$', views.filtered_results),
        url(r'^session_Pag/$', views.sessions_paginate),
        url(r'^reg_tag/$', views.WorkoutTags),
        url(r'^reg_manytags/$', views.ManyDefaultTags),
        url(r'^time_create/$', views.time_create),
        url(r'^edit_athletes/$', views.edit_athletes),
        url(r'^edit_split/$', views.edit_split),
        url(r'^individual_splits/$', views.IndividualTimes),
        url(r'^team_results/$', views.team_results),

        #url(r'^IndividualTimes/$', views.IndividualTimes.as_view()),

        # Endpoint for readers.
        url(r'^updates/$', views.post_splits, name='updates'),

        # Rest framework authentication.
        url(r'^api-auth/', include('rest_framework.urls',
            namespace='rest_framework'))
]
