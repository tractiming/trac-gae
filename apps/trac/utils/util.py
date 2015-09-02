from django.utils import timezone
#from trac.models import TimingSession

def is_athlete(user):
    """
    Returns True if the user is an athlete, False otherwise.
    """
    try:
        user.athlete
        return True
    except:
        return False

def is_coach(user):
    """
    Returns True if the user is a coach, False otherwise.
    """
    try:
        user.coach
        return True
    except:
        return False

def user_type(user):
    """
    Gives the type of user: coach, athlete, or generic user.
    """
    if is_athlete(user):
        return 'athlete'
    elif is_coach(user):
        return 'coach'
    else:
        return 'user'

'''
class RaceReport(object):
    """
    A summary of a race's results.
    """
    age_brackets = [( 0, 14), (15, 19), (20, 24), (25, 29), (30, 34), (35, 39),
                    (40, 44), (45, 49), (50, 54), (55, 59), (60, 64), (65, 69), 
                    (70, 74), (75, 79), (80, 120)]
    genders = ('M', 'F')
    results = {}

    def __init__(self, session_ids):
        """
        This method should be called with a list of session ids. The results
        will be aggregated across all of these sessions.
        """
        assert isinstance(session_ids, list)
        self.sessions = TimingSession.objects.filter(id__in=session_ids)
        self.results = None

    def get_results(self, recalc=True):
        """
        Calculate the full results by age groups/gender. Returns a list of
        dictionaries, each of which is the result for a different group.
        """
        if (not recalc) and (self.results is not None):
            return self.results

        self.results = []

        # Loop through all possible combinations of ages and genders.
        for age in self.age_brackets:
            for gender in self.genders:

                single_result = {}
                single_result['Age'] = "%i-%i" %age
                single_result['Gender'] = "%s" %gender

                # Get the filtered results from each session. The filtered
                # results return only those results matching our criteria.
                r = []
                for session in self.sessions:
                    rs = session.get_filtered_results(gender=gender,
                                                      age_range=age)
                    for ri in rs:
                        r.append((ri[1], ri[-1]))

                # Sort the results from all sessions by cumulative time.
                sr = sorted(r, key=lambda x: x[1])
                single_result['Results'] = sr

                self.results.append(single_result)

        return self.results

    def write_csv(self):
        """
        Write a csv file  with the results.
        """
        raise NotImplementedError
'''
