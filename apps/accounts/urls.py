from django.conf.urls import url, patterns


urlpatterns = patterns('',
    url(r'^google-auth/$', 'accounts.views.google_auth'),
    url(r'^stripe-single/$', 'accounts.views.stripeSingleCharge'),
    url(r'^stripe-Customer/$', 'accounts.views.stripe_CustomerPayment')
)
