from django.shortcuts import render
from django.template import RequestContext
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def index(request):
    #context = RequestContext(request)
    #context_dict = {}
    return render(request, 'index.html', {})

