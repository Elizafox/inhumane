# Copyright © 2013 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.

from threading import RLock

pcounter = 0
_pc_lock = RLock()


class Player(object):
    def __init__(self, name):
        self.name = name

        # Unique ID
        with _pc_lock:
            global pcounter
            self.uid = pcounter
            pcounter += 1

    def rename(self, name):
        self.name = name

    def __eq__(self, other):
        return self.uid == other.uid

    def __hash__(self):
        return hash(self.uid)

    def __str__(self):
        return "{p}".format(p=self.name)

    def __repr__(self):
        return "Player({x}, cid={i})".format(x=self.name, i=self.uid)

