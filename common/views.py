from django.shortcuts import render
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from models import TimingSession, Tag, Reader
from users.util import is_coach, is_athlete
from forms import TimingSessionForm, TagForm, ReaderForm

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
            tag.user = request.user
            tag.save()
            return HttpResponseRedirect('/common/managetags')

        else:
            print tag_form.errors

    else:
        tag_form = TagForm()

    return render(request, 'common/addtag.html', {'tag_form': tag_form})    

@login_required
def add_reader(request):
    """The form that allows a coach to register a reader to their account."""
    # TODO: only allow coaches to use this feature.

    context = RequestContext(request)

    if request.method == 'POST':
        reader_form = ReaderForm(data=request.POST)

        if reader_form.is_valid():
            reader = reader_form.save(commit=False)
            reader.owner = request.user
            reader.save()
            return HttpResponseRedirect('/common/managereaders')

        else:
            print reader_form.errors

    else:
        reader_form = ReaderForm()

    return render(request, 'common/addreader.html', {'reader_form': reader_form})    

@login_required
def reader_manager(request):
    """The page where a user can manage their RFID readers."""
    reader_list = [r.id_str for r in Reader.objects.filter(owner=request.user)]
    return render(request, 'common/managereaders.html', {'reader_list': reader_list})

#@permission_required('auth.can_create_workout', login_url='/users/login/')
@login_required
def create_workout(request):
    """The form page that allows a coach to create a new workout."""
    context = RequestContext(request)

    if request.method == 'POST':
        session_form = TimingSessionForm(request.user, data=request.POST)

        if session_form.is_valid():
            session = session_form.save(commit=False)
            session.manager = request.user
            session.save()
            return HttpResponseRedirect('/users/home/')

        else:
            print session_form.errors

    else:
        session_form = TimingSessionForm(request.user)

    return render(request, 'common/createworkout.html', 
            {'session_form': session_form})    


