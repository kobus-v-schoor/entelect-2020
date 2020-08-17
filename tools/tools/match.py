import os
import subprocess
import json
import random
import string
import shutil
from multiprocessing import Pool
from tqdm import tqdm
from tools.stats import matches_stats

starter_pack_zip = os.path.realpath('starter-pack.zip')
bot_zip = os.path.realpath('bot.zip')
cpu_div = 1

def run(cmd, wd):
    subprocess.run(cmd, cwd=wd, capture_output=True, shell=True, check=True)

def pretty_json_dump(obj, f):
    json.dump(obj, f, indent=4)

def set_config(starter_dir, fname, options):
    config_file = os.path.join(starter_dir, fname)
    with open(config_file, 'r') as f:
        config = json.load(f)
    for key in options:
        config[key] = options[key]
    with open(config_file, 'w') as f:
        pretty_json_dump(config, f)

def set_game_runner_config(starter_dir, options):
    set_config(starter_dir, 'game-runner-config.json', options)

def set_game_config(starter_dir, options):
    set_config(starter_dir, 'game-config.json', options)

def set_match_players(starter_dir, player_a, player_b):
    set_game_runner_config(starter_dir,
                           {'player-a': player_a, 'player-b': player_b})

def set_seed(starter_dir, seed):
    set_game_runner_config(starter_dir, {'seed': seed})

def set_player_config(player, config):
    config_file = os.path.join(player, os.path.join('sloth', 'weights.json'))
    with open(config_file, 'w') as f:
        pretty_json_dump(config, f)

def setup_wd(wd):
    starter_dir = os.path.join(wd, 'starter-pack')
    os.makedirs(starter_dir)
    run(f'unzip {starter_pack_zip}', wd)

    # increase max timeout for multi-threaded operation
    set_game_runner_config(starter_dir, {'max-runtime-ms': 10000})

    player_a = os.path.join(wd, 'player_a')
    os.makedirs(player_a)
    run(f'unzip {bot_zip}', player_a)

    player_b = os.path.join(wd, 'player_b')
    os.makedirs(player_b)
    run(f'unzip {bot_zip}', player_b)

    return starter_dir, player_a, player_b

def setup_tmp_wd(wd):
    tmp_dir = '/'
    while os.path.isdir(tmp_dir):
        r = ''.join(random.choices(string.ascii_lowercase, k=8))
        tmp_dir = os.path.join(wd, r)

    return (tmp_dir,) + setup_wd(tmp_dir)

def play_match(starter_dir, player_a, player_b):
    # set players
    set_match_players(starter_dir, player_a, player_b)

    # set seed
    seed = random.randint(0, 2 ** 16)
    set_seed(starter_dir, seed)

    logs_dir = os.path.join(starter_dir, 'match-logs')

    def play(flipped):
        if not flipped:
            config = {
                'PLAYER_ONE_START_LANE': 1,
                'PLAYER_TWO_START_LANE': 4,
            }
        else:
            config = {
                'PLAYER_ONE_START_LANE': 4,
                'PLAYER_TWO_START_LANE': 1,
            }

        set_game_config(starter_dir, config)

        run('make run', starter_dir)

        matches = sorted(list(os.listdir(logs_dir)))
        match_dir = os.path.join(logs_dir, matches[-1])
        rounds = [r for r in os.listdir(match_dir) if r.startswith('Round ')]
        last_round = max(rounds)

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
        return (winner, a_score, b_score)

    # play one flipped and one normal match
    try:
        winner_1, a_score_1, b_score_1 = play(flipped=True)
        winner_2, a_score_2, b_score_2 = play(flipped=False)

        a_score = a_score_1 + a_score_2
        b_score = b_score_1 + b_score_2
    except TypeError:
        winner_1 = random.choice('AB')
        winner_2 = random.choice('AB')

        a_score, b_score = 0, 0

    return ((winner_1, winner_2), a_score, b_score)

def play_tmp_match(wd, a_config, b_config):
    # setup tmp wd
    tmp_dir, starter_dir, player_a, player_b = setup_tmp_wd(wd)

    # set player weights
    set_player_config(player_a, a_config)
    set_player_config(player_b, b_config)

    # play_match
    winners, a_score, b_score = play_match(starter_dir, player_a, player_b)
    a_wins = winners.count('A')
    b_wins = winners.count('B')

    # remove tmp wd
    shutil.rmtree(tmp_dir)

    return ((a_config, a_wins, a_score), (b_config, b_wins, b_score))

def play_tmp_match_wrapper(tup):
    wd, a_config, b_config = tup
    return play_tmp_match(wd, a_config, b_config)

# takes a working directory and a list of tuples, with each tuple being two
# player configs to play against each other
def play_round(wd, matches, pbar):
    results = []

    with Pool(int(os.cpu_count() / cpu_div)) as pool:

        matches = [(wd,) + m for m in matches]
        gen = pool.imap_unordered(play_tmp_match_wrapper, matches)

        for match in tqdm(gen, desc='generation', position=1,
                          total=len(matches), smoothing=0, dynamic_ncols=True):
            results.append(match)
            pbar.update()

    return results

def rank(matches):
    # turns a dict into a (key, value) tuple for hashing
    keyfi = lambda p: tuple([(k, p[k]) for k in sorted(p)])

    score = {}

    for match in matches:
        def update_score(result):
            player, wins, match_score = result
            key = keyfi(player)

            if not key in score:
                score[key] = {'matches': 0, 'wins': 0, 'score': 0}

            score[key]['matches'] += 2
            score[key]['wins'] += wins
            score[key]['score'] += match_score

        for result in match:
            update_score(result)

    score = [(dict(k), score[k]['wins'] / score[k]['matches'],
              score[k]['score']) for k in score]

    return sorted(score, key=lambda p: (p[1], p[2]), reverse=True)

def play_stats_match(wd, a_config, b_config):
    # setup tmp wd
    tmp_dir, starter_dir, player_a, player_b = setup_tmp_wd(wd)

    # set player weights
    set_player_config(player_a, a_config)
    set_player_config(player_b, b_config)

    # play_match
    play_match(starter_dir, player_a, player_b)

    match_logs = os.path.join(starter_dir, 'match-logs')

    return tmp_dir, match_logs

def play_stats_match_wrapper(tup):
    return play_stats_match(*tup)

def play_stats(count, wd, a_config, b_config):
    logs_dir = os.path.join(wd, 'logs')
    os.makedirs(logs_dir)

    with Pool(int(os.cpu_count() / cpu_div)) as pool:
        matches = [(wd, a_config, b_config)] * count
        gen = pool.imap_unordered(play_stats_match_wrapper, matches)

        count = 0
        for tmp_dir, match_logs in tqdm(gen, desc='stats round',
                                        total=len(matches),
                                        dynamic_ncols=True):
            for match in os.listdir(match_logs):
                os.rename(os.path.join(match_logs, match),
                          os.path.join(logs_dir, str(count)))
                count += 1

            shutil.rmtree(tmp_dir)

    stats = matches_stats(logs_dir, keep_prefix=True)
    shutil.rmtree(logs_dir)

    return stats
