from reading import Reading


class OverlappingReadingError(ValueError):
    pass


class BucketList():
    """
    BucketList implements an ordered list using buckets whose keys are
    determined by the Reading's hash_bucket function. When iterating,
    BucketList yields in order of bucket key, then the ordered list in each
    bucket.
    """

    def __init__(self, *args):
        # dict to hold buckets -> ordered lists
        self._dict = {}
        # ordered list of bucket keys, for iteration
        self._keys = []

    def get_bucket(self, key: str):
        # create the bucket if it doesn't exist already
        if key not in self._dict:
            self._dict[key] = []

        return self._dict[key]

    def insert(self, reading: Reading):
        bucket = self.get_bucket(reading.hash_bucket())

        # ensure the incoming reading does not overlap with any existing ones
        for r in bucket:
            if reading.overlaps(r):
                raise OverlappingReadingError

        # incredibly lazy implementation, could insert sorted
        bucket.append(reading)
        bucket.sort(key=lambda x: x.start_time)
