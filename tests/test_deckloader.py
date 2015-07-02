# Copyright © 2013 Andrew Wilcox. All Rights Reserved
# Licensed according to the terms specified in LICENSE.

# NB - this test is known broken!

from inhumane.card import Deck
from inhumane import deckloader
from inhumane.deckloader import DeckLoadError
import unittest
import os.path


class DeckLoaderTestCase(unittest.TestCase):

    def test_loading_a_deck(self):
        """Load a deck we know exists."""
        deckpath = os.path.join(os.path.dirname(__file__), 'TestPack')
        a_deck = deckloader.load_deck(deckpath)
        self.assertIsInstance(a_deck, Deck)

    def test_loading_a_nonexistant_deck(self):
        """Load a deck we know doesn't exist."""
        self.assertRaises(DeckLoadError, deckloader.load_deck, "shittydeck")
