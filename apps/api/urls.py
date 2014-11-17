from django.conf.urls import url, include
from rest_framework import routers
import views

router = routers.DefaultRouter()
router.register(r'sessions', views.TimingSessionViewSet, 'Session')
router.register(r'readers', views.ReaderViewSet, 'Reader')
router.register(r'athletes', views.AthleteViewSet, 'Athlete')
router.register(r'tags', views.TagViewSet, 'Tag')

urlpatterns = [
        url(r'^', include(router.urls)),
        url(r'^register/$', views.RegistrationView.as_view()),
        url(r'^updates/$', views.post_splits, name='updates'),
        url(r'^auth_verify/$', views.verify_login, name='auth_verify'),
        url(r'^api-auth/', include('rest_framework.urls',
            namespace='rest_framework'))
]