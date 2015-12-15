from django.shortcuts import render
from django.template import RequestContext
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt

def index(request):
    return render(request, 'index.html', {})

def demo(request):
    return render(request, 'blog.html', {})

def mile_demo(request):
    return render(request, 'ignatius.html', {})

def cinci_demo(request):
    return render(request, 'cinci.html', {})
    
@ensure_csrf_cookie
def login(request):
    return render(request, 'login.html', {})

def live_view(request):
    return render(request, 'live_view.html', {})

def register(request):
    return render(request, 'register.html', {})

@csrf_exempt
def home(request):
    return render(request, 'home.html', {})

def create(request):
    return render(request, 'create.html', {})

def calendar(request):
    return render(request, 'calendar.html', {})

def settings(request):
    return render(request, 'settings.html', {})

def analyze(request):
    return render(request, 'analyze.html', {})

def readers(request):
    return render(request, 'readers.html', {})
    
def tags(request):
    return render(request, 'tags.html', {})

def caramile(request):
    return render(request, 'caramile.html', {})

def lakeforest(request):
    return render(request, 'lakeforest.html', {})

def score(request, org = None):
    if org == None:
        return render(request, 'teams.html', {})
    else:
        return render(request, 'score.html', {'org': org})

def individual(request, id = 0):
    return render(request, 'individual.html', {'id': id})

def tutorial(request, page = 1):
    return render(request, 'tutorial.html', {'page': page})

def usersettings(request, pk= None, token = None):
    return render(request, 'UserSettings.html', {'pk': pk, 'token' : token})

def account_settings(request):
    return render(request, 'account_settings.html')

def ipntest(request):
    return render(request, 'ipnTest.html')

def error404(request):
    return render(request, '404.html')

def error500(request):
    return render(request, '500.html')
