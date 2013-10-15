# Copyright © 2013 Andrew Wilcox. All Rights Reserved.

from inhumane.game import Game, GameError, RuleError
from inhumane.player import Player
from inhumane import deckloader
import os.path
import unittest


class GameParametersTestCase(unittest.TestCase):
    def test_unending_game(self):
        """ Ensure we can't start a game that won't end """
        with self.assertRaises(GameError):
            g = Game(name = 'Foo', maxrounds = None, maxap = None, decks = [])


class TradeCardsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """ Only load the decks for each game once. """
        cls._decks = deckloader.default_decks  #load_deck(os.path.join(os.path.dirname(__file__), 'TestPack'))

    def setUp(self):
        """ Initialise the game for each test. """
        self.fox = Player('awilfox')
        self.better_fox = Player('Missingno')
        self.game = Game(name = 'Trading Cards Test Game', decks = self._decks,
                         apxchg = (2, 4), players = [self.fox, self.better_fox])
        self.game.ap[self.fox] = 1
        self.game.ap[self.better_fox] = 5
        self.game.round_start()

    def test_more_than_limit(self):
        """ Ensure I can't trade more cards than allowed. """
        # just trade the whole damn hand
        with self.assertRaises(RuleError):
            self.game.player_trade_ap(self.better_fox,
                                      self.game.playercards[self.better_fox])

    def test_more_than_my_ap(self):
        """ Ensure I can't trade when I don't have the AP for it. """
        with self.assertRaises(RuleError):
            self.game.player_trade_ap(self.fox,
                                      self.game.playercards[self.fox][:2])

    def test_working_trade(self):
        """ Ensure I can trade when parameters are okay. """
        cards_to_trade = self.game.playercards[self.better_fox][:2]
        self.game.player_trade_ap(self.better_fox, cards_to_trade)
        self.assertNotIn(self.game.playercards[self.better_fox], cards_to_trade)

    def test_deck_exhaustion(self):
        """ Ensure I can't trade more cards than the deck has remaining. """
        # XXX TODO
        self.assertEqual(True, True)
