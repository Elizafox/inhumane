# Copyright © 2013 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.

import six

from threading import RLock
from itertools import chain

from orderedset import OrderedSet

ccounter = 0
_cc_lock = RLock()

class Deck(object):
    def __init__(self, name, black_cards, white_cards, copyright='Unknown',
                 license='Unknown', desc='', official=False):
        assert black_cards and white_cards

        self.name = name
        self.black_cards = black_cards
        self.white_cards = white_cards

        self.license = license
        self.copyright = copyright
        self.desc = desc
        self.official = official

        map(lambda card : card.set_deck(self),
            chain(self.black_cards, self.white_cards))

        maxdraw = 0
        maxplay = 0
        for n in self.black_cards:
            if n.drawcount > maxdraw: maxdraw = n.drawcount
            if n.playcount > maxplay: maxplay = n.playcount

        self.maxdraw = maxdraw
        self.maxplay = maxplay


class Card(object):
    def __init__(self, text, drawcount=0, playcount=1, watermark='', iswhite=True):
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

    def set_deck(self, deck):
        # XXX shoddy workaround
        self.deck = deck

    def __eq__(self, other):
        return self.deck == other.deck and self.text == other.text

    def __hash__(self):
        h = hash(self.text) ^ hash(self.iswhite) ^ hash(self.cid) 
        if not self.iswhite:
            h ^= hash(self.drawcount) << 32
            h ^= hash(self.playcount) << 64

        return h

    def __str__(self):
        return self.text

    def __repr__(self):
        return "Card({c}, cid={i}, deck={d})".format(c=self.text, i=self.cid, d=self.deck)


