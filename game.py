# Copyright © 2013 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.

from threading import RLock
from random import shuffle
from collections import deque, Counter, OrderedDict, defaultdict, Iterable

from orderedset import OrderedSet

gcounter = 0
_gc_lock = RLock()

class BaseGameError(Exception):
    """ The base for all game errors """
    pass

class GameError(BaseGameError):
    """ Class for internal game errors """
    pass

class GameConditionError(GameError):
    """ Invalid game condition """
    pass

class RuleError(BaseGameError):
    """ Class for rule violation errors """
    pass

class Game(object):
    """ The basic game object.

    Basically this holds the entire state for a given game minus (at present)
    player hands. A player can be attached to ONLY one game at a time. This is
    subject to change.

    Use the .add_player method to add Player instances to the game.

    Decks must be added at instantiation time.

    When errors with the game itself arise, GameError is thrown. When the rules
    are broken, RuleError is raised. Note that all forms of cheating are not
    caught (and you could cheat by setting attributes anyway, I won't add
    __setattr__ limits).
    """

    def __init__(self, name, **kwargs):
        """ Create a game.

        args:
            name: name of the game
            players: current players in the form of an Iterable. Can be empty.
            decks: card decks (see the Deck class)
            voting: HOUSE RULE: players vote instead of the tsar being used.
            maxcards: HOUSE RULE: change the number of cards per hand (default
                10)
            apxchg: HOUSE RULE: an Iterable containing (ap, cards) for
                trading. (default: forbidden)
            maxrounds: maximum number of game rounds (default unlimited)
            maxap: maximum number of AP to play to (default 10)
        """

        # Current players
        self.players = OrderedSet(kwargs.get("players", list()))

        # Card decks
        self.blackcards = deque()
        self.whitecards = deque()
        maxdraw = 0
        # Get all the decks
        # (and check for max len in each)
        for deck in kwargs.get("decks"):
            self.blackcards.extend(deck.blackcards)
            self.whitecards.extend(deck.whitecards)
            if deck.maxdraw > maxdraw: maxdraw = deck.maxdraw

        # Maximum amount of cards ever drawn
        self.maxdraw = maxdraw

        # Shuffle the decks
        shuffle(self.blackcards)
        shuffle(self.whitecards)

        # Discard piles
        self.discardblack = deque() 
        self.discardwhite = deque()

        # House rules
        self.voting = kwargs.get("voting", False)
        self.maxcards = kwargs.get("maxcards", 10)
        self.apxchg = kwargs.get("apxchg", (0, 0))
        # TODO more house rules

        # game play limits
        self.maxrounds = kwargs.get("maxrounds", None)
        self.maxap = kwargs.get("maxap", 10)
        if self.maxrounds is None and self.maxap is None:
            raise GameConditionError("Never-ending game")

        # Check to ensure we have enough cards for everyone
        # (After setting maxcards)
        self._check_enough()

        # Current tsar
        self.tsar = self.players[0] if len(self.players) > 0 else None
        self.tsarindex = 0

        # Black card in play
        self.blackplay = None

        # Players:decks/hands
        self.playercards = defaultdict(OrderedSet)
        self.playerplay = defaultdict(list)

        # Players last played
        self.playerlast = defaultdict(int)

        # Votes and AP
        self.voters = set()
        self.votes = Counter()
        self.ap = Counter()

        # Round counter
        self.rounds = 0

        # Currently in a round
        self.inround = False

        # Spent/suspended
        self.suspended = False
        self.spent = False

        with _gc_lock:
            global gcounter
            self.gid = gcounter
            gcounter += 1

    def player_vote(self, player, player2):
        """ Vote for a player if voting enabled.
        
        args:
            player: player voting
            player2: player voting for
        """

        if player not in self.players:
            raise RuleError("No external players voting!")
        if player2 not in self.players:
            raise RuleError("No voting for players not in the game!")
        if player in self.voters:
            raise RuleError("No double voting!")

        self.voters.add(player)
        self.votes[player2] += 1

        # Max votes had!
        if len(self.voters) == len(self.players):
            return self.round_end()
        # XXX - discussion - should it close the voting when a majority is
        # reached?
        # elif self.votes.most_common(1)[0][1] >= (len(self.players) / 2):
        #     return self.round_end()

        return None

    def player_trade_ap(self, player, cards):
        """ Trade AP for cards for the given player """

        if player not in self.players:
            raise GameError("Player not in the game!")

        # Get the exchange rate
        # (see if exchange is permitted)
        if self.apxchg == (0, 0):
            raise RuleError("Trading AP for cards is not permitted")

        ap, ccount = self.apxchg

        if self.ap[player] < ap:
            raise RuleError("Insufficient AP")

        if isinstance(cards, Iterable):
            if len(cards) > ccount:
                raise RuleError("Too many cards")
            self.playercards[player].difference_update(cards)
        else:
            self.playercards[player].remove(cards)

        self.ap[player] -= ap

        # Deal a new hand
        self.player_deal()

    def player_get_ap(self, player):
        """ Get AP for a user """

        if player is not None and player not in self.players:
            raise GameError("Player not in the game!")
        return self.ap[player]

    def _check_enough(self):
        maxhands = (self.maxdraw + self.maxcards) * len(self.players)
        if maxhands > len(self.whitecards):
            raise GameConditionError("Insufficient cards for all players!")

    def new_tsar(self, player=None):
        """ Select a new tsar (without player, automatically). """

        if player is not None and player not in self.players:
            raise GameError("Player not in the game!")

        if len(self.players) == 0:
            # Game is spent.
            self.suspended = True
            self.tsar = None
            self.tsarindex = 0
            raise GameConditionError("Insufficient Players")

        if player is not None and player not in self.players:
            raise GameError("Invalid player")

        if not player:
            player = self.players[(self.tsarindex + 1) % len(self.players)]

        self.tsarindex = self.players.index(player)
        self.tsar = player

        return self.tsar

    def player_add(self, player):
        """ Add a new player to the game """

        if player in self.players:
            raise GameError("Adding an existing player!")

        self._check_enough()

        self.players.add(player)

        # Reviving a game if it was suspended due to losing all but one player
        if len(self.players) > 1:
            self.suspended = False

        player.game_start(self)

        if len(self.players) == 1:
            self.new_tsar(player)

        # Give them cards if the round hasn't yet begun
        if not self.inround:
            self.player_deal(player, self.maxcards) 

    def player_clear(self, player):
        """ Clear a player out """

        if player not in self.players:
            raise GameError("Player not in the game!")

        # Return all player cards to the deck
        self.discardwhite.extend(self.playercards[player])
        self.discardwhite.extend(self.playerplay[player])

        del self.playercards[player]
        del self.playerplay[player]

        # Destroy their state
        self.ap.pop(player, None)
        self.votes.pop(player, None)
        self.voters.discard(player)

        if player == self.tsar and not self.spent and not self.suspended:
            # Reassign tsar if need be
            self.new_tsar()

    def player_remove(self, player):
        """ Remove a player from the game """

        if player is not None and player not in self.players:
            raise GameError("Player not in the game!")

        self.player_clear(player)
        self.players.remove(player)

        player.game_end()

        if len(self.players) == 1:
            # Game can't continue!
            self.suspended = True
        elif len(self.players) == 0:
            # Punt. destroy the game.
            self.end_game(True)

    def player_play(self, player, cards):
        if player not in self.players:
            raise GameError("Player not in the game!")

        if not self.inround:
            raise GameError("Not in a round to play!")

        if not self.voting and self.tsar == player:
            raise RuleError("The tsar can't play!")

        if isinstance(cards, Iterable):
            clen = len(cards)
        else:
            clen = 1

        if clen != self.blackplay.playcount:
            raise RuleError("Invalid number of cards played")

        self.playerlast[player] = self.rounds

        if isinstance(cards, Iterable):
            self.playercards[player].difference_update(cards)
            self.playerplay[player].extend(cards)
        else:
            self.playercards[player].remove(cards)
            self.playerplay[player].append(cards)

    def check_empty(self):
        """ Check if the decks are empty, and add cards from the discard pile if
        needs be """

        if len(self.discardblack) == len(self.blackcards) == 0:
            raise GameConditionError("Empty decks!")

        blackempty = whiteempty = False

        if len(self.blackcards) == 0:
            # Swap them
            tmp = self.blackcards
            self.blackcards = self.discardblack
            self.discardblack = tmp

            shuffle(self.blackcards)

            blackempty = True

        if len(self.whitecards) == 0:
            tmp = self.whitecards
            self.whitecards = self.discardwhite
            self.discardwhite = tmp

            shuffle(self.whitecards)

            whiteempty = True

        return (blackempty, whiteempty)

    def player_deal(self, player, count=0):
        """ Deal count white cards to the player """

        if player not in self.players:
            raise GameError("Player not in the game!")

        if count < 0:
            return
        elif count == 0:
            count = self.maxcards - len(self.playercards[player])
            if count == 0: return

        deal = list()
        for i in range(count):
            self.check_empty() # XXX I hate constantly checking
            deal.append(self.whitecards.popleft())

        self.player_deal_raw(player, deal)

    def player_deal_raw(self, player, cards):
        """ raw version of player_deal where you specify your own cards. Only use
        if you know what you're doing. """

        if player not in self.players:
            raise GameError("Player not in the game!")

        if isinstance(cards, Iterable):
            self.playercards[player].update(cards)
        else:
            self.playercards[player].add(cards)

    def player_all_deal(self):
        """Deal to all the players to fill their hands"""

        for player in self.players:
            self.player_deal(player)

    def player_cards(self, player):
        """ Return a player's cards """

        if player not in self.players:
            raise GameError("Player not in the game!")

        return self.playercards[player]

    def round_start(self):
        """ Start a round. """

        if self.inround:
            raise GameError("Attempting to start a round with one existing!")
        elif self.spent:
            raise GameError("Can't start a spent game!")
        elif self.suspended:
            raise GameConditionError("Game is suspended pending more players.")

        # No players should have leftover played cards
        # (they should be purged at the end of a round)
        assert [len(self.playerplay[player]) == 0 for player in self.players].count(False) == 0

        # Black card should be the null sentinel
        assert self.blackplay is None

        self.inround = True
        self.rounds += 1

        # Recycle the decks if need be
        self.check_empty()

        self.blackplay = self.blackcards.popleft()

        # Add cards to players' hands
        if self.blackplay.drawcount:
            for player in self.players:
                self.player_deal(player, self.blackplay.drawcount)

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

    def round_winner(self, player=None):
        """ Choose the winner of a round. If player is omitted, it will choose
        it based on the rules.

        Please use round_end instead unless you know what you're doing.

        return:
            winners: what it says on the tin (NOTE: for voting rounds, it
                returns a two element tuple - first element is the winning tally,
                second is a list of the winners.
        """

        if player is not None and player not in self.players:
            raise GameError("Player not in the game!")

        if len(self.players) <= 1:
            if self.spent or self.suspended:
                return None

        def give_ap(player): self.ap[player] += 1

        if player:
            # We have a winner - chosen via tsar or fiat.
            if player == self.tsar:
                raise RuleError("Tsar can't declare himself winner!")
            winning = [player]
            give_ap(player)
        elif self.voting:
            # A voting round without a fiat-declared winner.
            winning = self._get_top(self.votes, give_ap)
        else:
            raise GameConditionError("Player can't be None in a Tsar-based game")

        # NOTE: for voting rounds, it returns a two element tuple - first
        # element is the winning tally, second is a list of the winners.
        return winning

    def round_end(self, player=None):
        """ End a round and return round_winner. Pass through a player to select
        the result the tsar picked.
        
        Be sure to check the spent member to see if the game is done; if it is,
        the game winners are returned, instead.
        """

        if player is not None and player not in self.players:
            raise GameError("Player not in the game!")
        if not self.inround:
            raise GameError("Attempting to end a nonexistent round!")

        self.inround = False

        # Get the winners
        winners = self.round_winner(player)

        # Discard the black card
        self.discardblack.append(self.blackplay)
        self.blackplay = None
            
        # Return played white cards to the discard pile and clear their played
        # cards, then give them new cards.
        for player in self.players:
            self.discardwhite.extend(self.playerplay[player])
            self.playerplay[player].clear()

            self.player_deal(player)

        # Reset votes
        self.voters.clear()
        self.votes.clear() 

        # Check for end-of-game conditions
        if self.maxrounds is not None and self.rounds == self.maxrounds:
            return self.game_end()
        elif self.maxap != None:
            # Maximum AP earnt (first most common ((1)[0]) then [1] for the
            # tally.
            max = self.ap.most_common(1)[0][1]
            if max >= self.maxap:
                return self.game_end()

        # Choose the new tsar
        self.new_tsar()

        return winners

    def game_end(self, forreal=False):
        """ End the game. forreal will PURGE the game. Also return the winners
        of the game (None if <= 1 player)."""

        self.suspended = True
        self.spent = True

        if self.inround:
            self.round_end() # XXX discard?

        if self.players <= 1:
            # Nobody wins. :|
            winners = None
        else:
            # Find the winners
            winners = self._get_top(self.ap)

        # Clear the votes and AP
        self.votes.clear()
        self.ap.clear()

        # Clear the tsar
        self.tsar = None
        self.tsarindex = None

        self.rounds = 0

        if forreal:
            # Nuke the players
            for player in self.players:
                self.player_remove()

            # Wipe the decks
            self.blackcard.clear()
            self.whitecard.clear()
            self.discardblack.clear()
            self.discardwhite.clear()
        
            self.maxdraw = None
        else:
            # Clean up the players
            for player in self.players:
                player.player_clear()

            # Add the discard piles to the main decks
            self.blackcard.extend(self.discardblack)
            self.whitecard.extend(self.discardwhite)
            self.discardblack.clear()
            self.discardwhite.clear()

        return winners
