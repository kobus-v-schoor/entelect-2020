#! /usr/bin/env python3

# optimizes the scoring weights

import os
import shutil
import subprocess
import json
import random
import math
import string
from multiprocessing import Pool
from itertools import combinations
from tqdm import tqdm

bot_zip = '/home/kobus/bot.zip'
starter_pack = '/home/kobus/starter-pack.zip'
wd = '/home/kobus/tmp/opt'
results_dir = 'results'
weights_file = 'src/weights.json'

def run(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, shell=True, check=True)

# remove working directory
if os.path.isdir(wd):
    shutil.rmtree(wd)
os.makedirs(wd)

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
    ops = [
            lambda k: p1[k],
            lambda k: p2[k],
            lambda k: (p1[k] + p2[k]) / 2,
            ]

    return {key: random.choice(ops)(key) for key in p1}

# mutate one of the keys
def mutate(p):
    m = {k: p[k] for k in p}
    k = random.choice(list(m.keys()))
    m[k] = random.random() * (1 if p[k] > 0 else -1)
    return m

def mut_pop_size(gen):
    return int(0.25 * 2 ** (-gen / generations) * pop_size)

def random_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def setup_wd(tmp):
    starter_dir = os.path.join(tmp, 'starter-pack')
    os.makedirs(starter_dir)
    run(f'unzip {starter_pack}', tmp)

    player_a = os.path.join(tmp, 'player_a')
    os.makedirs(player_a)
    run(f'unzip {bot_zip}', player_a)

    player_b = os.path.join(tmp, 'player_b')
    os.makedirs(player_b)
    run(f'unzip {bot_zip}', player_b)

    config_file = os.path.join(starter_dir, 'game-runner-config.json')
    with open(config_file, 'r') as f:
        config = json.load(f)
    config['player-a'] = player_a
    config['player-b'] = player_b
    with open(config_file, 'w') as f:
        json.dump(config, f)

    logs_dir = os.path.join(starter_dir, 'match-logs')

    return starter_dir, player_a, player_b, config_file, logs_dir

def play_match(tup):
    p1, p2 = tup

    # setup starter_dirs
    tmp_dir = '/'
    while os.path.isdir(tmp_dir):
        tmp_dir = os.path.join(wd, random_id())
    starter_dir, player_a, player_b, config_file, logs_dir = setup_wd(tmp_dir)

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

    # remove tmp dirs
    shutil.rmtree(tmp_dir)

    # calculate winner
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

    with Pool(int(round(os.cpu_count() / 1.285))) as pool:
        for w in pool.imap_unordered(play_match, combinations(pop, 2)):
            if w is not None:
                score[keyfi(w)] += 1
            pbar.update()

    return sorted(pop, key=lambda p: score[keyfi(p)], reverse=True)

pop_size = 48
generations = 40

print('pop size:', pop_size)
print('generations:', generations)

population = [rand_ind() for _ in range(pop_size)]

print('starting training')

runs = generations * sum(range(pop_size))

with tqdm(total=runs, smoothing=0) as pbar:
    for gen in range(generations):
        selection = rank(population, pbar)[:int(pop_size/2)]

        if gen + 1 == generations:
            results = selection
            continue

        # perform mutation
        mut_len = mut_pop_size(gen)
        muts = [mutate(m) for m in random.sample(selection, k=mut_len)]

        # generate offspring
        off_len = pop_size - len(selection) - len(muts)
        pairs = list(combinations(selection, 2))
        offspring = [merge(*p) for p in random.sample(pairs, k=off_len)]

        # create new population
        population = selection + muts + offspring

        # remove duplicates
        population = [dict(t) for t in {tuple(sorted(d.items())) for d in
            population}]

        # pad population if required
        population += [rand_ind() for _ in range(pop_size-len(population))]

print('winner:', results[0])
if os.path.isdir(results_dir):
    shutil.rmtree(results_dir)
os.makedirs(results_dir)

for i, res in enumerate(results):
    with open(os.path.join(results_dir, f'{i}.json'), 'w') as f:
        json.dump(res, f, indent=4)
        f.write('\n')

print('done')
