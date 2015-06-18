from django.test import TestCase
from django.utils import timezone
from trac.models import *
from trac.util import RaceReport


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

    #def test_is_active(self):
    #    ts = self.create_timingsession()
    #    ts.start_time = timezone.now()
    #    ts.stop_time = timezone.now()+timezone.timedelta(1)
    #    ts.save()
#
 #       self.assertTrue(ts.is_active)
   #     ts.start_time = ts.stop_time
   #     ts.save()
   #     self.assertFalse(ts.is_active)

    def test_results(self):
        pass

    def test_all_users(self):
        pass

class TestRaceReport(TestCase):
    """
    Test the race report class that displays compiled results.
    """

    def create_athlete(self, name, age, gender):
        """
        Create an athlete with a name, age, and gender. Also, create a tag for
        the runner.
        """
        u = User.objects.create(username=name)
        a = AthleteProfile.objects.create(user=u, age=age, gender=gender)
        t = Tag.objects.create(id_str=str(self.tag_num), user=u)
        self.tag_num = self.tag_num+1
        return a, t

    def create_final_time(self, session, tag, reader, final_time):
        """
        Assign a tag a final time in the session.
        """
        time = session.start_button_time+final_time
        tt = TagTime.objects.create(tag=tag, time=time, reader=reader, milliseconds=0)
        session.tagtimes.add(tt.pk)
        session.save()

    def setUp(self):
        """
        Create sessions, athletes, and results.
        """

        # Create the timing session.
        u = User.objects.create(username='Test Coach')
        c = CoachProfile.objects.create(user=u)
        self.ts1 = TimingSession.objects.create(name='Test', manager=u)
        self.ts1.start_button_time = timezone.now()
        self.ts2 = TimingSession.objects.create(name='Test', manager=u)
        self.ts2.start_button_time = timezone.now()

        # Create readers and add them to the session.
        r1 = Reader.objects.create(name='R1', id_str='R1', owner=u)
        r2 = Reader.objects.create(name='R2', id_str='R2', owner=u)
        self.ts1.readers.add(r1.pk)
        self.ts2.readers.add(r2.pk)
        self.ts1.save()
        self.ts2.save()

        # Create some athletes, tags, and results.
        self.tag_num = 1
        a1, t1 = self.create_athlete("Runner 1", 15, 'M')
        self.create_final_time(self.ts1, t1, r1, timezone.timedelta(seconds=140))
        a2, t2 = self.create_athlete("Runner 2", 16, 'M')
        self.create_final_time(self.ts1, t2, r1, timezone.timedelta(seconds=141))
        a3, t3 = self.create_athlete("Runner 3", 20, 'M')
        self.create_final_time(self.ts1, t3, r1, timezone.timedelta(seconds=142))
        a4, t4 = self.create_athlete("Runner 4", 22, 'M')
        self.create_final_time(self.ts1, t4, r1, timezone.timedelta(seconds=143))
        a5, t5 = self.create_athlete("Runner 5", 81, 'M')
        self.create_final_time(self.ts1, t5, r1, timezone.timedelta(seconds=144))
        a6, t6 = self.create_athlete("Runner 6", 90, 'M')
        self.create_final_time(self.ts1, t6, r1, timezone.timedelta(seconds=145))
        a7, t7 = self.create_athlete("Runner 7", 34, 'M')
        self.create_final_time(self.ts1, t7, r1, timezone.timedelta(seconds=146))
        a8, t8 = self.create_athlete("Runner 8", 16, 'M')
        self.create_final_time(self.ts1, t8, r1, timezone.timedelta(seconds=147))

        a9, t9 = self.create_athlete("Runner 9", 15, 'M')
        self.create_final_time(self.ts2, t9, r2, timezone.timedelta(seconds=148))
        a10, t10 = self.create_athlete("Runner 10", 16, 'M')
        self.create_final_time(self.ts2, t10, r2, timezone.timedelta(seconds=149))
        a11, t11 = self.create_athlete("Runner 11", 20, 'M')
        self.create_final_time(self.ts2, t11, r2, timezone.timedelta(seconds=150))
        a12, t12 = self.create_athlete("Runner 12", 22, 'M')
        self.create_final_time(self.ts2, t12, r2, timezone.timedelta(seconds=151))
        a13, t13 = self.create_athlete("Runner 13", 81, 'M')
        self.create_final_time(self.ts2, t13, r2, timezone.timedelta(seconds=152))
        a14, t14 = self.create_athlete("Runner 14", 90, 'M')
        self.create_final_time(self.ts2, t14, r2, timezone.timedelta(seconds=153))
        a15, t15 = self.create_athlete("Runner 15", 34, 'M')
        self.create_final_time(self.ts2, t15, r2, timezone.timedelta(seconds=154))
        a16, t16 = self.create_athlete("Runner 16", 16, 'M')
        self.create_final_time(self.ts2, t16, r2, timezone.timedelta(seconds=155))
        a17, t17 = self.create_athlete("Runner 17", 17, 'M')
        self.create_final_time(self.ts2, t17, r2, timezone.timedelta(seconds=156))
		
    def test_results(self):
        ids = [self.ts1.id, self.ts2.id]
        rr = RaceReport(ids)
        res = rr.get_results()

		# Put assertions here.

        #for key in res: print key

        # Set up correct race report results
        res_ans0  = {'Gender': 'M', 'Age': '0-14', 'Results': []}
        res_ans1  = {'Gender': 'F', 'Age': '0-14', 'Results': []}
        res_ans2  = {'Gender': 'M', 'Age': '15-19', 'Results': [(u'Runner 1', 140.0),(u'Runner 2', 141.0),(u'Runner 8', 147.0),(u'Runner 9', 148.0),(u'Runner 10', 149.0),(u'Runner 16', 155.0),(u'Runner 17', 156.0)]}
        res_ans3  = {'Gender': 'F', 'Age': '15-19', 'Results': []}
        res_ans4  = {'Gender': 'M', 'Age': '20-24', 'Results': [(u'Runner 3', 142.0),(u'Runner 4', 143.0),(u'Runner 11', 150.0),(u'Runner 12', 151.0)]}
        res_ans5  = {'Gender': 'F', 'Age': '20-24', 'Results': []}
        res_ans6  = {'Gender': 'M', 'Age': '25-29', 'Results': []}
        res_ans7  = {'Gender': 'F', 'Age': '25-29', 'Results': []}
        res_ans8  = {'Gender': 'M', 'Age': '30-34', 'Results': [(u'Runner 7', 146.0),(u'Runner 15', 154.0),]}
        res_ans9  = {'Gender': 'F', 'Age': '30-34', 'Results': []}
        res_ans10 = {'Gender': 'M', 'Age': '35-39', 'Results': []}
        res_ans11 = {'Gender': 'F', 'Age': '35-39', 'Results': []}
        res_ans12 = {'Gender': 'M', 'Age': '40-44', 'Results': []}
        res_ans13 = {'Gender': 'F', 'Age': '40-44', 'Results': []}
        res_ans14 = {'Gender': 'M', 'Age': '45-49', 'Results': []}
        res_ans15 = {'Gender': 'F', 'Age': '45-49', 'Results': []}
        res_ans16 = {'Gender': 'M', 'Age': '50-54', 'Results': []}
        res_ans17 = {'Gender': 'F', 'Age': '50-54', 'Results': []}
        res_ans18 = {'Gender': 'M', 'Age': '55-59', 'Results': []}
        res_ans19 = {'Gender': 'F', 'Age': '55-59', 'Results': []}
        res_ans20 = {'Gender': 'M', 'Age': '60-64', 'Results': []}
        res_ans21 = {'Gender': 'F', 'Age': '60-64', 'Results': []}
        res_ans22 = {'Gender': 'M', 'Age': '65-69', 'Results': []}
        res_ans23 = {'Gender': 'F', 'Age': '65-69', 'Results': []}
        res_ans24 = {'Gender': 'M', 'Age': '70-74', 'Results': []}
        res_ans25 = {'Gender': 'F', 'Age': '70-74', 'Results': []}
        res_ans26 = {'Gender': 'M', 'Age': '75-79', 'Results': []}
        res_ans27 = {'Gender': 'F', 'Age': '75-79', 'Results': []}
        res_ans28 = {'Gender': 'M', 'Age': '80-120', 'Results': [(u'Runner 5', 144.0),(u'Runner 6', 145.0),(u'Runner 13', 152.0),(u'Runner 14', 153.0)]}
        res_ans29 = {'Gender': 'F', 'Age': '80-120', 'Results': []}

        # Test assertions
        self.assertEqual(res[ 0] , res_ans0) 
        self.assertEqual(res[ 1] , res_ans1) 
        self.assertEqual(res[ 2] , res_ans2) 
        self.assertEqual(res[ 3] , res_ans3)
        self.assertEqual(res[ 4] , res_ans4)
        self.assertEqual(res[ 5] , res_ans5)
        self.assertEqual(res[ 6] , res_ans6)
        self.assertEqual(res[ 7] , res_ans7)
        self.assertEqual(res[ 8] , res_ans8)
        self.assertEqual(res[ 9] , res_ans9)
        self.assertEqual(res[10] , res_ans10)
        self.assertEqual(res[11] , res_ans11)
        self.assertEqual(res[12] , res_ans12)
        self.assertEqual(res[13] , res_ans13)
        self.assertEqual(res[14] , res_ans14)
        self.assertEqual(res[15] , res_ans15)
        self.assertEqual(res[16] , res_ans16)
        self.assertEqual(res[17] , res_ans17)
        self.assertEqual(res[18] , res_ans18)
        self.assertEqual(res[19] , res_ans19)
        self.assertEqual(res[20] , res_ans20)
        self.assertEqual(res[21] , res_ans21)
        self.assertEqual(res[22] , res_ans22)
        self.assertEqual(res[23] , res_ans23)
        self.assertEqual(res[24] , res_ans24)
        self.assertEqual(res[25] , res_ans25)
        self.assertEqual(res[26] , res_ans26)
        self.assertEqual(res[27] , res_ans27)
        self.assertEqual(res[28] , res_ans28)
        self.assertEqual(res[29] , res_ans29)

