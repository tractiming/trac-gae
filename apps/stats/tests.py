from django.test import TestCase

from stats.vo2 import calc_vo2, predict_from_vo2


class StatsTest(TestCase):

    def setUp(self):
        self.benchmarks = [
            ((5000, (13*60 + 35)), 78),
            ((1500, (4*60 + 0)), 70),
            ((3000, (8*60 + 45)), 68)
        ]

    def test_vo2_max(self):
        """Test calculating vo2 max."""
        for result, vo2 in self.benchmarks:
            self.assertEqual(int(calc_vo2(*result)), vo2)

    def test_predict_from_vo2(self):
        """Test predicting performance based on VO2 max."""
        for result, _ in self.benchmarks:
            vo2 = calc_vo2(*result)
            # Check the prediction is within 2 decimal places
            self.assertAlmostEqual(
                predict_from_vo2(vo2, result[0]), result[1],
                places=2)
