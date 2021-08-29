from datetime import date, datetime

from coned import Coned
from reading import Reading
from store import BucketList

class Server:
    def __init__(self, coned: Coned):
        self._coned = coned

        # BucketList of Readings, so they will be bucketed by date string
        # BucketList{ '2021-08-30': [Reading, Reading, etc.] }
        self._list = BucketList()

    def add_reading(self, reading: Reading):
        self._list.insert(reading)

    def readings_for_date(self, day: date):
        return self._list.get_bucket(str(day))
