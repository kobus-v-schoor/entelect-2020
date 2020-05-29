import os
import sys
import json

from tabulate import tabulate

from tools.stats import matches_stats

same = False
if len(sys.argv) > 1:
    same = sys.argv[1] == 'same'

stats = matches_stats(os.getcwd(), same)
print()

for player in sorted(stats):
    print(player)

    headers = ['min', 'max', 'median', 'mean']
    rows = [
        ['matches', stats[player].pop('matches')],
        ['won', stats[player].pop('won')],
        ['win rate', round(stats[player].pop('win rate') * 100, 2)]
    ]

    for stat in stats[player]:
        if type(stats[player][stat]) is dict:
            rows.append([stat] + [round(stats[player][stat][k], 2) for k in
                                  headers])
        else:
            rows.append([stat, None])

    print(tabulate(rows, headers=(['statistic'] + headers), numalign='right',
                   tablefmt='rst'))
    print()
