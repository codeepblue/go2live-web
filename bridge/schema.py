from time import time


class Event(object):
    def __init__(self, form={}):
        for key in form:
            setattr(self, key, form.get(key))
        self.timestamp = int(time())

    @property
    def stream_key(self):
        return self.name
