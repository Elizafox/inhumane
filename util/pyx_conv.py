#!/usr/bin/python3
# pyx_conv.py - a crummy script to convert PYX databases to inhumane pack format
# Copyright © 2013 Elizabeth Myers. All rights reserved.
# License terms can be found in LICENSE.

from collections import defaultdict
import psycopg2
import bs4
import re
import os
import shutil
import json

whitespace = re.compile(r'\s+')

fmt = {'b' : '*',
       'i' : '/',
       'u' : '_',
       'underline' : '_',
       'br' : ' / '}

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

conn = psycopg2.connect("dbname=pyx user=elizabeth")
cur = conn.cursor()

cur.execute("select * from black_cards")
black_all = cur.fetchall()

cur.execute("select * from white_cards")
white_all = cur.fetchall()

cur.execute("select * from card_set")
card_sets = cur.fetchall()

cur.execute("select * from card_set_black_card")
black_to_set = cur.fetchall()

cur.execute("select * from card_set_white_card")
white_to_set = cur.fetchall()

conn.close()

# Create ID to card maps
black_map = dict()
white_map = dict()
for x in black_all:
    id, text, draw, pick, watermark = x
    black_map[id] = (text, draw, pick, watermark)

for x in white_all:
    id, text, watermark = x
    white_map[id] = (text, watermark)

# ID to names/descs
id_to_set = dict()

# Create control info for the card sets and the dirs needed
orig_dir = os.getcwd()
for x in card_sets:
    id, active, name, base_deck, desc, weight = x
    name = name.replace('/', '-')
    name = name.replace('[CUSTOM] ', '')

    if os.path.exists(name):
        shutil.rmtree(name)

    os.mkdir(name)
    os.chdir(name)

    with open('info.txt', 'w') as f:
        info = {'copyright' : 'Unknown',
                'license' : 'Creative Commons',
                'desc' : desc,
                'name' : name,
                'official' : base_deck,
               }
        json.dump(info, f, sort_keys=True, indent=4)

    os.chdir(orig_dir)

    id_to_set[id] = (name, desc)

# Black cards formatting
for x in black_to_set:
    set_id, card_id = x

    name, desc = id_to_set[set_id]
    os.chdir(name)

    text, draw, pick, watermark = black_map[card_id]

    # De-HTML-ify the text
    text = dehtmlify(text)

    with open('black.txt', 'a') as f:
        f.write('{t}\t{d}\t{p}\t{w}\n'.format(t=text, d=draw, p=pick, w=watermark))

    os.chdir(orig_dir)

# White cards formatting
for x in white_to_set:
    set_id, card_id = x

    name, desc = id_to_set[set_id]
    os.chdir(name)

    text, watermark = white_map[card_id]
    text = dehtmlify(text)

    with open('white.txt', 'a') as f:
        f.write('{t}\t{w}\n'.format(t=text, w=watermark))

    os.chdir(orig_dir)

