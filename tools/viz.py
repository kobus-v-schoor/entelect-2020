#! /usr/bin/env python3

import os
import sys
import enum
import json
import time

## settings ##

x_size = 1500
y_size = 4
x_behind = 5
x_ahead = 20

fps = 15
rps = 1 # rounds per second
delay = 0 # insert delay after every round
lift_fow = True # lifts the fog of war so that x_ahead blocks are always shown
manual = True # manually control round transitions

class Block(enum.Enum):
    EMPTY = 0
    MUD = 1
    OIL_SPILL = 2
    OIL_ITEM = 3
    FINISH_LINE = 4
    BOOST = 5
    WALL = 6
    LIZARD = 7
    TWEET = 8
    EMP = 9

    CYBERTRUCK = 100

block_renders = {
    Block.EMPTY: '░',
    Block.MUD: '▓',
    Block.OIL_SPILL: '█',
    Block.OIL_ITEM: 'Φ',
    Block.FINISH_LINE: '║',
    Block.BOOST: '»',
    Block.WALL: '#',
    Block.LIZARD: '∱',
    Block.TWEET: 'T',
    Block.EMP: '*',
    Block.CYBERTRUCK: 'C',
}

max_speed = [15, 9, 8, 6, 3, 0]

if len(sys.argv) > 1:
    match_dir = sys.argv[1]
else:
    match_dir = os.getcwd()

files = list(os.listdir(match_dir))
players = sorted([p[:-4] for p in files if p.endswith('.csv')])
rounds = sorted([p for p in files if p.startswith('Round')])

framebuffer = []

def read_state(cur_round, next_round, player):
    state_file = os.path.join(match_dir, cur_round, player, 'JsonMap.json')
    with open(state_file, 'r') as f:
        cur_state = json.load(f)

    if next_round is not None:
        state_file = os.path.join(match_dir, next_round, player,
                                  'JsonMap.json')
        with open(state_file, 'r') as f:
            next_state = json.load(f)
    else:
        state_file = os.path.join(match_dir, cur_round, 'GlobalState.json')
        with open(state_file, 'r') as f:
            next_state = json.load(f)


    def extract_pos(state):
        pos = lambda s: (state[s]['position']['x'], state[s]['position']['y'])
        return {
            state['player']['id']: pos('player'),
            state['opponent']['id']: pos('opponent'),
        }

    def end_extract_pos(state):
        pos = {}
        for player in state['players']:
            pos[player['id']] = (player['position']['blockNumber'],
                                 player['position']['lane'])
        return pos

    players_start = extract_pos(cur_state)
    if next_round is not None:
        players_end = extract_pos(next_state)
    else:
        players_end = end_extract_pos(next_state)

    track_map = {}
    max_x = -1

    for lane in cur_state['worldMap']:
        for block in lane:
            x = block['position']['x']
            y = block['position']['y']
            pos = (x, y)
            max_x = max(max_x, x)
            track_map[pos] = block_renders[Block(block['surfaceObject'])]

            if block.get('isOccupiedByCyberTruck', False):
                track_map[pos] = block_renders[Block.CYBERTRUCK]

    if lift_fow and next_round is not None:
        upto_x = players_end[cur_state['player']['id']][0] + x_ahead

        for lane in next_state['worldMap']:
            for block in lane:
                x = block['position']['x']
                y = block['position']['y']
                pos = (x, y)

                if x < max_x:
                    continue
                if x > upto_x:
                    break

                track_map[pos] = block_renders[Block(block['surfaceObject'])]

                if block.get('isOccupiedByCyberTruck', False):
                    track_map[pos] = block_renders[Block.CYBERTRUCK]

    info = {}
    info['name'] = player
    info['id'] = cur_state['player']['id']
    info['score'] = cur_state['player']['score']
    info['speed'] = cur_state['player']['speed']
    info['state'] = cur_state['player']['state']
    info['damage'] = cur_state['player'].get('damage', 0)
    info['max speed'] = max_speed[min(len(max_speed)-1, info['damage'])]
    info['powerups'] = {
        'oils': cur_state['player']['powerups'].count('OIL'),
        'boosts': cur_state['player']['powerups'].count('BOOST'),
        'lizards': cur_state['player']['powerups'].count('LIZARD'),
        'tweets': cur_state['player']['powerups'].count('TWEET'),
        'emps': cur_state['player']['powerups'].count('EMP'),
    }
    info['boosting'] = cur_state['player']['boosting']
    info['boostcount'] = cur_state['player']['boostCounter']

    cmd = {}
    cmd_file = os.path.join(match_dir, cur_round, player, 'PlayerCommand.txt')
    with open(cmd_file, 'r') as f:
        for line in f.readlines():
            line = line.strip()

            if line.startswith('Command:'):
                cmd['cmd'] = line[9:]
            elif line.startswith('Execution time:'):
                cmd['exec_time'] = line[16:]

    return {
        'map': track_map,
        'info': info,
        'cmd': cmd,
        'start': players_start,
        'end': players_end,
    }

