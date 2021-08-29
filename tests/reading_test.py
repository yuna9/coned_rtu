from datetime import datetime, timedelta, timezone
import unittest

from reading import Reading


class TestReading(unittest.TestCase):
    def setUp(self):
        self.sometime = datetime(2010, 12, 25, 14, 30, 0, tzinfo=timezone.utc)
        self.later = datetime(2010, 12, 26, 14, 30, 0, tzinfo=timezone.utc)

    def test_start_time_must_be_before_end_time(self):
        # start and end time the same
        with self.assertRaises(ValueError):
            Reading(self.sometime, self.sometime, "wh", 1)

        # start time after end time
        with self.assertRaises(ValueError):
            Reading(self.later, self.sometime, "wh", 1)

    def test_enforces_units(self):
        # only wh or kwh supported
        with self.assertRaises(ValueError):
            Reading(self.sometime, self.later, "mwh", 1)

        # incorrect capitalization is okay
        Reading(self.sometime, self.later, "Wh", 1)

    def test_duration(self):
        r = Reading(self.sometime, self.later, "wh", 1)
        self.assertEqual(r.duration(), timedelta(hours=24))

    def test_overlaps(self):
        t1 = self.sometime
        t2 = t1 + timedelta(hours=1)
        t3 = t2 + timedelta(hours=1)
        t4 = t3 + timedelta(hours=1)

        # one within the other
        a = Reading(t1, t4, "wh", 1)
        b = Reading(t2, t3, "wh", 1)
        self.assertTrue(a.overlaps(b))
        self.assertTrue(b.overlaps(a))

        # one ends during the other
        a = Reading(t1, t3, "wh", 1)
        b = Reading(t2, t4, "wh", 1)
        self.assertTrue(a.overlaps(b))
        self.assertTrue(b.overlaps(a))

        # same start, one is shorter than the other
        a = Reading(t1, t3, "wh", 1)
        b = Reading(t1, t2, "wh", 1)
        self.assertTrue(a.overlaps(b))
        self.assertTrue(b.overlaps(a))

        # same end, one is shorter than the other
        a = Reading(t1, t3, "wh", 1)
        b = Reading(t2, t3, "wh", 1)
        self.assertTrue(a.overlaps(b))
        self.assertTrue(b.overlaps(a))

        # not overlapping
        a = Reading(t1, t2, "wh", 1)
        b = Reading(t2, t3, "wh", 1)
        self.assertFalse(a.overlaps(b))
        self.assertFalse(b.overlaps(a))

    def test_hash_bucket(self):
        a = Reading(self.sometime, self.later, "wh", 1)
        b = Reading(self.sometime, self.later, "wh", 2)
        c = Reading(
            self.sometime + timedelta(hours=24),
            self.later + timedelta(hours=24),
            "wh",
            1,
        )
        self.assertEqual(a.hash_bucket(), b.hash_bucket())
        self.assertNotEqual(a.hash_bucket(), c.hash_bucket())

    def test_equality(self):
        r = Reading(self.sometime, self.later, "wh", 1)

        # times mismatch
        bad_time = self.sometime + timedelta(seconds=10)

        other = Reading(bad_time, self.later, "wh", 1)
        self.assertNotEqual(r, other)

        other = Reading(self.sometime, bad_time, "wh", 1)
        self.assertNotEqual(r, other)

        # energy mismatch
        other = Reading(self.sometime, self.later, "wh", 1.0000001)
        self.assertNotEqual(r, other)

        # fully equal
        other = Reading(self.sometime, self.later, "wh", 1)
        self.assertEqual(r, other)

    def test_hashing(self):
        # unequal
        a = Reading(self.sometime, self.later, "wh", 1)
        b = Reading(self.sometime, self.later, "wh", 2)
        self.assertNotEqual(hash(a), hash(b))

        # equal
        b = Reading(self.sometime, self.later, "wh", 1)
        self.assertEqual(hash(a), hash(b))
