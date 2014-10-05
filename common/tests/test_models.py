from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from common.models import TimingSession, Tag, Reader, TagTime


class ReaderTest(TestCase):

    def create_reader(self, *args, **kwargs):
        user = User.objects.create(username='Test User')
        return Reader.objects.create(name='Alien Reader', id_str='A101',
                owner=user)

    def create_session(self, coach_name, start_time, stop_time):
        user = User.objects.create(username=coach_name)
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
        
        r = self.create_reader()
        inactive_session = self.create_session('Coach1', start, inactive_stop)
        active_session = self.create_session('Coach2', start, active_stop)
        inactive_session.readers.add(r)
        active_session.readers.add(r)

        assert active_session in r.active_sessions
        assert inactive_session not in r.active_sessions

class TagTimeTest(TestCase):

    def create_tagtime(self, username):
        athlete = User.objects.create(username=username)
        coach = User.objects.create(username='Coach')
        tag = Tag.objects.create(id_str='A128 12G4', user=athlete)
        reader = Reader.objects.create(id_str='A102', owner=coach)
        return TagTime.objects.create(tag=tag, time=timezone.now(), reader=reader)

    def test_tagtime_creation(self):
        tt = self.create_tagtime('Test Athlete')
        self.assertTrue(isinstance(tt, TagTime))

    def test_unique_times(self):
        pass

    def test_owner_name(self):
        tt = self.create_tagtime('mo')
        self.assertTrue(tt.owner_name == 'Unknown')
        tt.tag.user.first_name = 'Mo'
        tt.tag.user.last_name = 'Farah'
        self.assertTrue(tt.owner_name == 'Mo Farah')

class TimingSessionTest(TestCase):

    def create_timingsession(self):
        athlete1 = User.objects.create(username='a1')
        athlete2 = User.objects.create(username='a2')
        athlete3 = User.objects.create(username='a3')

        tag1 = Tag.objects.create(user=athlete1, id_str='T001')
        tag2 = Tag.objects.create(user=athlete2, id_str='T002')
        tag3 = Tag.objects.create(user=athlete3, id_str='T003')

        time1 = timezone.now()+timezone.timedelta(0,1,1)
        time2 = timezone.now()+timezone.timedelta(0,1,2)
        time3 = timezone.now()+timezone.timedelta(0,1,3)

        coach = User.objects.create(username='bhudson')
        ts = TimingSession()
        ts. manager = coach
        ts.name = 'Mile Repeats'
        ts.start_time = timezone.now()
        ts.stop_time = timezone.now()+timezone.timedelta(1)
        
    def test_timingsession_creation(self):
        pass

    def test_is_active(self):
        pass

    def test_results(self):
        pass

    def test_all_users(self):
        pass

