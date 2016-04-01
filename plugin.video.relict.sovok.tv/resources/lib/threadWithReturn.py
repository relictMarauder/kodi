#!/usr/bin/python
from threading import Thread


class ThreadWithReturn(Thread):
    def __init__(self, *args, **kwargs):
        super(ThreadWithReturn, self).__init__(*args, **kwargs)

        self._return = None

    def run(self):
        if self._Thread__target is not None:
            self._return = self._Thread__target(*self._Thread__args, **self._Thread__kwargs)

    def join(self, *args, **kwargs):
        super(ThreadWithReturn, self).join(*args, **kwargs)

        return self._return
