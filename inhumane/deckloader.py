# Copyright © 2013 Elizabeth Myers. All Rights reserved.
# Licensed according to the terms specified in LICENSE.

from pkg_resources import resource_listdir, resource_isdir, resource_exists
from pkg_resources import resource_stream, resource_string
from warnings import warn
from contextlib import contextmanager
import traceback
import json
import os

from .card import Card, Deck
from .game import BaseGameError

blackseen = dict()
whiteseen = dict()


class BaseDeckError(BaseGameError):
    pass

class DeckLoadError(BaseDeckError):
    pass

def __fix_path(path):
    if os.sep != '/':
        return path.replace('/', os.sep)
    else:
        return path

def __exists(path, bundled=False):
    if bundled:
        return resource_exists('inhumane', path)
    else:
        return os.path.exists(__fix_path(path))

def __isdir(path, bundled=False):
    if bundled:
        return resource_isdir('inhumane', path)
    else:
        return os.path.isdir(__fix_path(path))

def __listdir(path, bundled=False):
    if bundled:
        return resource_listdir('inhumane', path)
    else:
        return os.listdir(__fix_path(path))

def __load_str(path, bundled=False):
    if bundled:
        return resource_string('inhumane', path).decode('utf-8')
    else:
        with open(__fix_path(path), 'r') as f:
            load = f.read()
            return load

@contextmanager
def __load_stream(path, bundled=False):
    if bundled:
        with resource_stream('inhumane', path) as f:
            yield f
    else:
        with open(__fix_path(path)) as f:
            yield f

def load_deck(path, bundled=False):
    if not __exists(path, bundled):
        raise DeckLoadError("Deck '{d}' does not exist".format(d=path))

    pinfo = "{p}/info.txt".format(p=path)
    pblack = "{p}/black.txt".format(p=path)
    pwhite = "{p}/white.txt".format(p=path)

    if not __exists(pinfo, bundled):
        raise DeckLoadError("{}: pack contains no control information".format(path))

    blackcards = list()
    whitecards = list()

    info = json.loads(__load_str(pinfo, bundled))

    if __exists(pblack, bundled):
        with __load_stream(pblack, bundled) as f:
            for cinfo in f.readlines():
                if isinstance(cinfo, bytes):
                    cinfo = cinfo.decode('utf-8')
                cinfo = cinfo.rstrip().split('\t')
                cinfo[1], cinfo[2] = int(cinfo[1]), int(cinfo[2])

                global blackseen
                c = Card(*cinfo, iswhite=False)
                if c.text not in blackseen:
                    blackcards.append(c)
                    blackseen[c.text] = c
                else:
                    # Add to the watermark
                    blackseen[c.text].watermark += ", {w}".format(w=cinfo[3])

    if __exists(pwhite, bundled):
        with __load_stream(pwhite, bundled) as f:
            for cinfo in f.readlines():
                if isinstance(cinfo, bytes):
                    cinfo = cinfo.decode('utf-8')
                cinfo = cinfo.rstrip().split('\t')

                global whiteseen
                c = Card(*cinfo)
                if c.text not in whiteseen:
                    whitecards.append(c)
                    whiteseen[c.text] = c
                else:
                    # Add to the watermark
                    whiteseen[c.text].watermark += ", {w}".format(w=cinfo[1])

    if not (blackcards and whitecards):
        raise DeckLoadError("Deck has insufficient cards: {}".format(path))

    info.update({"blackcards": blackcards, "whitecards": whitecards})
    deck = Deck(**info)
    return deck


def load_decks(dir, bundled=False):
    decks = list()
    for d in __listdir(dir, bundled):
        d = "{basedir}/{pack}".format(basedir=dir, pack=d)
        if __isdir(d, bundled):
            decks.append(load_deck(d, bundled))

    return decks
try:
    default_decks = load_decks("packs", __name__ != '__main__')
except Exception as e:
    traceback.print_last()
    warn("Couldn't load default packs: {e}".format(e=str(e)))

