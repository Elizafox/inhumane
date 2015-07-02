# TODO

Things I'd like to, well, do.

Architecture
============

Many of these issues stem from the fact I made this thing years ago and I
hadn't read PEP8 or such. I also hadn't had much chance to read other people's
code. Hindsight is 20/20.

- [ ] Revisit the way decks are loaded (it's kind of a mess).
- [ ] Revisit the player object (it's bloody half-mutable!)
- [ ] Card should be subclassed into BlackCard and WhiteCard.
- [ ] Nomenclature/mere existence of many functions is really dumb! (What /was/
    I thinking with card\_black()?)
- [ ] Easier indexing of players and turns.
- [ ] Deck stuff might want to be moved out of the card module(?).
- [ ] More checking of the rules
- [ ] Evaluate usage of GameError vs RuleError.
- [ ] A better interface to get the AP of all players (players without any AP
    are presently not counted).

Docs
====

The docs are complete-ish but need work.

- [ ] I'd really like to redo them all in reST.
- [ ] Document the members of Game.
- [ ] Document the members of Card.
- [ ] Document the members of Deck.
- [ ] Properly document the procedure for creating decks.

Bugs
====

- [ ] Watermarks are buggy as fuck. They should ideally be a list or a set also.
