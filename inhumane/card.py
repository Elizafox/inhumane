# Copyright © 2013-2015 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.


from threading import RLock


class Card(object):

    """The base object for cards.

    Stores the watermark(s) and card text."""

    _cid_count = 0
    _cid_lock = RLock()

    def __init__(self, text, watermark=()):
        """Create a card.

        args:
            text: text for the card
            watermark: watermark for the given card
        """
        self.text = text
        self.watermark = frozenset(watermark)

        with self._cid_lock:
            self.cid = self._cid_count
            self._cid_count += 1

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
        return hash((self.text, self.cid, self.watermark)) + 1

    def __str__(self):
        return self.text

    def __repr__(self):
        return "Card(text={0}, watermark={1})".format(self.text,
                                                      self.watermark)


class BlackCard(Card):

    """A black card.

    Stores the text, watermark(s), draw count, and play count.
    """

    def __init__(self, text, watermark=(), drawcount=0, playcount=1):
        """A black card.

        args:
            text: The text of the card.
            watermark: The watermarks of the card, as an iterable.
            drawcount: number of cards to draw when played (black only)
            playcount: number of cards to play when played (black only)

        """
        super().__init__(text, watermark)

        self.drawcount = drawcount
        self.playcount = playcount

    def __repr__(self):
        return ("BlackCard(text={0}, watermark={1}, drawcount={2}, "
                "playcount={3})").format(self.text, self.watermark,
                                         self.drawcount, self.playcount)

    def __hash__(self):
        obj = (self.text, self.cid, self.watermark, self.drawcount,
               self.playcount)
        return hash(obj) + 1


class WhiteCard(Card):
    """A white card."""
    pass

