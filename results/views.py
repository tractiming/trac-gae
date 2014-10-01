from django.shortcuts import render
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from common.models import TimingSession
from users.util import is_coach, is_athlete

@login_required
def results_home(request):
    """The user's home page for viewing all of his past workout results."""
    #user = User.objects.get(username=request.user) 
    
    # If the user is a coach, display the workouts he/she owns.
    #if is_coach(request.user):
    #    workout_list = [w.id for w in user.workout_set.all()] 

    # If the user is an athlete, list all the workouts he/she has contributed
    # splits to.
    #elif is_athlete(request.user):
    #    workout_list = [w.id for w in Workout.objects.all() if user in w.all_users()]

    #else:
    #    workout_list = []
    workout_list = []
    
    return render(request, 'results/results.html', {'workout_list':
        workout_list})



@login_required
def workout_results(request, *args, **kwargs):
    """Displays the results of one workout for one athlete or coach."""
    workout = Workout.objects.get(id=kwargs['wnum'])
    athlete_list = workout.all_users()
    workout_data = {'wid': workout.id, 'wdate': workout.start_time, 'athletes':
            athlete_list}
    return render(request, 'results/workoutresult.html', workout_data)


