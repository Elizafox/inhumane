import re
import sys

matcher = re.compile(r"(^.+?)(?:\s\(.*?([0-9]+)+?.+?(?:([0-9]+)?\))?)?$")
whmatch = re.compile(r"^(?:\s+)?$")

black = []
white = []
ref = black

template = "{text}\t{draw}\t{pick}\n"

with open(sys.argv[1], 'r') as f:
    for line in f.readlines():
        line = line.strip(' \n')

        if whmatch.match(line):
            # White phase
            ref = white
            continue

        text, a, b = matcher.match(line).groups()
        if a is None:
            draw, pick = 0, 1
        elif b is None:
            draw, pick = (0, a)
        else:
            draw, pick = (a, b)

        if ref == black:
            ref.append(template.format(**locals()))
        else:
            ref.append(text + '\n')

with open('white.txt', 'w') as f:
    f.writelines(white)

with open('black.txt', 'w') as f:
    f.writelines(black)
