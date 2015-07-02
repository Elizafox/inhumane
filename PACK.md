# The structure of packs

Packs are in a very simple text file, designed to be human editable (at least,
in a sensible editor). There's not really a lot to say about the design, given
it is intended to be very simple. About the only thing of note is that it has
been partially inspired by PYX, but is not an SQL format.

## Structure

Each pack is a directory containing three plaintext files:

- `info.txt` (control information)
- `white.txt` (white cards)
- `black.txt` (black cards)

All of the files are to be encoded and interpreted as UTF-8. No other encodings
are permissible, for interoperability reasons. Users of alternate encodings
should be punished in the most culturally ironic way possible (for KOIR-8 users,
a literal Iron Curtain should be dropped on them; for Shift-JIS users, they
should be slashed with a katana; GB and Big5 users should be punished with a
death by a thousand cuts; Windows-1252 users should be punished by
defenestration; UTF-16 users should have UTF surrogates embedded into their
reproductive organs; and so on).

### Information file
`info.txt` is a file written in JSON, containing metadata about the pack. It is
a single dictionary. The presently parsed keys and their values are as follows:

| Key       | Description             | Data type | Default | Info        |
|-----------|-------------------------|-----------|---------|-------------|
| copyright | The copyright owner     | string    | Unknown | Recommended |
| desc      | Description of the pack | string    |         | Recommended |
| license   | The license of the pack | string    | Unknown | Recommended |
| name      | The name of the pack    | string    |         | Required    |
| official  | An official CAH pack    | boolean   | false   | Optional    |

Keys may be added in the future if required. Unknown keys are simply ignored.

### White cards
`white.txt` contains a list of cards and their watermarks. The watermarks are
a holdover from PYX, and are entirely optional. They are an abbreviation for
what deck the card originates from. The format is thus:

`<freeform card text> [<tab> <watermark>]`

### Black cards
`black.txt` contains a list of cards, their watermarks, their pick count, and
their draw count. Note the draw count should never exceed the pick count. The
normal Cards Against Humanity rules should still apply, so even if draw is set
to 0, players should be drawn back to 10. As with the white cards, the
watermark is optional. The format is as follows:

`<freeform card text> <tab> <draw> <tab> <pick> [<tab> <watermark>]`

#### Intermezzo: why black cards have a draw count
Some cards have a draw X on them. For typical cards, this is draw 2/pick 3 (in
the official decks). Some purists have suggested I only support this rule. I
generally believe in flexibility, and in any case, I want to ensure
compatibility with PYX decks that do weird things. Therefore, I will not remove
this feature. Don't even ask. It's here to stay.
