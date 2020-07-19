import os
import json
import statistics
from tqdm import tqdm

def match_stats(path):
    files = os.listdir(path)
    files.remove('match.log')

    players = sorted([f[:-4] for f in files if f.endswith('.csv')])
    rounds = sorted([f for f in files if f.startswith('Round')])
    last_round = rounds[-1]

    stats = {}

    for player in players:
        stats[player] = {}

        stats[player]['won'] = None
        stats[player]['rounds'] = None
        stats[player]['score'] = None

        stats[player]['exec_time'] = []

        # speed effective during turn
        stats[player]['eff_speed'] = []
        # speed at start of turn
        stats[player]['turn_speed'] = []
        stats[player]['damage'] = []

        stats[player]['fixes_used'] = 0

        stats[player]['boosts_used'] = 0
        stats[player]['boost_runs'] = []

        stats[player]['oils_used'] = 0
        stats[player]['lizards_used'] = 0
        stats[player]['tweets_used'] = 0
        stats[player]['emps_used'] = 0

    endgame_path = os.path.join(path, last_round, 'endGameState.txt')
    with open(endgame_path, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith('The winner is:'):
                winner = line[15:]
                stats[winner]['won'] = 1
                stats[winner]['rounds'] = int(last_round[6:])
            else:
                for player in players:
                    if line.startswith(player):
                        line = line.split(':')[1]
                        line = line.split(' ')[0]
                        stats[player]['score'] = int(line)

    for player in players:
        prev_x = None
        used_boost = False
        used_boost_counter = 0

        for cur_round in rounds:
            state_path = os.path.join(path, cur_round, player, 'JsonMap.json')
            with open(state_path, 'r') as f:
                state = json.load(f)

            cmd_path = os.path.join(path, cur_round, player,
                                    'PlayerCommand.txt')
            with open(cmd_path, 'r') as f:
                for line in f.readlines():
                    line = line.strip()
                    if line.startswith('Command'):
                        cmd = line[9:]
                    elif line.startswith('Execution time'):
                        stats[player]['exec_time'].append(int(line[16:-2]))

            x = state['player']['position']['x']
            speed = state['player']['speed']
            boosting = state['player']['boosting']

            # effective speed
            if prev_x is not None:
                stats[player]['eff_speed'].append(x - prev_x)
            prev_x = x

            # turn speed
            stats[player]['turn_speed'].append(speed)

            stats[player]['damage'].append(state['player']['damage'])

            # boosts run length
            if used_boost:
                if not boosting:
                    stats[player]['boost_runs'].append(used_boost_counter)
                    used_boost = False
                else:
                    used_boost_counter += 1

            # boosts used
            if cmd == 'USE_BOOST':
                stats[player]['boosts_used'] += 1
                used_boost = True
                used_boost_counter = 1

            # fixes used
            if cmd == 'FIX':
                stats[player]['fixes_used'] += 1

            # oils used
            if cmd == 'USE_OIL':
                stats[player]['oils_used'] += 1

            # lizards used
            if cmd == 'USE_LIZARD':
                stats[player]['lizards_used'] += 1

            # tweets used
            if cmd.startswith('USE_TWEET'):
                stats[player]['tweets_used'] += 1

            # emps used
            if cmd == 'USE_EMP':
                stats[player]['emps_used'] += 1

    def avg(player, key):
        if stats[player][key]:
            stats[player][key] = (sum(stats[player][key]) /
                                  len(stats[player][key]))
        else:
            stats[player][key] = None

    for player in players:
        for key in ['exec_time', 'eff_speed', 'turn_speed', 'damage',
                    'boost_runs']:
            avg(player, key)

    return stats

def matches_stats(path, keep_prefix=False):
    stats = {}
    for match in tqdm(os.listdir(path)):
        mstats = match_stats(os.path.join(path, match))

        if not keep_prefix:
            mstats = {k[4:]: mstats[k] for k in mstats}

        for player in mstats:
            if not player in stats:
                stats[player] = {k: [] for k in mstats[player]}
                stats[player]['matches'] = 0

            stats[player]['matches'] += 1
            for key in mstats[player]:
                if mstats[player][key] is not None:
                    stats[player][key].append(mstats[player][key])

    def avg_min_max(player, key):
        if stats[player][key]:
            new = {}
            new['min'] = float(min(stats[player][key]))
            new['max'] = float(max(stats[player][key]))
            new['median'] = statistics.median(stats[player][key])
            new['mean'] = statistics.mean(stats[player][key])
            stats[player][key] = new
        else:
            stats[player][key] = None

    for player in stats:
        for key in stats[player]:
            if key == 'won':
                stats[player]['won'] = sum(stats[player]['won'])
            elif key != 'matches':
                avg_min_max(player, key)

        stats[player]['win rate'] = (stats[player]['won'] /
                                     stats[player]['matches'])

    return stats
