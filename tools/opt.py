#! /usr/bin/env python3

# optimizes the scoring weights

import os
import shutil
import subprocess
import json
import random
import math
from tqdm import tqdm

bot_zip = '/home/kobus/bot.zip'
starter_pack = '/home/kobus/starter-pack.zip'
wd = '/home/kobus/tmp/opt'
results = 'results'

def run(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, capture_output=True, shell=True, check=True)

print('cleaning work dir')
if os.path.isdir(wd):
    shutil.rmtree(wd)
os.makedirs(wd)

print('unzipping starter-pack')
starter_dir = os.path.join(wd, 'starter-pack')
os.makedirs(starter_dir)
run(f'unzip {starter_pack}', wd)

print('unzip player a')
player_a = os.path.join(wd, 'player_a')
os.makedirs(player_a)
run(f'unzip {bot_zip}', player_a)

print('unzip player b')
player_b = os.path.join(wd, 'player_b')
os.makedirs(player_b)
run(f'unzip {bot_zip}', player_b)

print('update starter config')
config_file = os.path.join(starter_dir, 'game-runner-config.json')
with open(config_file, 'r') as f:
    config = json.load(f)
config['player-a'] = player_a
config['player-b'] = player_b
with open(config_file, 'w') as f:
    json.dump(config, f)

def rand_ind():
    return {
            'pos': random.random(),
            'speed': random.random(),
            'boosts': random.random(),
            'opp_pos': -random.random(),
            'opp_speed': -random.random()
            }

def merge(p1, p2):
    n = {}
    for k in p1:
        r = random.randint(0, 2)

        if r == 0:
            n[k] = p1[k]
        elif r == 1:
            n[k] = p2[k]
        else:
            n[k] = (p1[k] + p2[k]) / 2

    return n

def play_match(p1, p2):
    seed = random.randint(0, 2 ** 16)

    # set seed
    with open(config_file, 'r') as f:
        config = json.load(f)
    config['seed'] = seed
    with open(config_file, 'w') as f:
        json.dump(config, f)

    def play(lp, rp):
        with open(os.path.join(player_a, weights_file), 'w') as f:
            json.dump(lp, f)
        with open(os.path.join(player_b, weights_file), 'w') as f:
            json.dump(rp, f)

        if os.path.isdir(logs_dir):
            shutil.rmtree(logs_dir)

        run('make run', starter_dir)

        match_dir = os.path.join(logs_dir, list(os.listdir(logs_dir))[0])
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

        if winner is None:
            return None
        elif winner == 'A':
            return (lp, a_score, b_score)
        else:
            return (rp, a_score, b_score)

    w1 = play(p1, p2)
    w2 = play(p2, p1)
    if w1[0] == w2[0]:
        return w1[0]
    else:
        if w1[1] + w2[2] > w1[2] + w2[1]:
            return p1
        else:
            return p2

def next_round(pop, pbar):
    random.shuffle(pop)
    pairs = list(zip(pop[::2], pop[1::2]))
    winners = []

    for pair in pairs:
        p1, p2 = pair
        w = play_match(p1, p2)
        pbar.update()
        winners.append(random.choice((p1, p2)) if w is None else w)

    return winners

pop_size = 2 ** 6 # 64
generations = 50

print('pop size:', pop_size)
print('generations:', generations)

population = [rand_ind() for _ in range(pop_size)]
weights_file = 'src/weights.json'
logs_dir = os.path.join(starter_dir, 'match-logs')

print('starting training')

runs = int(pop_size / 2) * generations
runs += pop_size - 1

with tqdm(total=runs) as pbar:
    for gen in range(generations):
        new_pop = next_round(population, pbar)

        random.shuffle(new_pop)
        pairs = list(zip(new_pop[::2], new_pop[1::2]))

        for pair in pairs:
            new_pop.append(merge(*pair))
            new_pop.append(merge(random.choice(pair), rand_ind()))

        population = new_pop

    while len(population) > 1:
        population = next_round(population, pbar)

print('winner:', population[0])
with open('result.json', 'w') as f:
    json.dump(population[0], f, indent=4)
    f.write('\n')

print('done')
