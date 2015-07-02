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

def register(request):
    return render(request, 'register.html', {})

def home(request):
    return render(request, 'home.html', {})

def create(request):
    return render(request, 'create.html', {})

def calendar(request):
    return render(request, 'calendar.html', {})

def settings(request):
    return render(request, 'settings.html', {})

def readers(request):
    return render(request, 'readers.html', {})
    
def tags(request):
    return render(request, 'tags.html', {})

def caramile(request):
    return render(request, 'caramile.html', {})

def score(request, org = None):
    if org == None:
        return render(request, 'teams.html', {})
    else:
        return render(request, 'score.html', {'org': org})