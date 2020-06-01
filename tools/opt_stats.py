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
    'oils': 0,
    'lizards': 4,
    'tweets': 0,

    'score': 0.3
}

print(f'starting with seed {json.dumps(seed, indent=2)}\n')

# pos is kept constant as point of reference
movement = ['speed', 'boosts', 'score']
offensive = ['oils']
parameters = movement + offensive
parameters = ['lizards']

match_count = 20
samples = 30
digits = 4

print(f'movement parameters: {movement}')
print(f'offensive parameters: {offensive}\n')

tmp_wd = os.path.realpath('tmpfs/opt-stats')

if os.path.isdir(tmp_wd):
    shutil.rmtree(tmp_wd)
os.makedirs(tmp_wd)

def optimize(starting_vals, parameters, opponent):
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
            score = stats['A - sonic-sloth']['eff_speed']['mean']
            # score = stats['A - sonic-sloth']['win rate']
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

config = optimize(seed, parameters, seed)
