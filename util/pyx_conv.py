#!/usr/bin/python3
# pyx_conv.py - a crummy script to convert PYX databases to inhumane pack format
# Copyright © 2013 Elizabeth Myers. All rights reserved.
# License terms can be found in LICENSE.

import psycopg2
import bs4
import re
import os
import sys
import shutil
import json

whitespace = re.compile(r'\s+')

fmt = {'b': '*',
       'i': '/',
       'u': '_',
       'underline': '_',
       'br': ' / '}


def dehtmlify(string):
    soup = bs4.BeautifulSoup(string)

    for tname, rep in fmt.items():
        for t in soup.find_all(tname):
            strrep = t.string if t.string else ''

            if strrep:
                t.replace_with('{rep}{strrep}{rep}'.format(**locals()))
            else:
                t.replace_with(rep)

    return whitespace.sub(' ', soup.get_text())

if len(sys.argv) >= 2:
    path = sys.argv[1]
    if os.path.exists(path):
        if len(os.listdir(path)) > 0:
            print("Not overwriting directory!")
            quit(1)
    else:
        os.mkdir(path)

    os.chdir(path)
else:
    print("Current dir implied...")

conn = psycopg2.connect("dbname=pyx user=elizabeth")
cur = conn.cursor()

cur.execute("SELECT id, active, name, base_deck, description FROM card_set")
card_sets = cur.fetchall()

cur.execute("""SELECT text, draw, pick, watermark, card_set_id FROM black_cards
            INNER JOIN card_set_black_card ON black_cards.id =
            card_set_black_card.black_card_id""")
black_cards = cur.fetchall()

cur.execute("""SELECT text, watermark, card_set_id FROM white_cards INNER JOIN
            card_set_white_card ON white_cards.id =
            card_set_white_card.white_card_id""")
white_cards = cur.fetchall()

conn.close()

card_set = dict()
orig_dir = os.getcwd()
# Load all the card sets
for item in card_sets:
    (id, active, name, base, desc) = item

    # Cruft elimination
    name = name.replace('/', '-')
    name = name.replace('[CUSTOM] ', '')

    name = dehtmlify(name)

    if os.path.exists(name):
        shutil.rmtree(name)

    os.mkdir(name)
    os.chdir(name)

    with open('info.txt', 'w') as f:
        info = {'copyright': 'Unknown',
                'license': 'Creative Commons',
                'desc': desc,
                'name': name,
                'official': base,
                }
        json.dump(info, f, sort_keys=True, indent=4)

    os.chdir(orig_dir)

    card_set[id] = (active, name, base, desc)

# Black cards
for item in black_cards:
    (text, draw, pick, watermark, set_id) = item

    deck_active, deck_name, base, deck_desc = card_set[set_id]
    os.chdir(deck_name)

    # De-HTML-ify the text
    text = dehtmlify(text)

    with open('black.txt', 'a') as f:
        f.write(
            '{t}\t{d}\t{p}\t{w}\n'.format(
                t=text,
                d=draw,
                p=pick,
                w=watermark))

    os.chdir(orig_dir)

# White cards
for item in white_cards:
    (text, watermark, set_id) = item

    deck_active, deck_name, base, deck_desc = card_set[set_id]
    os.chdir(deck_name)

    text = dehtmlify(text)

    with open('white.txt', 'a') as f:
        f.write('{t}\t{w}\n'.format(t=text, w=watermark))

    os.chdir(orig_dir)
