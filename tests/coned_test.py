from datetime import datetime, timedelta, timezone
import unittest

from coned import json_to_readings
from reading import Reading

tz = timezone(timedelta(hours=-4))


class TestConed(unittest.TestCase):
    def test_json_to_readings(self):
        with open("usage.json") as f:
            j = f.read()
        got = json_to_readings(j)
        want = [
            Reading(
                datetime(2021, 8, 29, 0, 30, 0, tzinfo=tz),
                datetime(2021, 8, 29, 0, 45, 0, tzinfo=tz),
                "wh",
                110.5,
            ),
            Reading(
                datetime(2021, 8, 29, 0, 45, 0, tzinfo=tz),
                datetime(2021, 8, 29, 1, 0, 0, tzinfo=tz),
                "wh",
                121.5,
            ),
        ]
        self.assertEqual(got, want)
