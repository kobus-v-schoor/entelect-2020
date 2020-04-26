#! /usr/bin/env python3

# optimizes the scoring weights

import os
import shutil
import subprocess
import json
import random
import math
import copy
from itertools import combinations
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
            'score': random.random(),
            'opp_pos': -random.random(),
            'opp_speed': -random.random(),
            'opp_score': -random.random(),
            }

def merge(p1, p2):
    n = {}
    for k in p1:
        n[k] = (p1[k] + p2[k]) / 2

    return n

def mutate(p):
    m = copy.deepcopy(p)
    k = random.choice(list(m.keys()))
    m[k] = random.random() * (1 if p[k] > 0 else -1)
    return m

def mut_pop_size(gen):
    return int(0.25 * 2 ** (-gen / generations) * pop_size)

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
    if w1 is None or w2 is None:
        return random.choice((p1, p2))
    elif w1[0] == w2[0]:
        return w1[0]
    else:
        if w1[1] + w2[2] > w1[2] + w2[1]:
            return p1
        else:
            return p2

def rank(pop, pbar):
    keyfi = lambda d: tuple(sorted(d.items()))
    score = {keyfi(p): 0 for p in pop}

    for pair in combinations(pop, 2):
        w = play_match(*pair)
        if w is not None:
            score[keyfi(w)] += 1
        pbar.update()

    return sorted(pop, key=lambda p: score[keyfi(p)], reverse=True)

pop_size = 2 ** 4
generations = 20

print('pop size:', pop_size)
print('generations:', generations)

population = [rand_ind() for _ in range(pop_size)]
weights_file = 'src/weights.json'
logs_dir = os.path.join(starter_dir, 'match-logs')

print('starting training')

runs = generations * sum(range(pop_size))

with tqdm(total=runs) as pbar:
    for gen in range(generations):
        selection = rank(population, pbar)[:int(pop_size/2)]

        if gen + 1 == generations:
            results = selection
            continue

        muts = []
        for _ in range(mut_pop_size(gen)):
            muts.append(mutate(random.choice(selection)))

        offspring = []
        while len(selection) + len(muts) + len(offspring) < pop_size:
            offspring.append(merge(*random.sample(selection, 2)))

        population = selection + muts + offspring

print('winner:', results[0])
if os.path.isdir('results'):
    shutil.rmtree('results')
os.makedirs('results')

for i, res in enumerate(results):
    with open(os.path.join('results', f'{i}.json'), 'w') as f:
        json.dump(res, f, indent=4)
        f.write('\n')

print('done')
