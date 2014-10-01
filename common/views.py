from django.shortcuts import render
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from models import TimingSession, Tag
from users.util import is_coach, is_athlete
from forms import TimingSessionForm, TagForm

def index(request):
    """Returns the home page for the overall site."""
    context = RequestContext(request)
    context_dict = {}
    return render(request, 'index.html', context_dict)

@login_required
def tag_manager(request):
    """The page where a user can manage their RFID tags."""
    tag_list = [t.id_str for t in Tag.objects.filter(user=request.user)]
    return render(request, 'common/managetags.html', {'tag_list': tag_list})

@login_required
def add_tag(request):
    """The form page that allows a user to add a tag to their account."""
    context = RequestContext(request)

    if request.method == 'POST':
        tag_form = TagForm(data=request.POST)

        if tag_form.is_valid():
            tag = tag_form.save(commit=False)
            #user = User.objects.get(username=request.user)
            tag.user = request.user
            tag.save()
            return HttpResponseRedirect('/common/managetags')

        else:
            print tag_form.errors

    else:
        tag_form = TagForm()

    return render(request, 'common/addtag.html', {'tag_form': tag_form})    


#@permission_required('auth.can_create_workout', login_url='/users/login/')
@login_required
def create_workout(request):
    """The form page that allows a coach to create a new workout."""
    context = RequestContext(request)

    if request.method == 'POST':
        session_form = TimingSessionForm(data=request.POST)

        if session_form.is_valid():
            #iuser = User.objects.get(username=request.user)
            session = session_form.save(commit=False)
            session.manager = request.user
            session.save()
            return HttpResponseRedirect('/users/home/')

        else:
            print session_form.errors

    else:
        session_form = TimingSessionForm()

    return render(request, 'common/createworkout.html', 
            {'session_form': session_form})    


