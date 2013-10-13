# Copyright © 2013 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.

from threading import RLock
from random import shuffle
from collections import deque

from orderedset import OrderedSet

gcounter = 0
_gc_lock = RLock()

class GameError(Exception):
    pass

class Game(object):
    def __init__(self, name, **kwargs):
        self.name = name

        # Current players
        self.players = kwargs.get('players', OrderedSet())

        self.black_cards = deque()
        self.white_cards = deque()
        maxdraw = 0
        # Get all the decks
        # (and check for max len in each)
        for deck in kwargs.get('decks'):
            self.black_cards.extend(deck.black_cards)
            self.black_cards.extend(deck.white_cards)
            if deck.maxdraw > maxdraw: maxdraw = deck.maxdraw

        self.maxdraw = maxdraw

        # Check to ensure we have enough cards for everyone
        self.check_enough()

        # Shuffle the decks
        shuffle(self.black_cards)
        shuffle(self.white_cards)

        # Discard piles
        self.discard_black = deque() 
        self.discard_white = deque()

        # Current tsar (tracked for simplicity reasons even in tsar-less games)
        self.tsar = self.players[0] if len(self.players) > 0 else None
        self.tsar_index = 0

        # Black card in play
        self.black_play = None

        # Round counter
        self.rounds = 0

        # Currently in a round
        self.in_round = False

        # Spent
        self.spent = False

        with _gc_lock:
            global gcounter
            self.gid = gcounter
            gcounter += 1

    def check_enough(self):
        maxhands = self.maxdraw + 10
        if maxhands > len(self.white_cards):
            raise GameError("Insufficient cards for all players!")

    def new_tsar(self, player=None):
        if len(self.players) == 0:
            # Game is spent.
            self.spent = True
            self.tsar = None
            self.tsar_index = 0

        if len(self.players) == 0:
            raise GameError("Insufficent players")

        if player is not None and player not in self.players:
            raise GameError("Invalid player")

        if not player:
            player = self.players[(self.tsar_index + 1) % len(self.players)]

        self.tsar_index = self.players.index(player)
        self.tsar = player

        return self.tsar

    def add_player(self, player):
        self.check_enough()

        # Reviving a game if it was spent due to losing all players
        self.spent = False

        self.players.add(player)
        player.game_start(self)

        if len(self.players) == 1:
            self.new_tsar(player)

        # Give them cards if the round hasn't yet begun
        if not self.in_round:
            self.deal_white(player, 10)

    def remove_player(self, player):
        self.players.remove(player)

        # Return their cards to the discard pile
        self.discard_white.extend(player.cards)

        # If they played any cards, return those too
        self.discard_white.extend(player.play_cards)

        # Set to None so it doesn't get into a loop
        player.game = None
        player.game_end()

        # If they were tsar, reassign it
        if player == self.tsar:
            self.new_tsar()

    def check_empty(self):
        if len(self.discard_black) != len(self.black_cards) != 0:
            raise GameError("Empty decks!")

        black_empty = white_empty = False

        if len(self.black_cards) == 0:
            # Swap them
            tmp = self.black_cards
            self.black_cards = self.discard_black
            self.discard_black = tmp

            shuffle(self.black_cards)

            black_empty = True

        if len(self.white_cards) == 0:
            tmp = self.white_cards
            self.white_cards = self.discard_white
            self.discard_white = tmp

            shuffle(self.white_cards)

            white_empty = True

        return (black_empty, white_empty)

    def deal_white(self, player, count):
        deal = list()
        for i in range(count):
            self.check_empty() # XXX I hate constantly checking
            deal.append(self.white_cards.popleft())

        player.deal(deal)

    def start_round(self):
        if self.in_round:
            raise GameError('Attempting to start a round with one existing!')

        # No players should have leftover played cards
        # (they should be purged at the end of a round)
        assert [len(player.play_cards) == 0 for player in self.players].count(False) == 0

        # Black card should be the null sentinel
        assert self.black_play is None

        self.in_round = True
        self.rounds += 1

        # Recycle the decks if need be
        self.check_empty()

        self.black_play = self.black_cards.popleft()

        # Add cards to players' hands
        for player in self.players:
            self.deal_white(player, self.black_play.drawcount)

    def choose_winner(self, player):
        # FIXME - presently tsar-based...
        if player == self.tsar:
            raise GameError("Tsar can't declare himself winner!")

        player.ap += 1
        self.end_round()

    def end_round(self):
        if not self.in_round:
            raise GameError('Attempting to end a nonexistent round!')

        # Discard the black card
        self.discard_black.append(self.black_play)
        self.black_play = None
            
        # Return played white cards to the discard pile and clear their played
        # cards, then give them new cards.
        for player in self.players:
            self.discard_white.extend(player.play_cards)
            player.play_cards.clear()

            if len(player.cards) < 10:
                self.deal_white(player, 10 - len(player.cards))

        # Choose the new tsar
        self.new_tsar()

        self.in_round = False
