# -*- coding: UTF-8 -*-
from __future__ import print_function

import game, player, card
import packloader

g = game.Game('testblah', decks=packloader.default_packs)
p_missingno = player.Player('Missingno')
p_awilfox = player.Player('awilfox')
g.player_add(p_missingno)
g.player_add(p_awilfox)

g.round_start()

print("This round's black card:", g.blackplay.text)

try:
    g.player_play(p_missingno, g.player_cards(p_missingno)[0:g.blackplay.playcount])
except:
    print("CAUGHT - the tsar tried to play!")

print(g.blackplay.playcount)
print(g.player_cards(p_awilfox))
card = g.player_cards(p_awilfox)[0:g.blackplay.playcount]
print("awilfox is playing", [c.text for c in card])
g.player_play(p_awilfox,card)
g.round_end(p_awilfox)
print("Chose winner!")
print("awilfox AP:", g.player_get_ap(p_awilfox))

g.round_start()
print("Round", g.rounds)
print("This round's black card:", g.blackplay.text)
card = g.player_cards(p_missingno)[0:g.blackplay.playcount]
print("Missingno is playing", [c.text for c in card])
g.player_play(p_missingno,card)
g.round_end(p_missingno)
print("Chose winner!")
print("Missingno AP:", g.player_get_ap(p_missingno))

g.round_start()
print("Round", g.rounds)
print("This round's black card:", g.blackplay.text)
card = g.player_cards(p_awilfox)[0:g.blackplay.playcount]
print("awilfox is playing", [c.text for c in card])
g.player_play(p_awilfox,card)
g.round_end(p_awilfox)
print("Chose winner!")
print("awilfox AP:", g.player_get_ap(p_awilfox))

g.round_start()
print("Round", g.rounds)
print("The Tsar is", g.tsar.name)
g.player_remove(p_awilfox)
print("The Tsar left! Current Tsar is now", g.tsar.name)
