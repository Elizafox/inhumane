# Copyright © 2013-2015 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.


import json
import os

from contextlib import contextmanager
from threading import RLock
from pkg_resources import (resource_listdir, resource_isdir, resource_exists,
                           resource_stream)

from .card import BlackCard, WhiteCard
from .contrib.orderedset import OrderedSet


class PackLoadError(Exception):
    """Error raised when a pack cannot be loaded."""



class BasePack(object):

    """This object stores all the given cards (white and black) and metadata
    for a given pack.

    It can be passed to the Game instance.

    """

    def __init__(self, path):
        self.path = path

        self.whitecards = OrderedSet()
        self.blackcards = OrderedSet()

        self.name = None
        self.license = None
        self.copyright = None
        self.desc = None
        self.official = None

        self.maxplay = 0
        self.maxdraw = 0

    def _formatpath(self, path): raise NotImplementedError
    def _isdir(self, path): raise NotImplementedError
    def _listdir(self, path): raise NotImplementedError
    def _exists(self, path): raise NotImplementedError

    @contextmanager
    def _open(self, filename): raise NotImplementedError

    def load_info(self):
        with self._open("/info.txt") as f:
            info = json.loads(f.read().decode("utf-8", "replace"))

        self.name = info["name"]
        self.license = info.get("license", "Unknown")
        self.copyright = info.get("copyright", "Unknown")
        self.desc = info.get("desc", "")
        self.official = info.get("official", False)

    def load_black(self):
        if not self._exists("/black.txt"):
            return False

        with self._open("/black.txt") as f:
            for cardinfo in f.readlines():
                if isinstance(cardinfo, bytes):
                    cardinfo = cardinfo.decode("utf-8", "replace")

                cardinfo = cardinfo.rstrip().split("\t")

                # Draw information
                cardinfo[1], cardinfo[2] = int(cardinfo[1]), int(cardinfo[2])

                text = cardinfo[0]
                drawcount = cardinfo[1]
                playcount = cardinfo[2]
                watermark = cardinfo[3] if len(cardinfo) >= 4 else ''

                if drawcount > self.maxdraw:
                    self.maxdraw = drawcount

                if playcount > self.maxplay:
                    self.maxplay = playcount

                c = BlackCard(text, watermark, drawcount, playcount)
                # TODO warn on dupes
                self.blackcards.add(c)

        return True

    def load_white(self):
        if not self._exists("/white.txt"):
            return False

        with self._open("/white.txt") as f:
            for cardinfo in f.readlines():
                if isinstance(cardinfo, bytes):
                    cardinfo = cardinfo.decode("utf-8", "replace")

                cardinfo = cardinfo.rstrip().split("\t")

                text = cardinfo[0]
                watermark = cardinfo[1] if len(cardinfo) > 1 else ''

                c = WhiteCard(text, watermark)
                # TODO warn on dupes
                self.whitecards.add(c)

        return True

    def load_all(self):
        self.load_info()
        if not any((self.load_black(), self.load_white())):
            raise PackLoadError("Blank pack")

    @classmethod
    def load(cls, path):
        p = cls(path)
        p.load_all()
        return p

    @classmethod
    def discover(cls, path):
        # Dummy object so _listdir works
        dummy = cls(path)
        return [cls.load(dummy._formatpath(p)) for p in dummy._listdir('') if
                dummy._isdir(p)]

    def __repr__(self):
        return ("Pack(name={0}, blackcards=<{1} cards>, whitecards=<{2} cards>, "
                "copyright={3}, license={4}, desc={5}, official={6})").format(
                    self.name, len(self.blackcards), len(self.whitecards),
                    self.copyright, self.license, self.desc, self.official)


class BuiltinPack(BasePack):

    """The pack object for builtin (package) packs."""

    def _formatpath(self, path):
        return "{0}/{1}".format(self.path, path)

    def _isdir(self, path):
        return resource_isdir(__name__, self._formatpath(path))

    def _listdir(self, path):
        return resource_listdir(__name__, self._formatpath(path))

    def _exists(self, path):
        return resource_exists(__name__, self._formatpath(path))

    @contextmanager
    def _open(self, filename):
        with resource_stream(__name__, self._formatpath(filename)) as f:
            yield f


basepacks = BuiltinPack.discover("packs")


class ExternalPack(BasePack):

    """The pack object for external (non-package) packs."""

    def __init__(self, path):
        if os.sep != "/":
            # XXX probably wrong but it's good enough
            path = path.replace("/", os.sep)

        super().__init__(path)

    def _formatpath(self, path):
        return os.path.join(self.path, path)

    def _isdir(self, path):
        return os.path.isdir(self._formatpath(path))

    def _listdir(self, path):
        return os.listdir(self._formatpath(path))

    def _exists(self, path):
        return os.path.exists(self._formatpath(path))

    @contextmanager
    def _open(self, filename):
        with open(self._formatpath(filename), "r") as f:
            yield f


class Deck(object):

    """The entire deck, containing packs.

    Dupes are filtered out optionally."""

    def __init__(self, packs, dupes=False):
        self.packs = packs
        self.dupes = dupes

        self.whitecards = OrderedSet()
        self.blackcards = OrderedSet()

        self.maxdraw = 0
        self.maxplay = 0

        for pack in packs:
            self._do_white(pack)
            self._do_black(pack)

            if pack.maxdraw > self.maxdraw:
                self.maxdraw = pack.maxdraw

            if pack.maxplay > self.maxplay:
                self.maxplay = pack.maxplay

        if not (self.whitecards or self.blackcards):
            raise PackLoadError("No cards in deck")

    def _do_white(self, pack):
        t_white = dict()

        # Dupe filtering and watermark stuff
        for card in pack.whitecards:
            if card.text in t_white and not self.dupes:
                # Update watermark
                watermark = list(t_white[card.text].watermark)
                watermark.append(card.watermark)
                card = WhiteCard(card.text, watermark)

            t_white[card.text] = card

        for card in t_white.values():
            self.whitecards.add(card)

    def _do_black(self, pack):
        t_black = dict()

        # Dupe filtering and watermark stuff
        for card in pack.blackcards:
            if card.text in t_black and not self.dupes:
                watermark = list(t_black[card.text].watermark)
                watermark.append(card.watermark)
                card = BlackCard(card.text, watermark, card.drawcount,
                                 card.playcount)

            t_black[card.text] = card

        for card in t_black.values():
            self.blackcards.add(card)

