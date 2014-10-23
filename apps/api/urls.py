from django.conf.urls import url, include
from rest_framework import routers
import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet, 'User')
router.register(r'sessions', views.TimingSessionViewSet, 'Session')

urlpatterns = [
        url(r'^', include(router.urls)),
        url(r'^register/$', views.RegistrationView.as_view()),
        url(r'^updates/$', views.post_splits, name='updates'),
        url(r'^api-auth/', include('rest_framework.urls',
            namespace='rest_framework'))
]
