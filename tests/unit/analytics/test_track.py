from lbrynet import analytics

from twisted.trial import unittest


class TrackTest(unittest.TestCase):
    def test_empty_summarize_is_None(self):
        track = analytics.Track()
        _, result = track.summarize('a')
        self.assertEqual(None, result)

    def test_can_get_sum_of_metric(self):
        track = analytics.Track()
        track.add_observation('b', 1)
        track.add_observation('b', 2)

        _, result = track.summarize('b')
        self.assertEqual(3, result)

    def test_summarize_resets_metric(self):
        track = analytics.Track()
        track.add_observation('metric', 1)
        track.add_observation('metric', 2)

        track.summarize('metric')
        _, result = track.summarize('metric')
        self.assertEqual(None, result)
