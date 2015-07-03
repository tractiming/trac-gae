
'''
    def get_final_results(self, user=None, force_update=False):
        """Gets the current splits for the session."""
        
        wdata = cache.get(('ts_%i_results' %self.id))

        if not wdata:
            name_array = []
            time_array=[]
            school = []
            q_objects=Q()
            
            #Filter by gender, age, grade. Note that age and grade are json arrays
            #TODO: Filter by team
            			
            if self.age_scoring:
			    for age in self.age_scoring:
				    q_objects |= Q(tag__user__athlete__age=age)
			
            if self.grade_scoring:
			    for grade in self.grade_scoring:
				    q_objects |= Q(tag__user__athlete__grade=grade)
		    
            if self.gender_scoring:
				q_objects &= Q(tag__user__athlete__gender=self.gender_scoring)
			
				
            tag_ids = self.tagtimes.filter(q_objects).values_list('tag_id',flat=True).distinct()
            for tag_id in tag_ids:

                # Get the name of the tag's owner.
                tag = Tag.objects.get(id=tag_id)
                user = tag.user
                if user:
                    name = user.get_full_name()
                    if not name:
                        name = user.username
                else:
                    name = str(tag_id)
                
                try:
                    team = user.groups.values_list('name',flat=True)[0]
                except:
                    team = None
                
                # Calculate the splits for this tag in the current workout.
                times = TagTime.objects.filter(timingsession=self, 
                                               tag=tag).order_by('time')
                
                interval = []
                scoring_time = []
                for i in range(len(times)-1):
                    t1 = times[i].time+timezone.timedelta(
                            milliseconds=times[i].milliseconds)
                    t2 = times[i+1].time+timezone.timedelta(
                            milliseconds=times[i+1].milliseconds)
                    dt = t2-t1

                    # Convert the number to a string to prevent round-off error.
                    str_dt = str(round(dt.total_seconds(), 3))
                    interval.append([str_dt])
                    scoring_time.append(round(dt.total_seconds(), 3))

                counter = range(1,len(interval)+1)   

                # Filtering algorithm.
                if self.filter_choice:
                    interval, counter = filter_splits(interval, 
                                                      self.interval_distance,
                                                      self.track_size)

                # Add the runner's data to the workout. 
                #Insure that scoring_time[-1] is the same array length if reader misses runner

                name_array.append(name)
                time_array.append(scoring_time[-1])
                school.append(team)
        
        #TODO: Better JSON Sorted by time?
        self.participating_schools = set(school)   
        #sort arrays by fastest time, print name and time in order
        sorted_results = [sorted(zip(time_array,name_array,school))]
        self.sorted_results = sorted_results
        return (sorted_results)
    def get_results_old(self, force_update=False):
        """
        Gets the current splits for the session. The force_update argument
        ensures splits are recalculated and not read from cache.
        """
        wdata = cache.get(('ts_%i_results' %self.id))

        if (not wdata) or (force_update):
            wdata = {}
            wdata['date'] = self.start_time.strftime('%m.%d.%Y')
            wdata['workoutID'] = self.id
            wdata['runners'] = []

            tag_ids = self.tagtimes.values_list('tag_id',flat=True).distinct()
            for tag_id in tag_ids:

                # Get the name of the tag's owner.
                tag = Tag.objects.get(id=tag_id)
                user = tag.user
                if user:
                    name = user.get_full_name()
                    if not name:
                        name = user.username
                else:
                    name = str(tag_id)

                # Calculate the splits for this tag in the current workout.
                times = TagTime.objects.filter(timingsession=self, 
                                               tag=tag).order_by('time')
                if self.start_button_time.year > 1:
                    s_tt = TagTime(time=self.start_button_time, milliseconds=0)
                    times = [s_tt]+list(times)
                
                interval = []
                for i in range(len(times)-1):
                    t1 = times[i].time+timezone.timedelta(
                            milliseconds=times[i].milliseconds)
                    t2 = times[i+1].time+timezone.timedelta(
                            milliseconds=times[i+1].milliseconds)
                    dt = t2-t1

                    # Convert the number to a string to prevent round-off error.
                    str_dt = str(round(dt.total_seconds(), 3))
                    interval.append([str_dt])

                counter = range(1,len(interval)+1)   

                # Filtering algorithm.
                if self.filter_choice:
                    interval, counter = filter_splits(interval, 
                                                      self.interval_distance,
                                                      self.track_size)

                # Add the runner's data to the workout. 
                wdata['runners'].append({'name': name, 'counter': counter,
                             'interval': interval})

            cache.set(('ts_%i_results' %self.id), wdata)    

        return wdata    
'''

