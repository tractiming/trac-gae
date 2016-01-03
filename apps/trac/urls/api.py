from django.conf.urls import url, include
from rest_framework import routers

from trac.views import (
    user_views, session_views, tag_views, reader_views, team_views,
    split_views, auth_views
)


router = routers.DefaultRouter()
router.register(r'athletes', user_views.AthleteViewSet, 'Athlete')
router.register(r'coaches', user_views.CoachViewSet, 'Coach')
router.register(r'readers', reader_views.ReaderViewSet, 'Reader')
router.register(r'score', team_views.ScoringViewSet, 'Score')
router.register(r'sessions', session_views.TimingSessionViewSet, 'Session')
router.register(r'splits', split_views.SplitViewSet, 'Split')
router.register(r'tags', tag_views.TagViewSet, 'Tag')
router.register(r'teams', team_views.TeamViewSet, 'Team')
router.register(r'users', user_views.UserViewSet, 'User')


urlpatterns = [
        url(r'^', include(router.urls)),
        url(r'^api-auth/', include('rest_framework.urls',
                                   namespace='rest_framework'))
]
