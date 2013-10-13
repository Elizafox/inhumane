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
    p_missingno.play(p_missingno.cards[0])
except:
    print("CAUGHT - the tsar tried to play!")

card = p_awilfox.cards[0]
print("awilfox is playing", card.text)
p_awilfox.play(card)
g.choose_winner(p_awilfox)
print("Chose winner!")
print("awilfox AP:", p_awilfox.ap)

g.start_round()
print("Round", g.rounds)
print("This round's black card:", g.black_play.text)
card = p_missingno.cards[0]
print("Missingno is playing", card.text)
p_missingno.play(card)
g.choose_winner(p_missingno)
print("Chose winner!")
print("Missingno AP:", p_missingno.ap)

g.start_round()
print("Round", g.rounds)
print("This round's black card:", g.black_play.text)
card = p_awilfox.cards[0]
print("awilfox is playing", card.text)
p_awilfox.play(card)
g.choose_winner(p_awilfox)
print("Chose winner!")
print("awilfox AP:", p_awilfox.ap)

g.start_round()
print("Round", g.rounds)
print("The Tsar is", g.tsar.name)
g.remove_player(p_awilfox)
print("The Tsar left! Current Tsar is now", g.tsar.name)
