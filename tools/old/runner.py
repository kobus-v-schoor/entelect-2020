#! /usr/bin/env python3

import os
import json
import subprocess
import random
import shutil
from tqdm import tqdm

starter_pack = '/home/kobus/starter-pack-1'
runner_config_file = os.path.join(starter_pack, 'game-runner-config.json')
game_config_file = os.path.join(starter_pack, 'game-config.json')
logs_dir = os.path.join(starter_pack, 'match-logs')

player_a = '/home/kobus/repo'
player_b = '/home/kobus/opp-new'
# player_b = 'reference-bot/java/'
# player_b = '/home/kobus/opp-very-old'
min_lane = 1
max_lane = 4

# match_count = 10
match_count = 20

def run(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, capture_output=True, shell=True, check=True)

def play_match():
    seed = random.randint(0, 2 ** 16)

    # set seed
    with open(runner_config_file, 'r') as f:
        config = json.load(f)
    config['seed'] = seed
    with open(runner_config_file, 'w') as f:
        json.dump(config, f)

    def play(apos, bpos):
        with open(game_config_file, 'r') as f:
            config = json.load(f)
        config['PLAYER_ONE_START_LANE'] = apos
        config['PLAYER_TWO_START_LANE'] = bpos
        with open(game_config_file, 'w') as f:
            json.dump(config, f)

        run('make run', starter_pack)

        match_dir = os.path.join(logs_dir, sorted(os.listdir(logs_dir))[-1])
        rounds = [r for r in os.listdir(match_dir) if
                os.path.isdir(os.path.join(match_dir, r))]
        rounds = [int(r.lstrip('Round ')) for r in rounds]
        last_round = f'Round {max(rounds)}'

        endgame_file = os.path.join(match_dir, last_round, 'endGameState.txt')
        winner = None
        if os.path.isfile(endgame_file):
            with open(endgame_file, 'r') as f:
                for line in f.readlines():
                    if line.startswith('The winner is:'):
                        winner = line[15]
                    elif line[0] == 'A' or line[0] == 'B':
                        mid = line.split(':')[1]
                        score = int(mid.rstrip(' health'))
                        if line[0] == 'A':
                            a_score = score
                        else:
                            b_score = score
        return (winner, a_score, b_score)

    w1 = play(min_lane, max_lane)
    w2 = play(max_lane, min_lane)

# remove existing logs
if os.path.isdir(logs_dir):
    shutil.rmtree(logs_dir)

# set player a and b
with open(runner_config_file, 'r') as f:
    config = json.load(f)
config['player-a'] = player_a
config['player-b'] = player_b
with open(runner_config_file, 'w') as f:
    json.dump(config, f)

# play matches
for match in tqdm(range(match_count)):
    play_match()

def fixup(fname, drop=[], fix={}):
    with open(fname, 'r') as f:
        config = json.load(f)
    for d in drop:
        config.pop(d, None)
    for f in fix:
        config[f] = fix[f]
    with open(fname, 'w') as f:
        json.dump(config, f, indent=4)

# fix and prettify game configs
fixup(runner_config_file, drop=['seed'])
fixup(game_config_file, fix={
    'PLAYER_ONE_START_LANE': min_lane,
    'PLAYER_TWO_START_LANE': max_lane})
