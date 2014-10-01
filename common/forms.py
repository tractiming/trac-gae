from django.contrib.auth.models import User
from models import Tag, Reader, TimingSession
from django import forms

class TimingSessionForm(forms.ModelForm):
    name = forms.CharField()

    class Meta:
        model = TimingSession
        fields = ('name', 'start_time', 'stop_time',)
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

