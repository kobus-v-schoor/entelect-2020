#! /usr/bin/env python3

import json
import os
import sys
import math
import time
import sys

PLAYER = ['1', '2']
EMPTY_BLOCK = '░'
MUD_BLOCK = '▓'
BOOST_BLOCK = '»'
OIL_BLOCK = 'Φ'
OIL_SPILL = '█'
FINISH_LINE = '║'

BLOCKS = [EMPTY_BLOCK, MUD_BLOCK, OIL_SPILL, OIL_BLOCK, FINISH_LINE,
        BOOST_BLOCK]

rnd = 1
round_dir_fmt = 'Round {0:03}'
round_dir = round_dir_fmt.format(rnd)

hist = []

x_size = 1500
y_size = 4
track_map = [[' ' for _ in range(y_size)] for _ in range(x_size)]

# player view
blocks_behind = 5
blocks_ahead = 20

fps = 10
spr = 1 # seconds per round
round_delay = 0 # seconds delay after every round

def clear_line():
    sys.stdout.write('\r')
    sys.stdout.write('\033[K')

def one_line_up():
    sys.stdout.write('\033[F')

def clear_n_lines(n):
    for i in range(n):
        clear_line()
        if i + 1 != n:
            one_line_up()

def render_map(x, y, pos, state):
    print('id:', state['id'], 'y:', state['y'], 'x:', state['x'], 'speed:',
            state['speed'])
    for yb in range(y_size):
        print('[', end='')
        for xb in range(-blocks_behind, blocks_ahead + 1):
            if x + xb >= x_size:
                break
            if (x + xb, yb) in pos:
                print(PLAYER[pos[(x + xb, yb)]], end='')
            else:
                print(track_map[x + xb][yb], end='')
        print(']')
    print('boosts:', state['boosts'], 'oils:', state['oils'])
    print('state:', state['state'])
    print()

def clear_renders(renders):
    for _ in range(renders):
        clear_n_lines(9)

pwd = '.'
if len(sys.argv) > 1:
    pwd = sys.argv[1]

while os.path.isdir(os.path.join(pwd, round_dir)):
    with open(os.path.join(os.path.join(pwd, round_dir), 'GlobalState.json'),
            'r') as state_file:
        state = json.load(state_file)
    rnd += 1
    round_dir = round_dir_fmt.format(rnd)

    players = []
    for p in range(2):
        p = state['players'][p]
        player = {}
        player['x'] = p['position']['blockNumber']
        player['y'] = p['position']['lane']
        player['speed'] = p['speed']
        player['boosts'] = len([x for x in p['powerups'] if x == 'BOOST'])
        player['oils'] = len([x for x in p['powerups'] if x == 'OIL'])
        player['state'] = p['state']
        player['id'] = p['id']
        players.append(player)

    hist.append(players)

    player_count = len(players)

    if len(hist) == 1:
        continue

    for block in state['blocks']:
        x, y = block['position']['blockNumber'], block['position']['lane']
        track_map[x-1][y-1] = BLOCKS[block['surfaceObject']]

    if len(hist) > 2:
        clear_renders(len(pos))
    for frame in range(int(spr * fps)):
        pos = {} # holds all the positions of all the players
        players = {}
        prev = {}
        for idx in range(player_count):
            prev_x = hist[-2][idx]['x']
            nxt_x = hist[-1][idx]['x']

            nxt_y = int(hist[-1][idx]['y'])
            cur_x = math.floor((frame / (spr * fps) * (nxt_x - prev_x)) + prev_x)
            cur_x = int(cur_x)

            pk = (cur_x-1, nxt_y-1)
            pos[pk] = hist[-1][idx]['id']-1
            players[pk] = hist[-2][idx]
            prev[pk] = (prev_x, nxt_y)

        for p in pos:
            if round_delay:
                render_map(*prev[p], pos, players[p])
            else:
                render_map(*p, pos, players[p])
        time.sleep(1 / fps)
        if frame + 1 < spr * fps:
            clear_renders(len(pos))
    if round_delay:
        time.sleep(round_delay)
