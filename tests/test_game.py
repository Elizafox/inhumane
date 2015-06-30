# Copyright © 2013 Andrew Wilcox. All Rights Reserved.

from inhumane.game import Game, GameError, RuleError
from inhumane.player import Player
from inhumane import deckloader
from math import ceil
import os.path
import random
import unittest


def create_players_helper():
    return [Player('Missingno'), Player('awilfox'), Player('MidnightCommando'),
            Player('SilverWoof'), Player('appledash')]


class GameParametersTestCase(unittest.TestCase):

    def test_unending_game(self):
        """ Ensure we can't start a game that won't end """
        with self.assertRaises(GameError):
            g = Game(name='Foo', maxrounds=None, maxap=None, decks=[])


class FinishGameByAPTestCase(unittest.TestCase):

    def test(self):
        """ Ensures that we can finish a game using maxap. """
        decks = deckloader.default_decks
        better_fox, fox, stallion, derpy_dog, derpy_pony = player_list = create_players_helper()
        ap_to_test = 40
        game = Game(name='Max AP Test Game', decks=decks,
                    maxap=ap_to_test, players=player_list)

        for next_round in range(0, ap_to_test + 1 + int(ceil(ap_to_test / 5))):
            game.round_start()
            if (next_round + 1) % 5 == 0:
                game.player_play(
                    derpy_dog,
                    game.playercards[derpy_dog][
                        0:game.card_black().playcount])
                game.round_end(derpy_dog)
            else:
                game.player_play(
                    better_fox,
                    game.playercards[better_fox][
                        0:game.card_black().playcount])
                game.round_end(better_fox)

        self.assertTrue(game.spent)


class FinishGameByRoundsTestCase(unittest.TestCase):

    def test(self):
        """ Ensures that we can finish a game using maxrounds. """
        decks = deckloader.default_decks
        better_fox, fox, stallion, derpy_dog, derpy_pony = create_players_helper()
        player_list = set([better_fox, fox, stallion, derpy_dog, derpy_pony])
        rounds_to_test = 20
        game = Game(name='Max Rounds Test Game', decks=decks,
                    maxrounds=rounds_to_test, players=player_list)
        for next_round in range(0, rounds_to_test):
            game.round_start()
            winner = random.choice(list(player_list.difference([game.tsar])))
            game.player_play(
                winner,
                game.playercards[winner][
                    0:game.card_black().playcount])
            game.round_end(winner)
        self.assertTrue(game.spent)


class TradeCardsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """ Only load the decks for each game once. """
        # below was load_deck(os.path.join(os.path.dirname(__file__), 'TestPack'))
        cls._decks = deckloader.default_decks

    def setUp(self):
        """ Initialise the game for each test. """
        assert self._decks and len(self._decks) > 0
        self.fox = Player('awilfox')
        self.better_fox = Player('Missingno')
        self.game = Game(name='Trading Cards Test Game', decks=self._decks,
                         apxchg=(2, 4), players=[self.fox, self.better_fox])
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
        for card in cards_to_trade:
            self.assertNotIn(card, self.game.playercards[self.better_fox])

    def test_deck_exhaustion(self):
        """ Ensure I can't trade more cards than the deck has remaining. """
        # XXX TODO
        self.assertEqual(True, True)
