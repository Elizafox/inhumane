# Copyright © 2013 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.

import six

from collections import Iterable
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
        self.votes = 0

    def deal(self, cards):
        if isinstance(cards, Iterable):
            self.cards.update(cards)
        else:
            self.cards.add(cards)
        
    def play(self, cards):
        assert self.game

        if not self.game:
            raise GameError("No game!")

        if not self.game.in_round:
            raise GameError("Not in a round to play!")

        if not self.game.voting and self.game.tsar == self:
            raise GameError("The tsar can't play!")

        if isinstance(cards, Iterable):
            clen = len(cards)
        else:
            clen = 1

        if clen != self.game.black_play.playcount:
            raise GameError("Invalid number of cards played")

        self.last_played = self.game.rounds

        if isinstance(cards, Iterable):
            self.cards.difference_update(cards)
            self.play_cards.extend(cards)
        else:
            self.cards.remove(cards)
            self.play_cards.append(cards)

    def vote_for(self, player):
        if not self.game:
            raise GameError("No game!")

        if not self.game.voting:
            raise GameError("Not a voting game.")

        if self == player:
            raise GameError("Cannot vote for yourself!")

        self.votes += 1
        if self.votes == (len(self.game.players) - 1):
            # Declare victory
            self.game.choose_winner(player)

    def game_start(self, game):
        assert self.game is None

        self.reset()
        self.game = game

    def game_end(self):
        if self.game:
            self.game.remove_player(self)

        self.reset()

    def reset(self):
        self.game = None
        self.last_played = 0
        self.cards.clear()
        self.play_cards.clear()
        self.ap = 0
        self.votes = 0

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

