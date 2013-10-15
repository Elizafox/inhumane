# Copyright © 2013 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.

import six

from collections import Iterable
from threading import RLock

from orderedset import OrderedSet
from game import GameError, RuleError

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

        self.cards = OrderedSet()
        self.playcards = list()

        self.last_played = 0
        self.game = game

    def deal(self, cards):
        if isinstance(cards, Iterable):
            self.cards.update(cards)
        else:
            self.cards.add(cards)
        
    def play(self, cards):
        assert self.game

        if not self.game:
            raise GameError("No game!")

        if not self.game.inround:
            raise GameError("Not in a round to play!")

        if not self.game.voting and self.game.tsar == self:
            raise RuleError("The tsar can't play!")

        if isinstance(cards, Iterable):
            clen = len(cards)
        else:
            clen = 1

        if clen != self.game.blackplay.playcount:
            raise RuleError("Invalid number of cards played")

        self.last_played = self.game.rounds

        if isinstance(cards, Iterable):
            self.cards.difference_update(cards)
            self.playcards.extend(cards)
        else:
            self.cards.remove(cards)
            self.playcards.append(cards)

    def game_start(self, game):
        assert self.game is None
        self.game = game

    def game_end(self):
        self.last_played = 0
        self.game = None

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

