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
    # For a coach, list all workout that he/she manages.
    if is_coach(request.user):
        session_list = request.user.timingsession_set.all()

    elif is_althete(request.user):
        session_list = []
        
    else:
        session_list = []
    
    return render(request, 'results/results.html', {'session_list':
        session_list})



@login_required
def workout_results(request, *args, **kwargs):
    """Displays the results of one workout for one athlete or coach."""
    session = TimingSession.objects.get(id=kwargs['wnum'])
    athlete_list = session.all_users()
    session_data = {'wid': session.id, 'wdate': session.start_time, 'athletes':
            athlete_list}
    return render(request, 'results/workoutresult.html', session_data)


