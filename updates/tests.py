from django.test import TestCase
from update.models import Split, Tag, Workout, Reader
import datetime

# Create your tests here.

class WorkoutDataTestCase(TestCase):
    #fixtures = ['update_views_testdata.json']
    
    def build_test(self):
        u = User.objects.create(first_name='Elliot', last_name='Hevel', 
                                username='ehevel', password='password')
        t = Tag.objects.create(id_str='11C5 0A1C', user=u.pk)
        r = Reader.objects.create(num=1)
        w = Workout.objects.create(num=1, start_time=, stop_time=)
        r.workouts.add(w)
        s = Split.objects.create()

    def test_json_response(self):
        test_wkt_id = 1
        resp = self.client.get('/update/', {'w_id': test_wkt_id})
        self.assertEqual(resp.status_code, 200)
        print resp.content
