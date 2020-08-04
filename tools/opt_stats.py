#! /usr/bin/env python3

import json
import os
import shutil
import random

from tools.match import play_stats

seed = {
    'pos': 1.0,
    'speed': 1.0,

    'boosts': 9.6,
    'lizards': 2.3,

    'oils': 0.4871,
    'tweets': 0,
    'emps': 1,

    'damage': -1,
    'score': 0.3,

    'next_state': 0.5
}

print(f'starting with seed {json.dumps(seed, indent=2)}\n')

# pos is kept constant as point of reference
movement = ['damage', 'speed', 'boosts', 'lizards', 'score', 'next_state']
offensive = ['oils', 'tweets'] # , 'emps']

match_count = 20
samples = 30
digits = 4

print(f'movement parameters: {movement}')
print(f'offensive parameters: {offensive}\n')

tmp_wd = os.path.realpath('tmpfs/opt-stats')

if os.path.isdir(tmp_wd):
    shutil.rmtree(tmp_wd)
os.makedirs(tmp_wd)

def optimize(starting_vals, parameters, opponent, neg_opponent):
    config = {**starting_vals}

    for parameter in parameters:
        print(f'now trying to optimize {parameter}')

        scores = {}

        value = starting_vals[parameter]

        for sample in range(samples):
            print(f'sample {sample+1}/{samples}')
            print(f'testing {parameter} = {value}')

            config[parameter] = value
            stats = play_stats(match_count, tmp_wd, config, opponent)
            score = stats['A - sonic-sloth']['eff_ratio']['mean']
            if neg_opponent:
                score -= stats['B - sonic-sloth']['eff_ratio']['mean']
            scores[value] = score
            print(f'score for {parameter} = {value} is {score}')

            mu = max(scores, key=lambda v: scores[v])
            sigma = 2 ** (-3 * sample / samples)
            print(f'mu: {mu} sigma: {round(sigma, 4)}')
            value = round(random.gauss(mu, sigma), digits)
            print(f'next value: {value}')

        value = max(scores, key=lambda v: scores[v])
        print(f'selected {parameter} = {value}')
        config[parameter] = value
        print(f'new config is {json.dumps(config, indent=2)}')

    return config

mov_config = optimize(seed, movement, seed, neg_opponent=False)
off_config = optimize(mov_config, offensive, seed, neg_opponent=True)
