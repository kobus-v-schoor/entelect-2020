#! /usr/bin/env python3

# calculates the distribution of block types
# run in match logs' final round folder

import json

blocks = []

with open('GlobalState.json', 'r') as f:
    state = json.load(f)

    for block in state['blocks']:
        blocks.append(block['surfaceObject'])

print('empty:', round(len([b for b in blocks if b == 0]) / len(blocks), 2))
print('mud:', round(len([b for b in blocks if b == 1]) / len(blocks), 2))
print('oil:', round(len([b for b in blocks if b == 3]) / len(blocks), 2))
print('boost:', round(len([b for b in blocks if b == 5]) / len(blocks), 2))
