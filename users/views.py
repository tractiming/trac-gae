from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User, Group
from util import user_type
from users.models import AthleteProfile, CoachProfile
from users.forms import UserForm

def register(request):
    """Registers a user and saves their information to the database."""
    context = RequestContext(request)

    registered = False

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)

        if user_form.is_valid():
           
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            
            user_type = user_form.cleaned_data['user_type']
            if user_type == '1':
                # Register an athlete.
                athlete = AthleteProfile()
                athlete.user = user
                athlete.save()

            elif user_type == '2':
                # Register a coach.
                coach = CoachProfile()
                coach.user = user
                coach.save()

            registered = True
            new_user = authenticate(username=request.POST['username'],
                                    password=request.POST['password'])
            auth_login(request, new_user)
            return HttpResponseRedirect('/')

        else:
            print user_form.errors

    else:
        user_form = UserForm()

    return render(request, 'users/register.html', {'user_form': user_form,
                                        'registered': registered})    

def user_login(request):
    """Logs a user in."""
    context = RequestContext(request)

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                auth_login(request, user)
                return HttpResponseRedirect('/users/home')
            else:
                return HttpResponse("Your trac account is disabled")

        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login credentials.")

    else:
        return render(request, 'users/login.html')

@login_required
def user_logout(request):
    """Logs a user out."""
    logout(request)
    return HttpResponseRedirect('/')

@login_required
def user_home(request):
    """A user's main profile page."""
    context = RequestContext(request)
    utype = user_type(request.user)
    return render(request, 'users/home.html', {'user_type': utype})

