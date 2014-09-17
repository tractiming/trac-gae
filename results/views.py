from django.shortcuts import render
from django.template import RequestContext
from results.forms import WorkoutForm, TagForm
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from common.models import Workout
from users.util import is_coach, is_athlete

@login_required
def results_home(request):
    """The user's home page for viewing all of his past workout results."""
    user = User.objects.get(username=request.user) 
    
    # If the user is a coach, display the workouts he/she owns.
    if is_coach(request.user):
        workout_list = [w.id for w in user.workout_set.all()] 

    # If the user is an athlete, list all the workouts he/she has contributed
    # splits to.
    elif is_athlete(request.user):
        workout_list = [w.id for w in Workout.objects.all() if user in w.all_users()]

    else:
        workout_list = []
    
    return render(request, 'results/results.html', {'workout_list':
        workout_list})

@permission_required('auth.can_create_workout', login_url='/users/login/')
def create_workout(request):
    """The form page that allows a coach to create a new workout."""
    context = RequestContext(request)

    if request.method == 'POST':
        workout_form = WorkoutForm(data=request.POST)

        if workout_form.is_valid():
            user = User.objects.get(username=request.user)
            workout = workout_form.save(commit=False)
            workout.owner_id = user.id
            workout.save()
            return HttpResponseRedirect('/results/')

        else:
            print workout_form.errors

    else:
        workout_form = WorkoutForm()

    return render(request, 'results/createworkout.html', {'workout_form': workout_form})    
def add_tag(request):
    """The form page that allows a user to add a tag to their account."""
    context = RequestContext(request)

    if request.method == 'POST':
        tag_form = TagForm(data=request.POST)

        if tag_form.is_valid():
            user = User.objects.get(username=request.user)
            tag = tag_form.save(commit=False)
            tag.owner_id = user.id
            tag.save()
            return HttpResponseRedirect('results_home')

        else:
            print tag_form.errors

    else:
        tag_form = TagForm()

    return render(request, 'add_tag', {'tag_form': tag_form})    



@login_required
def workout_results(request, *args, **kwargs):
    """Displays the results of one workout for one athlete or coach."""
    workout = Workout.objects.get(id=kwargs['wnum'])
    athlete_list = workout.all_users()
    workout_data = {'wid': workout.id, 'wdate': workout.start_time, 'athletes':
            athlete_list}
    return render(request, 'results/workoutresult.html', workout_data)


