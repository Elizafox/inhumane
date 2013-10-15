# Copyright © 2013 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.

from warnings import warn
import json
import os

from .card import Card, Deck

blackseen = dict()
whiteseen = dict()

def load_deck(pack):
    cur = os.getcwd()
    os.chdir(pack)
    try:
        with open('info.txt', 'r') as f:
            info = json.load(f)

        blackcards = list()
        whitecards = list()

        with open('black.txt', 'r') as f:
            for cinfo in f.readlines():
                cinfo = cinfo.rstrip('\n')
                cinfo = cinfo.split('\t')
                cinfo[1], cinfo[2] = int(cinfo[1]), int(cinfo[2])

                global blackseen
                c = Card(*cinfo, iswhite=False)
                if c.text not in blackseen:
                    blackcards.append(c)
                    blackseen[c.text] = c
                else:
                    # Add to the watermark
                    blackseen[c.text].watermark += ', {w}'.format(w=cinfo[3])

        with open('white.txt', 'r') as f:
            for cinfo in f.readlines():
                cinfo = cinfo.rstrip('\n')
                cinfo = cinfo.split('\t')

                global whiteseen
                c = Card(*cinfo)
                if c.text not in whiteseen:
                    whitecards.append(c)
                    whiteseen[c.text] = c
                else:
                    # Add to the watermark
                    whiteseen[c.text].watermark += ', {w}'.format(w=cinfo[1])

        info.update({'blackcards' : blackcards, 'whitecards' : whitecards})

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

try:
    default_packs = load_packs('packs')
except Exception as e:
    warn("Couldn't load default packs: {e}".format(e=str(e)))

del blackseen
del whiteseen
