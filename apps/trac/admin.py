from django.contrib import admin
from trac.models import TimingSession, Tag, Coach, Athlete, Team, Reader

admin.site.register(TimingSession)
admin.site.register(Tag)
admin.site.register(Coach)
admin.site.register(Athlete)
admin.site.register(Team)
admin.site.register(Reader)
