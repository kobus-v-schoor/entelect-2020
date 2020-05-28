#! /usr/bin/env python3

import os
import csv

stats = {}
matches = 0

for match in os.listdir('.'):
    matches += 1
    files = list(os.listdir(match))
    files.remove('match.log')
    players = sorted([f.rstrip('.csv') for f in files if f.endswith('.csv')])
    rounds = [int(r.lstrip('Round ')) for r in files if r.startswith('Round')]
    rounds.sort()
    last_round = 'Round ' + str(rounds[-1]).zfill(3)

    for player in players:
        if not player in stats:
            stats[player] = {}
            stats[player]['wins'] = 0
            stats[player]['min_rounds'] = float('inf')
            stats[player]['max_rounds'] = float('-inf')
            stats[player]['rounds'] = []
            stats[player]['eff_speed'] = []
            stats[player]['turn_speed'] = []
            stats[player]['boost_used'] = 0
            stats[player]['boost_runs'] = []
            stats[player]['ahead'] = []
            stats[player]['scores'] = []

    with open(os.path.join(match, last_round, 'endGameState.txt'), 'r') as f:
        for line in f.readlines():
            if line.startswith('The winner is: '):
                w = line.lstrip('The winner is: ').strip()
                stats[w]['wins'] += 1
                stats[w]['rounds'].append(rounds[-1])
                stats[w]['min_rounds'] = min(stats[w]['min_rounds'], rounds[-1])
                stats[w]['max_rounds'] = max(stats[w]['max_rounds'], rounds[-1])
                winner = w
            else:
                for player in players:
                    if line.startswith(player):
                        mid = line.split(':')[1]
                        score = int(mid.rstrip(' health'))
                        stats[player]['scores'].append(score)

    end_pos = {}
    for player in players:
        s = stats[player]
        with open(os.path.join(match, f'{player}.csv'), 'r') as f:
            reader = csv.reader(f)
            prev_x = None
            boost_run = 0
            cmd = None
            for row in reader:
                rnd,pid,y,x,speed,state,boosting,bst_cnt,boosts,oils,score = row

                x = int(x)
                speed = int(speed)

                if int(rnd) == rounds[-1]:
                    end_pos[player] = x

                s['turn_speed'].append(speed)

                if prev_x is not None:
                    s['eff_speed'].append(x - prev_x)
                prev_x = x

                if cmd == 'USE_BOOST':
                    boost_run = 1
                    s['boost_used'] += 1
                if boost_run:
                    if speed != 15:
                        s['boost_runs'].append(boost_run)
                        boost_run = 0
                    else:
                        boost_run += 1

                rnd_dir = 'Round ' + str(rnd).zfill(3)
                with open(os.path.join(match, rnd_dir, player,
                    'PlayerCommand.txt'), 'r') as f:
                    for line in f.readlines():
                        if line.startswith('Command:'):
                            cmd = line.strip().lstrip('Command: ')
                            break

    ahead = []
    w_pos = 0
    for p in end_pos:
        if p != winner:
            ahead.append(end_pos[p])
        else:
            w_pos = end_pos[p]

    stats[winner]['ahead'].append(w_pos - max(ahead))

for player in stats:
    s = stats[player]
    def avgl(key):
        if s[key]:
            s[key] = round(sum(s[key]) / len(s[key]), 2)
        else:
            s[key] = 0
    def avg(key):
        if matches:
            s[key] = round(s[key] / matches, 2)
        else:
            s[key] = 0

    avgl('rounds')
    avgl('turn_speed')
    avgl('eff_speed')
    avgl('boost_runs')
    avg('boost_used')
    avgl('ahead')
    avgl('scores')

    boost_dist = s['boost_used'] * s['boost_runs'] * 15
    norm_runs = (1500 - boost_dist) / 9
    # amount of rounds needed if the player was at speed 9 whenever they were
    # not boosting, so basically driving absolutely perfectly
    s['theory'] = round(norm_runs + (s['boost_used'] * s['boost_runs']), 2)
    s['improve'] = round(s['rounds'] - s['theory'], 2)

for player in stats:
    s = stats[player]
    print('player:\t\t\t', player)
    print('wins:\t\t\t', s['wins'])
    print('min rounds:\t\t', s['min_rounds'])
    print('max rounds:\t\t', s['max_rounds'])
    print('avg rounds:\t\t', s['rounds'])
    print('theoretical best:\t', s['theory'], f"({s['improve']})")
    print('avg turn speed:\t\t', s['turn_speed'])
    print('avg eff speed:\t\t', s['eff_speed'])
    print('avg boosts used:\t', s['boost_used'])
    print('avg boost run length:\t', s['boost_runs'])
    print('avg lead when winner:\t', s['ahead'])
    print('avg score:\t\t', s['scores'])

    print()
