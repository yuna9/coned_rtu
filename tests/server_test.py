from datetime import datetime, timezone
import unittest

from coned_rtu import Reading, Server


class TestServer(unittest.TestCase):
    def setUp(self):
        self.sometime = datetime(2010, 12, 25, 14, 30, 0, tzinfo=timezone.utc)
        self.later = datetime(2010, 12, 26, 14, 30, 0, tzinfo=timezone.utc)

    def test(self):
        s = Server(None)

        r = Reading(self.sometime, self.later, "wh", 1)
        s.add_reading(r)

        got = s.readings_for_date(r.start_time.date())
        self.assertEqual(got, [r])
