from django.test import TestCase
from django.utils import timezone
from trac.models import *


class ReaderTest(TestCase):

    def create_reader(self, user_name="Test User", reader_name="Alien", 
                      reader_str="A123"):
        user = User.objects.create(username=user_name)
        return Reader.objects.create(name=reader_name, id_str=reader_str, owner=user)

    def create_session(self, coach_name, start_time, stop_time):
        user, created = User.objects.get_or_create(username=coach_name)
        return TimingSession.objects.create(start_time=start_time,
                                            stop_time=stop_time,
                                            manager=user)

    def test_reader_creation(self):
        r = self.create_reader()
        self.assertTrue(isinstance(r, Reader))
        self.assertEqual(r.__unicode__(), r.name)

    def test_active_sessions(self):
        start = timezone.now()
        inactive_stop = timezone.now()+timezone.timedelta(-1)
        active_stop = timezone.now()+timezone.timedelta(1)
        
        r = self.create_reader("T")
        inactive_session = self.create_session('Coach1', start, inactive_stop)
        active_session = self.create_session('Coach2', start, active_stop)
        inactive_session.readers.add(r)
        active_session.readers.add(r)

        self.assertIn(active_session, r.active_sessions)
        self.assertNotIn(inactive_session, r.active_sessions)

class TagTimeTest(TestCase):

    def create_tagtime(self, username):
        athlete = User.objects.create(username=username)
        coach = User.objects.create(username='Coach')
        tag = Tag.objects.create(id_str='A128 12G4', user=athlete)
        reader = Reader.objects.create(id_str='A102', owner=coach)
        return TagTime.objects.create(tag=tag, time=timezone.now(),
                reader=reader, milliseconds=145)

    def test_tagtime_creation(self):
        tt = self.create_tagtime('Test Athlete')
        self.assertTrue(isinstance(tt, TagTime))

    def test_unique_times(self):
        pass

    def test_owner_name(self):
        tt = self.create_tagtime('mo')
        self.assertTrue(tt.owner_name == '')
        tt.tag.user.first_name = 'Mo'
        tt.tag.user.last_name = 'Farah'
        self.assertTrue(tt.owner_name == 'Mo Farah')

class TimingSessionTest(TestCase):

    def create_timingsession(self):
        u = User.objects.create(username='Test Coach')
        c = CoachProfile.objects.create(user=u)
        return TimingSession.objects.create(name='Test Session', manager=u)

    def create_tagtime(self, username='A1', time=timezone.now(), tagid='0001'):
        u = User.objects.get_or_create(username=username)
        a = AthleteProfile.objects.get_or_create(user=u)
        return tagtime.objects.create(user=u, id_str=tagid)
        
    def test_timingsession_creation(self):
        ts = self.create_timingsession() 
        self.assertIsInstance(ts, TimingSession)

    def test_is_active(self):
        ts = self.create_timingsession()
        ts.start_time = timezone.now()
        ts.stop_time = timezone.now()+timezone.timedelta(1)
        ts.save()

        self.assertTrue(ts.is_active)
        ts.start_time = ts.stop_time
        ts.save()
        self.assertFalse(ts.is_active)

    def test_results(self):
        pass

    def test_all_users(self):
        pass

