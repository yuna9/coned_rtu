from datetime import date

from coned import Coned, json_to_readings
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

    def record_usage(self):
        self._coned.login()
        usage_json = self._coned.get_usage()
        readings = json_to_readings(usage_json)
        for r in readings:
            self._list.insert(r)

    def print_readings(self):
        for r in self._list.to_list():
            print(f"Start: {r.start_time}\tDuration: {r.duration()}\tWh: {r.wh}")
