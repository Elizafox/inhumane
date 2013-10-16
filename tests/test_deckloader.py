# Copyright © 2013 Andrew Wilcox. All Rights Reserved
# Licensed according to the terms specified in LICENSE.

from inhumane.card import Deck
from inhumane import deckloader
import unittest
import os.path


class DeckLoaderTestCase(unittest.TestCase):
    def test_loading_a_deck(self):
        """ Load a deck we know exists """
        print(os.path.join(os.path.dirname(__file__), 'TestPack'))
        a_deck = deckloader.load_deck(os.path.join(os.path.dirname(__file__), 'TestPack'))
        self.assertIsInstance(a_deck, Deck)

    def test_loading_a_nonexistant_deck(self):
        """ Load a deck we know doesn't exist """
        self.assertRaises(FileNotFoundError, deckloader.load_deck, 'This pack does not exist')

