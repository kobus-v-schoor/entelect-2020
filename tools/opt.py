#! /usr/bin/env python3

# optimizes the scoring weights

import os
import shutil
import subprocess
import json
import random
from tqdm import tqdm

bot_zip = '/home/kobus/bot.zip'
starter_pack = '/home/kobus/starter-pack.zip'
wd = '/home/kobus/opt'
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
run(f'unzip {starter_pack}', starter_dir)

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
    with open(os.path.join(player_a, weights_file), 'w') as f:
        json.dump(p1, f)
    with open(os.path.join(player_b, weights_file), 'w') as f:
        json.dump(p2, f)

    if os.path.isdir(logs_dir):
        shutil.rmtree(logs_dir)

    run('make run', starter_dir)

    match_dir = os.path.join(logs_dir, list(os.listdir(logs_dir))[0])
    rounds = [r for r in os.listdir(match_dir) if
            os.path.isdir(os.path.join(match_dir, r))]
    last_round = max(rounds)

    endgame_file = os.path.join(match_dir, last_round, 'endGameState.txt')
    with open(endgame_file, 'r') as f:
        for line in f.readlines():
            if line.startswith('The winner is:'):
                winner = line[15]
                break
    return p1 if winner == 'A' else p2

pop_size = 60
selection = int(pop_size / 2)
generations = 10

print('pop size:', pop_size)
print('generations:', generations)
print('selection size:', selection)

population = [rand_ind() for _ in range(pop_size)]
weights_file = 'src/weights.json'
logs_dir = os.path.join(starter_dir, 'match-logs')

print('starting training')

with tqdm(total=(generations * selection + sum(range(pop_size)))) as pbar:
    for gen in range(generations):
        sel = []

        while len(sel) < selection:
            p1 = random.choice(population)
            p2 = random.choice(population)

            if p1 == p2:
                continue

            sel.append(play_match(p1, p2))
            population.remove(sel[-1])

            pbar.update(1)

        new_pop = sel

        while len(new_pop) < pop_size:
            p1 = random.choice(sel + population)
            p2 = random.choice(sel + population)

            if p1 == p2:
                continue

            new_pop.append(merge(p1, p2))

        population = new_pop

    stats = [0 for _ in population]

    for i in range(len(population)):
        for j in range(i + 1, len(population)):
            w = play_match(population[i], population[j])
            if w == population[i]:
                stats[i] += 1
            else:
                stats[j] += 1
            pbar.update(1)

stats = list(zip(population, stats))
stats = sorted(stats, key=lambda x: x[1], reverse=True)

if os.path.isdir(results):
    shutil.rmtree(results)
os.makedirs(results)

for idx, w in enumerate(stats):
    with open(os.path.join(results, str(idx)), 'w') as f:
        json.dump(w[0], f)

print('done')