def render(state, frame_prog):
    add = lambda line: framebuffer.append(line)

    add(f"{state['info']['name']} (id: {state['info']['id']}, score: "
        f"{state['info']['score']})")

    pid = state['info']['id']
    start_pos = state['start'][pid]
    end_pos = state['end'][pid]
    speed = state['info']['speed']
    damage = state['info']['damage']
    mspeed = state['info']['max speed']
    add(f'pos: {start_pos} -> {end_pos}, speed: {speed} ({mspeed})'
        f', damage: {damage}')

    add(f"cmd: {state['cmd']['cmd']}, exec time: {state['cmd']['exec_time']}")

    sstr = str(state['info']['state'])
    bstr = (f"boosting: {state['info']['boosting']}, boost-counter: " +
            f"{state['info']['boostcount']}")

    add(f"state: {sstr}, {bstr}")
    powerups = state['info']['powerups']
    powerups = ', '.join([f'{k}: {powerups[k]}' for k in powerups])
    add(f'powerups: {powerups}')

    pos = {}

    for player in state['start']:
        start = state['start'][player]
        end = state['end'][player]
        x = int(round(start[0] + (end[0] - start[0]) * frame_prog))
        if frame_prog:
            y = end[1]
        else:
            y = start[1]

        pos[(x, y)] = player

        if player == pid:
            x_ref, y_ref = x, y

    for y in range(1, y_size + 1):
        blocks = []
        x_start = max(1, x_ref - x_behind)
        if lift_fow:
            x_end = min(x_size + 1, x_ref + x_ahead + 1)
        else:
            x_end = min(x_size + 1, start_pos[0] + x_ahead + 1)
        for x in range(x_start, x_end):
            if (x, y) not in state['map']:
                continue
            blocks.append(state['map'][(x, y)])
            if (x, y) in pos:
                blocks[-1] = str(pos[(x, y)])

        add('[' + ''.join(blocks) + ']')

    add('')

def clear_lines(n):
    def clear_line():
        sys.stdout.write('\r')
        sys.stdout.write('\033[K')

    def one_line_up():
        sys.stdout.write('\033[F')

    for i in range(n):
        clear_line()
        if i + 1 != n:
            one_line_up()

def print_buffer(framebuffer):
    print('\n'.join(framebuffer))

round_num = 0

while True:
    cur_round = rounds[round_num]
    next_round = (rounds[1:] + [None])[round_num]

    states = {}
    for player in players:
        states[player] = read_state(cur_round, next_round, player)

    frames = int(fps / rps)
    for frame in range(frames):
        prev_lines = len(framebuffer)
        framebuffer.clear()

        framebuffer += [cur_round, '']

        for player in players:
            render(states[player], frame / frames)

        clear_lines(prev_lines + 1)
        print_buffer(framebuffer)

        if frame == 0:
            if manual:
                r = input()
                reset = False
                r = r if r else ']'
                if r == 'c':
                    manual = False
                elif r == ']':
                    round_num += 1
                elif r == '[':
                    round_num -= 1
                    reset = True
                else:
                    try:
                        round_num = int(r) - 1
                        reset = True
                    except:
                        print(f'unable to understand "{r}", aborting')
                        sys.exit(1)

                clear_lines(2)
                if reset:
                    break
            else:
                if delay:
                    time.sleep(delay)
                round_num += 1

        time.sleep(1 / fps)

    if round_num == len(rounds):
        break
