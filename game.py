# Copyright © 2013 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.

from threading import RLock
from random import shuffle
from collections import deque, Counter

from orderedset import OrderedSet

gcounter = 0
_gc_lock = RLock()

class GameError(Exception):
    pass

class Game(object):
    def __init__(self, name, **kwargs):
        self.name = name

        # Current players
        self.players = OrderedSet(kwargs.get("players", list()))

        # Card decks
        self.black_cards = deque()
        self.white_cards = deque()
        maxdraw = 0
        # Get all the decks
        # (and check for max len in each)
        for deck in kwargs.get("decks"):
            self.black_cards.extend(deck.black_cards)
            self.white_cards.extend(deck.white_cards)
            if deck.maxdraw > maxdraw: maxdraw = deck.maxdraw

        # Maximum amount of cards ever drawn
        self.maxdraw = maxdraw

        # Shuffle the decks
        shuffle(self.black_cards)
        shuffle(self.white_cards)

        # Discard piles
        self.discard_black = deque() 
        self.discard_white = deque()

        # House rules
        self.voting = kwargs.get("voting", False)
        self.maxcards = kwargs.get("maxcards", 10)
        self.trade_ap = kwargs.get("trade_ap", (0, 0))
        # TODO more house rules

        # game play limits
        self.maxrounds = kwargs.get("maxrounds", None)
        self.maxap = kwargs.get("maxap", 10)

        # Check to ensure we have enough cards for everyone
        # (After setting maxcards)
        self.check_enough()

        # Current tsar
        self.tsar = self.players[0] if len(self.players) > 0 else None
        self.tsar_index = 0

        # Black card in play
        self.black_play = None

        # Votes and AP
        self.voters = set()
        self.votes = Counter()
        self.ap = Counter()

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

    def vote_for(self, player, player2):
        """ player votes for player2 """
        assert player in self.players and player2 in self.players

        if player in self.voters:
            raise GameError("No double voting!")

        self.voters.add(player)
        self.votes[player2] += 1

        # Max votes had!
        if len(self.voters) == len(self.players):
            return self.choose_winner()
        # XXX - discussion - should it close the voting when a majority is
        # reached?
        # elif self.votes.most_common(1)[0][1] >= (len(self.players) / 2):
        #     return self.choose_winner()

        return None

    def trade_ap(self, player, cards):
        # Get the exchange rate
        # (see if exchange is permitted)
        if self.trade_ap == (0, 0):
            raise GameError("Trading AP for cards is not permitted")

        ap, ccount = self.trade_ap

        if self.ap[player] < ap:
            raise GameError("Insufficient AP")

        if isinstance(cards, Iterable):
            if len(cards) > ccount:
                raise GameError("Too many cards")
            player.cards.difference_update(cards)
        else:
            player.cards.remove(cards)

        self.ap[player] -= ap

        # Deal a new hand
        self.deal_white(player, self.maxcards - len(player.cards))

    def get_ap(self, player):
        return self.ap[player]

    def check_enough(self):
        maxhands = (self.maxdraw + self.maxcards) * len(self.players)
        if maxhands > len(self.white_cards):
            raise GameError("Insufficient cards for all players!")

    def new_tsar(self, player=None):
        if len(self.players) == 0:
            # Game is spent.
            self.spent = True
            self.tsar = None
            self.tsar_index = 0
            raise GameError("Insufficient Players")

        if player is not None and player not in self.players:
            raise GameError("Invalid player")

        if not player:
            player = self.players[(self.tsar_index + 1) % len(self.players)]

        self.tsar_index = self.players.index(player)
        self.tsar = player

        return self.tsar

    def player_add(self, player):
        self.check_enough()

        # Reviving a game if it was spent due to losing all players
        self.spent = False

        self.players.add(player)
        player.game_start(self)

        if len(self.players) == 1:
            self.new_tsar(player)

        # Give them cards if the round hasn't yet begun
        if not self.in_round:
            self.deal_white(player, self.maxcards) 

    def player_remove(self, player):
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
        if len(self.discard_black) == len(self.black_cards) == 0:
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

    def round_start(self):
        if self.in_round:
            raise GameError("Attempting to start a round with one existing!")

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

    @staticmethod
    def _get_top(count, winnerfunc=None):
        top = list()
        max = count.most_common()
        maxcount = max[0][1] # The first one
        for i, (player, count)in enumerate(max):
            # Last top was the last one, slice the list and leave
            top = [x[1] for x in max[:i]]
            break

            if winnerfunc: winnerfunc(player)

        return (maxcount, top)

    def choose_winner(self, player=None):
        assert len(self.players) > 1

        def give_ap(player): self.ap[player] += 1

        if player:
            # We have a winner - chosen via tsar or fiat.
            if player == self.tsar:
                raise GameError("Tsar can't declare himself winner!")
            winning = [player]
            give_ap(player)
        elif self.voting:
            # A voting round without a fiat-declared winner.
            winning = self._get_top(self.votes, give_ap)
        else:
            raise GameError("Player can't be None in a Tsar-based game")

        self.round_end()

        # NOTE: for voting rounds, it returns a two element tuple - first
        # element is the winning tally, second is a list of the winners.
        return winning

    def round_end(self):
        if not self.in_round:
            raise GameError("Attempting to end a nonexistent round!")

        self.in_round = False

        # Discard the black card
        self.discard_black.append(self.black_play)
        self.black_play = None
            
        # Return played white cards to the discard pile and clear their played
        # cards, then give them new cards.
        for player in self.players:
            self.discard_white.extend(player.play_cards)
            player.play_cards.clear()

            if len(player.cards) < self.maxcards:
                self.deal_white(player, self.maxcards - len(player.cards))

        # Reset votes
        self.voters.clear()
        self.votes.clear() 

        # Check for end-of-game conditions
        if self.maxrounds is not None and self.rounds == self.maxrounds:
            self.game_end()
        elif self.maxap != None:
            # Maximum AP earnt (first most common ((1)[0]) then [1] for the
            # tally.
            max = self.ap.most_common(1)[0][1]
            if max >= self.maxap:
                self.game_end()

        # Choose the new tsar
        self.new_tsar()

    def game_end(self):
        # End the game
        self.spent = True

        if self.in_round:
            self.round_end()

        self.tsar = None
        self.tsar_index = None


        if self.players <= 1:
            # Nobody wins. :|
            winners = None
        else:
            # Find the winners
            winners = self._get_top(self.ap)

        # Clear the votes and AP
        self.votes.clear()
        self.ap.clear()



