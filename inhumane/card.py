# Copyright © 2013 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.

from threading import RLock
from itertools import chain

from .contrib.orderedset import OrderedSet


ccounter = 0
_cc_lock = RLock()


class Deck(object):

    """ This object stores all the given cards (white and black) and metadata
    for a given deck. It can be passed to the Game instance. """

    def __init__(self, name, blackcards, whitecards, copyright="Unknown",
                 license="Unknown", desc='', official=False):
        """ Initalise a deck object, containing white and black cards and
        metadata,

        args:
            name: name of the deck
            blackcards: black cards (Card objects) (must be an iterable)
            whitecards: white cards (Card objects) (must be an iterable)
            copyright: who created/owns the copyright on this deck
            license: what is the license of the deck
            desc: description of the deck
            official: is it an official Cards Against Humanity™ deck?
        """

        assert blackcards or whitecards, "No cards!"

        self.name = name
        self.blackcards = OrderedSet(blackcards)
        self.whitecards = OrderedSet(whitecards)

        self.license = license
        self.copyright = copyright
        self.desc = desc
        self.official = official

        self.hash = None  # Cached hash value

        for card in chain(self.blackcards, self.whitecards):
            card.deck = self

        # Calculate the max draw/play cards for this deck
        maxdraw = 0
        maxplay = 0
        for n in self.blackcards:
            if n.drawcount > maxdraw:
                maxdraw = n.drawcount
            if n.playcount > maxplay:
                maxplay = n.playcount

        self.maxdraw = maxdraw
        self.maxplay = maxplay

    def __repr__(self):
        return ("Deck(name={n}, black cards={b}, white cards={w}, "
                "copyright={c}, license={l}, desc={d}, official={o})").format(
                    n=self.name, b=len(self.blackcards),
                    w=len(self.whitecards), c=self.copyright, l=self.license,
                    d=self.desc, o=str(self.official))

    def __hash__(self):
        if self.hash is not None:
            return self.hash

        hashval = hash(self.blackcards[0])
        for i, b in enumerate(self.blackcards[1:]):
            hashval ^= hash(b) << (i % 48)

        for i, w in enumerate(self.whitecards):
            hashval ^= hash(w) << (i % 48)

        hashval ^= repr(self)
        self.hash = hashval
        return self.hash


class Card(object):

    """ This contains a single card (white or black). It contains what deck it's
    in (initalised to None until added to a deck), the text of the card,
    the watermark, and whether or not it's white. It also stores play count and
    draw count for white cards.

    Note without a deck, a card is useless.
    """

    def __init__(
            self, text, drawcount=0, playcount=1, watermark='', iswhite=True):
        """ Create a card.

        args:
            text: text for the card
            drawcount: number of cards to draw when played (black only)
            playcount: number of cards to play when played (black only)
            watermark: watermark for the given card
            iswhite: whether or not the card is white (default True)
        """
        self.deck = None
        self.text = text
        self.watermark = watermark

        # These two aren't used for white cards
        if not iswhite:
            self.drawcount = drawcount
            self.playcount = playcount

        self.iswhite = iswhite

        with _cc_lock:
            global ccounter
            self.cid = ccounter
            ccounter += 1

    def __eq__(self, other):
        return self.text == other.text

    def __gt__(self, other):
        return self.text > other.text

    def __lt__(self, other):
        return self.text < other.text

    def __ge__(self, other):
        return self.text >= other.text

    def __le__(self, other):
        return self.text <= other.text

    def __ne__(self, other):
        return self.text != other.text

    def __hash__(self):
        h = hash(self.text) ^ hash(self.iswhite)
        if not self.iswhite:
            h ^= hash(self.drawcount) << 32
            h ^= hash(self.playcount) << 64

        return h

    def __str__(self):
        return self.text

    def __repr__(self):
        return "Card({c}, cid={i}, deck={d})".format(
            c=self.text, i=self.cid, d=self.deck)
