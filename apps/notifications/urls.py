from django.conf.urls import url, include
from rest_framework import routers

from notifications.views import SubscriptionViewSet, notify


router = routers.DefaultRouter()
router.register(r'subscriptions', SubscriptionViewSet, 'Subscription')


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^notify', notify)
]
