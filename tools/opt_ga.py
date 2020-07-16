import os
import shutil
import random
import json
from itertools import product, combinations

from tqdm import tqdm

from tools.match import play_round, rank

wd = os.path.realpath(os.path.join('tmpfs', 'opt'))

if os.path.isdir(wd):
    shutil.rmtree(wd)

results_dir = 'results'

population_size = 30
generations = 40
mutation_decay = 0.4
champion_count = 7
digits = 3

seed = {
    "pos": 1.0,
    "speed": 1.0,

    "boosts": 9.6,
    "oils": 0,
    "lizards": 4,
    "tweets": 0,

    "score": 0.3,
    "damage": -1,
}

# generate offspring between two individuals
def merge(p1, p2):
    ops = [
        lambda k: p1[k],
        lambda k: p2[k],
        lambda k: round((p1[k] + p2[k]) / 2, digits),
    ]

    return {key: random.choice(ops)(key) for key in p1}

# mutate one of the keys
def mutate(p, gen=0):
    m = {k: p[k] for k in p}
    k = random.choice(list(m.keys()))
    s = 5 * (2 ** (-1.7 * (gen / generations)))
    m[k] = round(random.normalvariate(m[k], s), digits)
    return m

# amount of individuals to mutate
def mutation_population_size(gen):
    return int(mutation_decay * 2 ** (-3 * gen / generations) * population_size)

population = [seed] + [mutate(seed) for _ in range(population_size - 1)]

print('population size:', population_size)
print('generations:', generations)

print('starting training')

total = generations * (population_size - champion_count) * champion_count

with tqdm(total=total, smoothing=0, desc='overall', dynamic_ncols=True) as pbar:
    for gen in range(generations):
        champions = population[:champion_count]

        matches = list(product(population[:champion_count],
                               population[champion_count:]))
        results = rank(play_round(wd, matches, pbar))

        selection = [r[0] for r in results[:int(population_size/2)]]

        # perform mutation
        mut_count = mutation_population_size(gen)
        muts = [mutate(m, gen) for m in random.sample(selection, k=mut_count)]

        # generate offspring
        off_count = population_size - len(selection) - len(muts)
        pairs = list(combinations(selection, 2))
        offspring = [merge(*p) for p in random.sample(pairs, k=off_count)]

        # create new population
        population = selection + muts + offspring

results = selection

print('winner:', results[0])
if os.path.isdir(results_dir):
    shutil.rmtree(results_dir)
os.makedirs(results_dir)

for i, res in enumerate(results):
    with open(os.path.join(results_dir, f'{i}.json'), 'w') as f:
        json.dump(res, f, indent=4)
        f.write('\n')

print('done')
