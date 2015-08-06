# Copyright © 2013 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.

from random import shuffle, SystemRandom
from collections import deque, Counter, OrderedDict, defaultdict, Iterable
from operator import itemgetter
from uuid import uuid1
from warnings import warn

from .contrib.orderedset import OrderedSet
from .deck import Deck, basepacks


rng = SystemRandom()


class BaseGameError(Exception):

    """The base for all game errors."""


class GameError(BaseGameError):

    """Class for internal game errors."""


class GameConditionError(GameError):

    """Invalid game condition."""


class RuleError(BaseGameError):

    """Class for rule violation errors."""


class Game(object):

    """The basic game object.

    Basically this holds the entire state for a given game minus (at present)
    player hands.

    Decks must be added at instantiation time.

    When an error with the game arises, :py:exc:`~inhumane.game.GameError` is
    raised. When the rules are broken, :py:exc:`~inhumane.game.RuleError` is
    raised. Note that all forms of cheating are not caught (and you could cheat
    by setting attributes anyway).

    :ivar name:
        The name of the game. Can be freeform.

    :ivar blackcards:
        A ``deque`` holding the present set of black cards from the deck.

    :ivar whitecards:
        A ``deque`` holding the present set of white cards from the deck.

    :ivar discardblack:
        The black discard pile.

    :ivar discardwhite:
        The white discard pile.

    :ivar blackcard:
        The present black card in play.

    :ivar players:
        An ``OrderedSet`` of player UUID's

    :ivar playerplay:
        An ``OrderedDict`` of player UUID's to cards played.
    
    :ivar playerlast:
        A ``dict`` containing player UUID's to last round played.

    :ivar voters:
        An ``OrderedDict`` of players who have voted this round and the player
        they have voted for, if voting is enabled. This is subject to change.

    :ivar votes:
        A ``Counter`` containing the total number of votes players have
        received. Note that players without votes aren't listed.

    :ivar gamblers:
        The ``set`` containing gamblers for this round, if gambling is
        enabled.

    :ivar ap:
        A ``Counter`` representing the amount of player's current AP.

    :ivar rounds:
        Present number of rounds played.

    :ivar suspended:
        The game is suspended for some reason (usually insufficient players).

    :ivar spent:
        The game is spent and is over.
    """

    def __init__(self, name, **kwargs):
        """Create a game.

        :param name:
            Name of the game.

        :key players:
            An ordered iterable containing player data to add. Players are
            added based on this data and placed (in order) in the
            :py:attr:`~inhumane.Game.players` attribute.

        :key decks:
            An iterable containing card decks. See the
            :py:class:~inhumane.deck.Deck` class for more information.

        :key voting:
            A house rule. If set to true, players vote instead of the tsar
            being used. Voting is presently not anonymous (this is a bug).

        :key maxcards:
            A house rule. Change the number of cards per hand. The default is
            10.

        :key apxchg:
            A house rule. This is a tuple containing ``(ap, card)`` counts for
            exchange of AP for new cards. This is forbidden by default.

        :key maxrounds:
            A house rule. Maximum number of rounds to play for. The default is
            unlimited, until a winner is chosen.

        :key maxap:
            A house rule. Maximum number of AP to play to (default is 10).
        """
        self.name = name

        # Current players
        self.players = OrderedSet()

        # Card decks
        self.blackcards = deque()
        self.whitecards = deque()
        maxdraw = 0
        # Get all the decks
        # (and check for max len in each)
        for deck in kwargs.get("decks", [Deck(basepacks)]):
            self.blackcards.extend(deck.blackcards)
            self.whitecards.extend(deck.whitecards)
            if deck.maxdraw > maxdraw:
                maxdraw = deck.maxdraw

        # Maximum amount of cards ever drawn
        self.maxdraw = maxdraw

        # Shuffle the decks
        # Use the system RNG to (try to) ensure all possible shuffle states
        # occur, because the default RNG only has 2**32 ish states and a deck
        # can have 2**255.6 possible shuffles.
        shuffle(self.blackcards, rng.random)
        shuffle(self.whitecards, rng.random)

        # Discard piles
        self.discardblack = deque()
        self.discardwhite = deque()

        # Black card in play
        self.blackcard = None

        # Players:decks/hands
        self.playercards = defaultdict(OrderedSet)
        self.playerplay = OrderedDict()

        # Round that the players last played
        self.playerlast = defaultdict(int)

        # Votes and AP
        self.voters = dict()
        self.votes = Counter()
        self.ap = Counter()
        self.gamblers = set()
        self.ap_grant = 1

        # Round counter
        self.rounds = 0

        # Currently in a round
        self.inround = False

        # Spent/suspended
        self.suspended = False
        self.spent = False

        # House rules
        self.gambling = kwargs.get("gambling", True)  # Technically official...
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
        self.tsar = None
        self.tsarindex = 0

        self.playerdata = dict()

        # Add the players if we have any
        for data in kwargs.get('players', list()):
            self.player_add(data)

        self.gid = uuid1()

    def player_vote(self, player, player2):
        """Vote for a player if voting enabled.

        :param player:
            The player voting.

        :param player2:
            The player being voted for.

        :returns:
            ``(False, turnout)`` for no decision made, or ``(True, turnout)``
            when a plurality is reached.
        """

        if not self.voting:
            raise RuleError("Voting is prohibited in this game")

        if player not in self.players:
            raise RuleError("No external players voting!")

        if player2 not in self.players:
            raise RuleError("No voting for players not in the game!")

        if player in self.voters:
            raise RuleError("No double voting!")

        self.voters[player] = player2
        self.votes[player2] += 1

        turnout = len(self.voters) / len(self.players)

        # Majority reached
        if self.votes.most_common(1)[0][1] >= (len(self.players) / 2):
            return (True, turnout)

        return (False, turnout)

    def player_get_vote_sel(self, player):
        """Get the vote for a given player."""

        if not self.voting:
            raise RuleError("Voting is prohibited in this game.")

        if player not in self.players:
            raise RuleError("No external players voting!")

        return self.voters.get(player, None)

    def player_all_get_vote_sel(self):
        """Get the votes for all players."""

        if not self.voting:
            raise RuleError("Voting is prohibited in this game")

        votes = [(player, self.player_get_vote_sel(player)) for player in
                 self.players]

        return votes

    def player_get_vote_count(self, player):
        """Get the vote count for a given user."""
        return self.votes[player]

    def player_all_get_vote_count(self, sort_vote=True):
        """Get the vote count for all users."""
        count = [(player, self.player_get_vote_count(player)) for player in
                 self.players]
        if sort_vote:
            count = sorted(count, key=itemgetter(1))

        return count

    def player_trade_ap(self, player, cards):
        """Trade AP for cards for the given player."""
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

        self.player_discard(player, cards)

        self.ap[player] -= ap

        # Deal a new hand
        self.player_deal(player)

    def player_gamble(self, player, card):
        """Gamble an AP on an additional white card.

        Only usable when a black card is pick one...
        """
        if player not in self.players:
            raise GameError("Player not in the game!")

        if not self.gambling:
            raise RuleError("Gambling is not permitted")

        if player in self.gamblers:
            raise RuleError("No double gambling!")

        if self.blackcard.playcount > 1:
            # NOTE: the official rules seem to imply that you can't do this.
            # Since the precise semantics of doing otherwise are pretty
            # ill-defined, I'm going to go with this rule.
            raise RuleError("Can't gamble on pick > 1 cards")

        if self.ap[player] <= 1:
            raise RuleError("Player can't gamble - not enough AP")

        if isinstance(card, Iterable):
            raise RuleError("Cannot gamble more than one card!")

        if card not in self.playerhand[player]:
            raise GameError("Can't gamble a card the player doesn't have!")

        self.ap[player] -= 1
        self.ap_grant += 1
        self.player_discard(player, card)

        if player not in self.playerplay:
            self.playerplay[player] = list()

        self.playerplay[player].append(card)
        self.gamblers.add(player)

    def player_get_ap(self, player):
        """Get AP for a user."""
        if player is not None and player not in self.players:
            raise GameError("Player not in the game!")

        return self.ap[player]

    def player_all_get_ap(self, sort_score=True):
        """Get AP for all users."""
        ap = [(player, self.player_get_ap(player)) for player in self.players]
        if sort_score:
            ap = sorted(ap, key=itemgetter(1))

        return ap

    def _check_enough(self):
        maxhands = (self.maxdraw + self.maxcards) * len(self.players)
        if maxhands > len(self.whitecards):
            raise GameConditionError("Insufficient cards for all players!")

    def player_add(self, data=None):
        """Add a new player to the game.

        :param data:
            Private data for new player.

        :returns:
            The player UUID. Keep this around for later use.
        """

        self._check_enough()

        player = uuid1()

        self.players.add(player)
        self.playerdata[player] = data

        # Reviving a game if it was suspended due to losing all but one player
        self.suspended = len(self.players) < 1

        if len(self.players) == 2:
            # Choose a new tsar now that we have enough players
            self.game_new_tsar(player)

        # Give them cards if the round hasn't yet begun
        if not self.inround:
            self.player_deal(player, self.maxcards)

        return player

    def player_clear(self, player):
        """Clear a player out."""
        if player not in self.players:
            raise GameError("Player not in the game!")

        # Return all player cards to the deck
        self.discardwhite.extend(self.playercards[player])

        # Clear state
        self.playercards.pop(player, None)
        self.playerlast.pop(player, None)

        # This is so indexes don't get fucked up
        if player in self.playerplay:
            self.discardwhite.extend(self.playerplay[player])
            self.playerplay[player] = []

        self.ap.pop(player, None)
        self.votes.pop(player, None)
        self.voters.pop(player, None)

        if self.inround and self.playerlast[player] == self.rounds:
            del self.playerlast[player]

        if self.tsar is not None and player == self.tsar and not self.spent and not self.suspended:
            # Reassign tsar if need be
            self.game_new_tsar()

    def player_remove(self, player):
        """Remove a player from the game."""
        if player is not None and player not in self.players:
            raise GameError("Player not in the game!")

        self.player_clear(player)
        self.players.remove(player)

        if len(self.players) == 1:
            # Game can't continue!
            self.suspended = True
        elif len(self.players) == 0:
            # Punt. destroy the game.
            return self.game_end(True)

    def player_play(self, player, cards):
        if player not in self.players:
            raise GameError("Player not in the game!")

        if not self.inround:
            raise GameError("Not in a round to play!")

        if not self.voting and self.tsar == player:
            raise RuleError("The tsar can't play!")

        if self.playerlast[player] == self.rounds:
            raise RuleError("Can't double play!")

        if isinstance(cards, Iterable):
            clen = len(cards)
        else:
            clen = 1

        if clen != self.blackcard.playcount:
            raise RuleError("Invalid number of cards played")

        self.playerlast[player] = self.rounds

        if player not in self.playerplay:
            self.playerplay[player] = list()

        if isinstance(cards, Iterable):
            self.playercards[player].difference_update(cards)
            self.playerplay[player].extend(cards)
        else:
            self.playercards[player].remove(cards)
            self.playerplay[player].append(cards)

    def player_pass(self, player):
        """A player is skipping their turn."""
        if player not in self.players:
            raise GameError("Player not in the game!")

        if not self.inround:
            raise GameError("Not in a round to play!")

        if not self.voting and self.tsar == player:
            raise RuleError("The tsar can't play!")

        if self.playerlast[player] == self.rounds:
            raise GameError("You have already played!")

        self.playerlast[player] = self.rounds

    def player_played(self):
        warn("This method is deprecated, use playerplay.items() instead",
             DeprecationWarning, 2)
        return self.playerplay.items()

    def card_refill(self):
        """Check if the decks are empty, and add cards from the discard pile if
        needs be."""
        if len(self.discardblack) == len(self.blackcards) == 0:
            raise GameConditionError("Empty decks!")

        blackempty = whiteempty = False

        if len(self.blackcards) == 0:
            # Swap them
            tmp = self.blackcards
            self.blackcards = self.discardblack
            self.discardblack = tmp

            shuffle(self.blackcards, rng.random)

            blackempty = True

        if len(self.whitecards) == 0:
            tmp = self.whitecards
            self.whitecards = self.discardwhite
            self.discardwhite = tmp

            shuffle(self.whitecards, rng.random)

            whiteempty = True

        return (blackempty, whiteempty)

    def card_black(self):
        """Return the current black card."""
        warn("This method is deprecated, use self.blackcard instead",
             DeprecationWarning, 2)
        return self.blackcard

    def player_deal(self, player, count=0):
        """Deal count white cards to the player."""

        if player not in self.players:
            raise GameError("Player not in the game!")

        if count < 0:
            return
        elif count == 0:
            count = self.maxcards - len(self.playercards[player])
            if count == 0:
                return

        deal = list()
        for i in range(count):
            self.card_refill()  # XXX I hate constantly checking
            deal.append(self.whitecards.popleft())

        self.player_deal_raw(player, deal)

    def player_deal_raw(self, player, cards):
        """raw version of player_deal where you specify your own cards.

        Only use if you know what you're doing.
        """
        if player not in self.players:
            raise GameError("Player not in the game!")

        if isinstance(cards, Iterable):
            self.playercards[player].update(cards)
        else:
            self.playercards[player].add(cards)

    def player_all_deal(self):
        """Deal to all the players to fill their hands."""

        for player in self.players:
            self.player_deal(player)

    def player_cards(self, player):
        """Return a player's cards."""

        if player not in self.players:
            raise GameError("Player not in the game!")

        return sorted(self.playercards[player])

    def player_discard(self, player, cards):
        """Discard cards from a player's hands into the discard pile.

        if cards is None, discard the entire hand (excluding cards in
        play)

        """
        if player not in self.players:
            raise GameError("Player not in game!")

        if cards is None:
            self.discardwhite.extend(self.playercards[player])
            self.playercards.clear()
        elif isinstance(cards, Iterable):
            self.discardwhite.extend(cards)
            self.playercards[player].difference_update(cards)
        else:
            self.discardwhite.append(cards)
            self.playercards[player].remove(cards)

    def round_start(self):
        """Start a round."""
        if self.inround:
            raise GameError("Attempting to start a round with one existing!")
        elif self.spent:
            raise GameError("Can't start a spent game!")
        elif self.suspended:
            raise GameConditionError("Game is suspended pending more players.")

        # No players should have leftover played cards
        # (they should be purged at the end of a round)
        # XXX broken because now it uses an OrderedDict not a defaultdict
        #assert [len(self.playerplay[player]) == 0 for player in self.players].count(False) == 0

        # Black card should be the null sentinel
        assert self.blackcard is None

        self.inround = True
        self.rounds += 1

        # The tsar is considered to have played, to simplify return logic
        self.playerlast[self.tsar] = self.rounds

        # Recycle the decks if need be
        self.card_refill()

        self.blackcard = self.blackcards.popleft()

        # Add cards to players' hands
        if self.blackcard.drawcount:
            for player in self.players:
                self.player_deal(player, self.blackcard.drawcount)

    def game_new_tsar(self, player=None):
        """Select a new tsar (without player, automatically)."""
        if player is not None and player not in self.players:
            raise GameError("Player not in the game!")

        if len(self.players) <= 1:
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

    def round_result(self, player=None):
        """Choose the result of a round. If player is omitted, it will choose
        it based on the rules.

        Please use round_end instead unless you know what you're doing.

        :returns:
            The results of the game.
        
        ..note::
            For voting rounds, this returns a two element tuple - the first
            element is the results tally; the second is a list of the results.
        """
        if player is not None and player not in self.players:
            raise GameError("Player not in the game!")

        if len(self.players) <= 1:
            if self.spent or self.suspended:
                return None

        def give_ap(player):
            self.ap[player] += self.ap_grant

        if player:
            # We have a result - chosen via tsar or fiat.
            if player == self.tsar:
                raise RuleError("Tsar can't declare himself result!")
            results = player
            give_ap(player)
        elif self.voting:
            # A voting round without a fiat-declared result.
            results = self.votes.most_common()
            top = results[0][1]  # Top result count

            # Give all winners AP
            for player, votes in results:
                if votes < top:
                    break

                give_ap(player)
        else:
            raise GameConditionError(
                "Player can't be None in a Tsar-based game")

        return results

    def round_end(self, player=None):
        """End a round and return round_result. Pass through a player to select
        the result the tsar picked.

        Be sure to check the spent member to see if the game is done; if
        it is, the game results are returned, instead.
        """
        if player is not None and player not in self.players:
            raise GameError("Player not in the game!")
        if not self.inround:
            raise GameError("Attempting to end a nonexistent round!")

        self.inround = False

        # Get the results
        results = self.round_result(player)

        # Discard the black card
        self.discardblack.append(self.blackcard)
        self.blackcard = None

        # Return played white cards to the discard pile and clear their played
        # cards, then give them new cards.
        for player in self.players:
            self.discardwhite.extend(self.playerplay.get(player, []))

            self.player_deal(player)

        self.playerplay.clear()

        # Reset votes
        self.voters.clear()
        self.votes.clear()

        # Reset the AP grant and gamblers
        self.ap_grant = 1
        self.gamblers.clear()

        # Check for end-of-game conditions
        if self.maxrounds is not None and self.rounds == self.maxrounds:
            return self.game_end()

        if self.maxap is not None:
            # Maximum AP earnt (first most common ((1)[0]) then [1] for the
            # tally.
            max = self.ap.most_common(1)[0][1]
            if max >= self.maxap:
                return self.game_end()

        # Choose the new tsar
        self.game_new_tsar()

        return results

    def game_end(self, forreal=False):
        """End the game.

        :param forreal:
            Purge the game, clearing all state, and returning the results.
            This will be none if there is <= 1 player.
        """
        self.suspended = True
        self.spent = True

        if self.inround:
            self.round_end()  # XXX discard the value?

        if len(self.players) <= 1:
            # Nobody wins. :|
            results = None
        else:
            # Find the results
            results = self.ap.most_common()

        # Clear the votes and AP
        self.votes.clear()
        self.ap.clear()
        self.ap_grant = 1
        self.gamblers.clear()

        # Clear the tsar
        self.tsar = None
        self.tsarindex = None

        self.rounds = 0

        if forreal:
            # Nuke the players
            for player in self.players:
                self.player_remove(player)

            # Wipe the decks
            self.blackcards.clear()
            self.whitecards.clear()
            self.discardblack.clear()
            self.discardwhite.clear()

            self.maxdraw = None
        else:
            # Clean up the players
            for player in self.players:
                self.player_clear(player)

            # Add the discard piles to the main decks
            self.blackcards.extend(self.discardblack)
            self.whitecards.extend(self.discardwhite)
            self.discardblack.clear()
            self.discardwhite.clear()

        return results
