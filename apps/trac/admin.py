from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from trac.models import TimingSession, Tag, Coach, Athlete, Team, Reader


class CoachAdmin(admin.ModelAdmin):
    fields = (
        'username', 'email', 'date_joined', 'teams', 'num_athletes',
        'num_sessions', 'payment_info'
    )
    readonly_fields = (
        'username', 'email', 'date_joined', 'teams', 'num_athletes',
        'num_sessions', 'payment_info'
    )
    list_display = ('username', 'email', 'date_joined')

    def username(self, obj):
        return obj.user.username

    def email(self, obj):
        return obj.user.email

    def date_joined(self, obj):
        return obj.user.date_joined

    def teams(self, obj):
        return obj.team_set.values_list('name', flat=True)

    def num_athletes(self, obj):
        """Number of athletes registered to this coach."""
        return Athlete.objects.filter(team__coach=obj).count()

    def num_sessions(self, obj):
        """Number of sessions created by this coach."""
        return TimingSession.objects.filter(coach=obj).count()

    def payment_info(self, obj):
        """Whether the coach has registered payment info."""
        try:
            obj.user.customer
            return True
        except ObjectDoesNotExist:
            return False


class TimingSessionAdmin(admin.ModelAdmin):
    exclude = ('registered_athletes',)


admin.site.register(TimingSession, TimingSessionAdmin)
admin.site.register(Tag)
admin.site.register(Coach, CoachAdmin)
admin.site.register(Athlete)
admin.site.register(Team)
admin.site.register(Reader)
