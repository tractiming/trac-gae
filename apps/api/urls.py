from django.conf.urls import url, include
from rest_framework import routers
import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'sessions', views.TimingSessionViewSet)

urlpatterns = [
        url(r'^', include(router.urls)),
        url(r'^register/$', views.RegistrationView.as_view()),
        url(r'^api-auth/', include('rest_framework.urls',
            namespace='rest_framework'))
]
