# Copyright © 2013 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.

import six

from threading import RLock

from orderedset import OrderedSet
from game import GameError

pcounter = 0
_pc_lock = RLock()


class Player(object):
    def __init__(self, name, game=None):
        self.name = name

        # Unique ID
        with _pc_lock:
            global pcounter
            self.uid = pcounter
            pcounter += 1

        self.game = game
        self.last_played = 0
        self.cards = OrderedSet()
        self.play_cards = list()
        self.ap = 0

    def deal(self, *kargs):
        self.cards.update(kargs)
        
    def play(self, *kargs):
        assert self.game
        assert self.game.in_round == True
        assert self.game.tsar != self # FIXME - tsar based 

        if len(kargs) != self.game.black_play.playcount:
            raise GameError('Invalid number of cards played')

        self.last_played = self.game.rounds

        self.cards.difference_update(kargs)
        self.play_cards.extend(kargs)

    def game_start(self, game):
        assert self.game is None

        self.game = game
        self.last_played = 0
        self.cards.clear()
        self.play_cards.clear()
        self.ap = 0

    def game_end(self):
        if self.game:
            self.game.remove_player(self)

        # Erase their cards
        self.game = None
        self.last_played = 0
        self.cards.clear()
        self.play_cards.clear()
        self.ap = 0

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

