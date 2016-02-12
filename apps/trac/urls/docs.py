from django.conf.urls import url
from django.views.decorators.cache import cache_page

from rest_framework_swagger.views import (
    SwaggerResourcesView, SwaggerApiView, SwaggerUIView
)


urlpatterns = [
    url(r'^$',
        SwaggerUIView.as_view(),
        name="django.swagger.base.view"),
    url(r'^api-docs/$',
        SwaggerResourcesView.as_view(),
        name="django.swagger.resources.view"),
    url(r'^api-docs/(?P<path>.*)/?$',
        cache_page(60 *15)(SwaggerApiView.as_view()),
        name='django.swagger.api.view'),
]
