# Copyright © 2013 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.

from threading import RLock

pcounter = 0
_pc_lock = RLock()


class Player(object):

    """ A player object for use in the game. """

    def __init__(self, name, data=None):
        """ Initalise a player

        args:
            name: name of the player
            data: private data"""
        self.name = name
        self.data = data

        # Unique ID
        with _pc_lock:
            global pcounter
            self.uid = pcounter
            pcounter += 1

    def rename(self, name):
        """ Rename a player """
        self.name = name

    def __eq__(self, other):
        return self.uid == other.uid

    def __hash__(self):
        return hash(self.uid) + 1

    def __str__(self):
        return "{p}".format(p=self.name)

    def __repr__(self):
        return "Player({x}, cid={i}, data={d!r})".format(x=self.name,
                                                         i=self.uid,
                                                         d=self.data)
