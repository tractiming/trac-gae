from django.conf.urls import url, include
from rest_framework_nested import routers

from trac.views.reader_views import ReaderViewSet
from trac.views.session_views import TimingSessionViewSet, CheckpointViewSet
from trac.views.split_views import SplitViewSet
from trac.views.tag_views import TagViewSet
from trac.views.team_views import TeamViewSet
from trac.views.user_views import AthleteViewSet, CoachViewSet


router = routers.DefaultRouter()
router.register(r'athletes', AthleteViewSet, 'Athlete')
router.register(r'coaches', CoachViewSet, 'Coach')
router.register(r'readers', ReaderViewSet, 'Reader')
router.register(r'sessions', TimingSessionViewSet, 'Session')
router.register(r'splits', SplitViewSet, 'Split')
router.register(r'tags', TagViewSet, 'Tag')
router.register(r'teams', TeamViewSet, 'Team')

sessions_router = routers.NestedSimpleRouter(router, r'sessions',
                                             lookup='session')
sessions_router.register(r'checkpoints', CheckpointViewSet,
                         base_name='checkpoints')


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^', include(sessions_router.urls))
]
