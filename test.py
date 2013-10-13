# -*- coding: UTF-8 -*-
from __future__ import print_function

import game, player, card
import packloader

g = game.Game('testblah', decks=packloader.default_packs)
p_missingno = player.Player('Missingno')
p_awilfox = player.Player('awilfox')
g.add_player(p_missingno)
g.add_player(p_awilfox)

g.start_round()

print("This round's black card:", g.black_play.text)

try:
    p_missingno.play(p_missingno.cards[0:g.black_play.playcount])
except:
    print("CAUGHT - the tsar tried to play!")

print(g.black_play.playcount)
print(p_awilfox.cards)
card = p_awilfox.cards[0:g.black_play.playcount]
print("awilfox is playing", [c.text for c in card])
p_awilfox.play(card)
g.choose_winner(p_awilfox)
print("Chose winner!")
print("awilfox AP:", p_awilfox.ap)

g.start_round()
print("Round", g.rounds)
print("This round's black card:", g.black_play.text)
card = p_missingno.cards[0:g.black_play.playcount]
print("Missingno is playing", [c.text for c in card])
p_missingno.play(card)
g.choose_winner(p_missingno)
print("Chose winner!")
print("Missingno AP:", p_missingno.ap)

g.start_round()
print("Round", g.rounds)
print("This round's black card:", g.black_play.text)
card = p_awilfox.cards[0:g.black_play.playcount]
print("awilfox is playing", [c.text for c in card])
p_awilfox.play(card)
g.choose_winner(p_awilfox)
print("Chose winner!")
print("awilfox AP:", p_awilfox.ap)

g.start_round()
print("Round", g.rounds)
print("The Tsar is", g.tsar.name)
g.remove_player(p_awilfox)
print("The Tsar left! Current Tsar is now", g.tsar.name)