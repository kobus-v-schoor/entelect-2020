#! /usr/bin/env python3

import json
import os
import shutil
import random

from tools.match import play_ref_matches

with open('seed.json', 'r') as f:
    seed = json.load(f)

print(f'starting with seed {json.dumps(seed, indent=2)}\n')

movement = ['pos', 'speed', 'boosts', 'score']
offensive = ['oils']
match_count = 20
samples = 30
digits = 3

print(f'movement parameters: {movement}')
print(f'offensive parameters: {offensive}\n')

ref_bot = './reference-bot/java/'
tmp_wd = os.path.realpath('tmpfs/opt-stats')

if os.path.isdir(tmp_wd):
    shutil.rmtree(tmp_wd)
os.makedirs(tmp_wd)

def optimize(starting_vals, parameters, scoring, opponent):
    config = {**starting_vals}

    for parameter in parameters:
        print(f'now trying to optimize {parameter}')

        scores = {}

        for sample in range(samples):
            if not scores:
                value = starting_vals[parameter]
            else:
                mean = sum([k * scores[k] for k in scores])
                mean /= sum([abs(scores[k]) for k in scores])
                print(f'mean updated to {mean}')

                value = round(random.gauss(mean, (samples - sample) / samples),
                              digits)

            print(f'testing {parameter} = {value}')

            config[parameter] = value
            stats = play_ref_matches(match_count, tmp_wd, config, opponent)
            score = scoring(stats)
            print(f'score for {parameter} = {value} is {score}')

            scores[value] = score

        value = max(scores, key=lambda v: scores[v])
        print(f'selected {parameter} = {value}')
        config[parameter] = value
        print(f'new config is {json.dumps(config, indent=2)}')

    return config

movement_config = optimize(seed, movement,
                           lambda s: 500 - s['sonic-sloth']['rounds']['mean'],
                           ref_bot)

print(json.dumps(movement_config))
