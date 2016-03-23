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
    list_display = ('username', 'email', 'date_joined', 'num_sessions',
                    'num_athletes')

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
    list_display = ('pk', 'coach_email', 'name', 'start_time',
                    'num_athletes')
    exclude = ('registered_athletes',)

    def coach_email(self, obj):
        return obj.coach.user.email

    def num_athletes(self, obj):
        return obj.num_athletes


class AthleteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'team_name', 'rfid_tag', 'birth_date', 'gender')

    def team_name(self, obj):
        team = obj.team
        return team.name if team is not None else None

    def rfid_tag(self, obj):
        return obj.tag.id_str


class ReaderAdmin(admin.ModelAdmin):
    list_display = ('pk', 'id_str', 'coach_username', 'num_sessions')

    def coach_username(self, obj):
        return obj.coach.user.username

    def num_sessions(self, obj):
        return obj.timingsession_set.count()


class TeamAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'coach_email', 'num_athletes',
                    'primary_team')

    def coach_email(self, obj):
        return obj.coach.user.email

    def num_athletes(self, obj):
        return obj.athlete_set.count()


class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'id_str', 'bib', 'athlete_name')

    def athlete_name(self, obj):
        return obj.athlete.user.get_full_name()


admin.site.register(TimingSession, TimingSessionAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Coach, CoachAdmin)
admin.site.register(Athlete, AthleteAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Reader, ReaderAdmin)
