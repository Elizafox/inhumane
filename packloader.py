# Copyright © 2013 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.

import json
import os

from card import Card, Deck

black_seen = dict()
white_seen = dict()

def load_deck(pack):
    cur = os.getcwd()
    os.chdir(pack)
    try:
        with open('info.txt', 'r') as f:
            info = json.load(f)

        black_cards = list()
        white_cards = list()

        with open('black.txt', 'r') as f:
            for cinfo in f.readlines():
                cinfo = cinfo.rstrip('\n')
                cinfo = cinfo.split('\t')
                cinfo[1], cinfo[2] = int(cinfo[1]), int(cinfo[2])

                global black_seen
                c = Card(*cinfo, iswhite=False)
                if c.text not in black_seen:
                    black_cards.append(c)
                    black_seen[c.text] = c
                else:
                    # Add to the watermark
                    black_seen[c.text].watermark += ', {w}'.format(w=cinfo[3])

        with open('white.txt', 'r') as f:
            for cinfo in f.readlines():
                cinfo = cinfo.rstrip('\n')
                cinfo = cinfo.split('\t')

                global white_seen
                c = Card(*cinfo)
                if c.text not in white_seen:
                    white_cards.append(c)
                    white_seen[c.text] = c
                else:
                    # Add to the watermark
                    white_seen[c.text].watermark += ', {w}'.format(w=cinfo[1])

        info.update({'black_cards' : black_cards, 'white_cards' : white_cards})

        deck = Deck(**info)
    finally:
        os.chdir(cur)

    return deck

def load_packs(dir):
    try:
        cur = os.getcwd()
        os.chdir(dir)
        packs = [load_deck(x) for x in os.listdir('.') if os.path.isdir(x)]
    finally:
        os.chdir(cur)

    return packs

default_packs = load_packs('packs')

del black_seen
del white_seen
