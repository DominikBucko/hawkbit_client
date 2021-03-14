class ObjectView(object):
    def __init__(self, d):
        self.__dict__ = d


def parse_time_to_seconds(t):
    hours = int(t[0:2])
    mins = int(t[3:5])
    sec = int(t[6:])

    return hours * 360 + mins * 60 + sec
