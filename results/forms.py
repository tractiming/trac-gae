from django.contrib.auth.models import User
#from results.models import WorkoutLog
from common.models import Workout, Reader, Tag
from django import forms

class WorkoutForm(forms.ModelForm):
    name = forms.CharField()

    class Meta:
        model = Workout
        fields = ('name', 'start_time', 'stop_time')
        widgets = {'start_time': forms.widgets.DateTimeInput(), 
                   'stop_time': forms.widgets.DateTimeInput()}

class ReaderForm(forms.ModelForm):
    """Form for registering a reader to a user."""

    class Meta:
        model = Reader
        fields = ('num', 'key')

class TagForm(forms.ModelForm):
    """Form for registering an RFID tag."""

    class Meta:
        model = Tag
        fields = ('id_str',)

