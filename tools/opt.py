import os
import random
from itertools import combinations

from tools.match import play_round, rank

wd = os.path.realpath(os.path.join('tmpfs', 'opt'))

def rand():
    return {
        "boosts": round(random.random(), 2),
        "lizards": round(random.random(), 2),
        "oils": round(random.random(), 2),
        "pos": round(random.random(), 2),
        "score": round(random.random(), 2),
        "speed": round(random.random(), 2),
        "tweets": round(random.random(), 2),
    }

pop = [rand() for _ in range(5)]
results = rank(play_round(wd, list(combinations(pop, 2))))
