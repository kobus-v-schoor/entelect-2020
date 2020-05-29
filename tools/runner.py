import os
import shutil

from tqdm import tqdm

from tools.match import play_match

starter_dir = '/home/kobus/starter-pack-1'
player_a = '/home/kobus/repo'
player_b = '/home/kobus/opp/opp-new'
matches = 20

match_logs = os.path.join(starter_dir, 'match-logs')

if os.path.isdir(match_logs):
    shutil.rmtree(match_logs)

stats = {
    'A': {
        'wins': 0,
        'score': 0,
    },
    'B': {
        'wins': 0,
        'score': 0,
    },
}

print(f'A: {player_a}')
print(f'B: {player_b}')

for match in tqdm(range(matches)):
    winners, a_score, b_score = play_match(starter_dir, player_a, player_b)

    for winner in winners:
        stats[winner]['wins'] += 1
    stats['A']['score'] += a_score
    stats['B']['score'] += b_score

    tqdm.write(str(stats))
