from django.shortcuts import render
from django.template import RequestContext
from django.views.decorators.csrf import ensure_csrf_cookie

def index(request):
    return render(request, 'index.html', {})

@ensure_csrf_cookie
def login(request):
    return render(request, 'login.html', {})

def live_view(request):
    return render(request, 'liveView.html', {})

def home(request):
    return render(request, 'home.html', {})

def create(request):
    return render(request, 'create.html', {})

def calendar(request):
    return render(request, 'calendar.html', {})