from datetime import datetime, timedelta, timezone
import unittest

from reading import Reading
from store import BucketList, OverlappingReadingError


class TestStore(unittest.TestCase):
    def setUp(self):
        self.sometime = datetime(2010, 12, 25, 14, 30, 0, tzinfo=timezone.utc)
        self.later = datetime(2010, 12, 26, 14, 30, 0, tzinfo=timezone.utc)
        self.hour = timedelta(hours=1)

    def test(self):
        bl = BucketList()
        t1 = self.sometime
        t2 = t1 + self.hour
        t3 = t2 + self.hour

        b = Reading(t2, t3, "wh", 1)
        bl.insert(b)

        a = Reading(t1, t2, "wh", 1)
        bl.insert(a)

        # inserting an overlapping reading is an error
        bad = Reading(t2, t2 + timedelta(minutes=30), "wh", 1)
        with self.assertRaises(OverlappingReadingError):
            bl.insert(bad)

        # inserted readings are sorted
        got = bl.get_bucket(a.hash_bucket())
        want = [a, b]
        self.assertEqual(got, want)

    def test_get_bucket_makes_bucket_if_not_exist(self):
        bl = BucketList()
        day = "2021-08-30"
        _ = bl.get_bucket(day)
        self.assertEqual(len(bl._dict), 1)
        self.assertEqual(list(bl._dict.keys())[0], day)