'''
from django.contrib.auth.models import User
from models import Tag, Reader, TimingSession
from django import forms

class TimingSessionForm(forms.ModelForm):
    name = forms.CharField()
    comment = forms.CharField()
    rest_time = forms.IntegerField()
    track_size = forms.IntegerField()
    interval_distance= forms.IntegerField()
    interval_number = forms.IntegerField()
    
    def __init__(self, user, *args, **kwargs):
        super(TimingSessionForm, self).__init__(*args, **kwargs)
        self.fields['readers'] = forms.ModelMultipleChoiceField(
                queryset=Reader.objects.filter(owner=user))

    class Meta:
        model = TimingSession
        fields = ('name', 'start_time', 'stop_time','comment','rest_time','track_size','interval_distance','interval_number','filter_choice','readers', )
        widgets = {'start_time': forms.widgets.DateTimeInput(), 
                   'stop_time': forms.widgets.DateTimeInput()}

class ReaderForm(forms.ModelForm):
    """Form for registering a reader to a user."""

    class Meta:
        model = Reader
        fields = ('id_str', 'name',)

class TagForm(forms.ModelForm):
    """Form for registering an RFID tag."""

    class Meta:
        model = Tag
        fields = ('id_str',)
'''
'''
class RaceReport:
    """A summary of a race's results."""

    age_brackets = [(0,17), (18, 21), (22, 30), (31, 40), (41, 50)]
    results = {}

    def __init__(self, session_id):
        self.ts = TimingSession.objects.get(id=session_id)
        self.results = {}
        pass

    def get_results(self):
        pass

    def write_csv(self):
        pass





############# old stuff ######################################
#def parse_raw_msg(string):
#    """
#    DEPRECATED
#    Extracts split data from reader notification message.
#    """
#    # Check that tag contains good information.
#    if ('Tag:' not in string) or ('Last:' not in string) or ('Ant:' not in string):
#        return None
#
#    msg_info = {}
#    for d in string.split(', '):
#        k = d.split(':')
#        
#        if k[0] == 'Tag':
#            msg_info['name'] = k[1]
#        elif k[0] == 'Last':
#            time_str = d[5:]
#            msg_info['time'] = datetime.datetime.strptime(time_str,
#                                                          "%Y/%m/%d %H:%M:%S.%f") 
#        elif k[0] == 'Ant':
#            msg_info['Ant'] = int(k[1])
#
#    return msg_info
#
#def parse_formatted_msg(msg):
#    """
#    DEPRECATED
#    Extracts time data from a formatted reader message.
#    """
#    # Ensure that the message contains valid info.
#    for token in ['ant', 'r', 'id', 'time']:
#        if token not in msg:
#            return None
#    
#    msg_info = {'name': msg['ant']}
'''
'''
from django.shortcuts import render
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from models import TimingSession, Tag, Reader
from util import is_coach, is_athlete
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

    def get_score(self):
		"""
		Calculate score from data fed from get_final_results
		"""
		scored_array=[]
		schools = []
		scoring_runners=[]
		score_breakdown=[]
		score=[]
		#compare registered schools to schools of runners
		for t in self.participating_schools:
			count=0
			points = 0
			r = 0
			team_scorers=[]
			team_score_breakdown=[]
			while r<len(self.sorted_results[0]) and count < self.number_scoring: #change to scoring_runners
				
				if(self.sorted_results[0][r][2] == t):
				    count = count + 1
				    points = points + r + 1
				    team_scorers.append(self.sorted_results[0][r][1])
				    team_score_breakdown.append(r+1)
				r = r + 1
			#compare team to scoring standard, if less than standard set to null	
			if count < self.number_scoring:#change to scoring_runners
				points= None
			
            # if we need individual arrays,or json format will need to redo and
            # order json
			score_breakdown.append(team_score_breakdown)	
			scoring_runners.append(team_scorers)
			scored_array.append(points)
			schools.append(t)
            #score.append({'team': team_score_breakdown, 'team scoreres':
            #team_scorers, 'points': points,'school':t})
			
		zipped_scores = [sorted(zip(scored_array,schools,scoring_runners,score_breakdown))]
		return zipped_scores

'''
