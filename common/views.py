from django.shortcuts import render
from django.template import RequestContext

def index(request):
    """Returns the home page for the overall site."""
    context = RequestContext(request)
    context_dict = {}
    return render(request, 'index.html', context_dict)
