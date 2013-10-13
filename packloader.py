# Copyright © 2013 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.

import json
import os

from card import Card, Deck

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

                black_cards.append(Card(*cinfo, iswhite=False))

        with open('white.txt', 'r') as f:
            for cinfo in f.readlines():
                cinfo = cinfo.rstrip('\n')

                white_cards.append(Card(cinfo))

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
print(default_packs[0].name)
