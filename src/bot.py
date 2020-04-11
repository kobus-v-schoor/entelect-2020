import logging
import json
import os
from collections import deque

from state import State, next_state, final_state
from enums import Speed, Block, Cmd, CMD_SEARCH
from map import GlobalMap

logging.basicConfig(filename='bot.log', filemode='w', level=logging.INFO)
log = logging.getLogger(__name__)

class Tree:
    def __init__(self, path=[]):
        self.path = path
        self.children = (Tree(self.path + [c]) for c in CMD_SEARCH)

    def __str__(self):
        return str(self.path)

    def __repr__(self):
        return str(self)

    def depth(self):
        return len(self.path)

class Bot:
    def __init__(self):
        log.info('creating bot')
        self.next_round = None
        self.state = None
        self.global_map = GlobalMap(x_size=1500, y_size=4)
        self.finished = False
        self.state_cmd_cache = {}

        with open('weights.json', 'r') as wfile:
            weights = json.load(wfile)
            self.w_pos = weights['pos']
            self.w_speed = weights['speed']
            self.w_boosts = weights['boosts']
            self.w_opp_pos = weights['opp_pos']
            self.w_opp_speed = weights['opp_speed']

    def wait_for_next_round(self):
        log.debug('waiting for next round')
        self.next_round = int(input())
        log.debug(f'next round read as {self.next_round}')

    # reads the state json file
    # returns false if some error occurred
    def read_state(self):
        log.debug('reading json file')
        state_file = os.path.join('rounds', str(self.next_round), 'state.json')
        try:
            with open(state_file, 'r') as f:
                self.raw_state = json.load(f)
        except OSError:
            log.error(f'state file "{state_file}" cannot be opened for reading')
            return False
        except JSONDecodeError:
            log.error(f'unable to parse state file "{state_file}"')
            return False

        log.debug(f'successfully read state file {state_file}')
        return True

    def parse_state(self):
        log.debug('parsing state')

        if self.raw_state['player']['state'] == 'FINISHED':
            log.debug('detected finished state')
            self.finished = True
            return

        # parse state vars
        self.state = State(self.raw_state)

        # update global map
        self.state.map.update_global_map(self.global_map)

        # purge old state cmd cache
        self.state_cmd_cache = {}

        log.debug('finished parsing state')

    # executes the given cmd for the current round
    def exec(self, cmd):
        log.info(f'exec {cmd} for round {self.next_round}')
        print(f'C;{self.next_round};{cmd.value}')

    # returns the cmd that should be executed given the current state
    # done by doing a search for the best move
    def find_cmd(self):
        ## do bfs search of depth search_depth which prunes invalid paths
        # search depth determines how far into the future we test, e.g a value
        # of 3 means that we search 3 moves into the future
        search_depth = 4
        options = []

        # holds the bfs queue
        queue = deque()
        queue.append(Tree())

        # will hold the cache state
        cache = {}

        # true if one of the moves allow finishing the game
        endgame = False

        while queue:
            cur = queue.popleft()

            if cur.depth() == 0:
                queue += list(cur.children)
                continue

            actions = cur.path
            fstate = final_state(self.state, actions, cache)

            if fstate is not None:
                options.append((actions, fstate))
                if fstate.x >= self.global_map.max_x and cur.depth() == 1:
                    endgame = True
                    search_depth = 1
                elif fstate.x > self.state.map.max_x:
                    search_depth = min(search_depth, cur.depth())
                if cur.depth() < search_depth:
                    queue += list(cur.children)

        options = [o for o in options if len(o[0]) == search_depth]

        ## do sorting and selection
        def score(option):
            actions, fstate = option
            total = 0

            total += self.w_pos * (fstate.x - self.state.x)
            total += self.w_speed * fstate.speed
            total += (self.w_boosts *
                    (fstate.boosts - self.state.boosts) *
                    (Speed.BOOST_SPEED.value - Speed.MAX_SPEED.value))
            total += self.w_opp_pos * (fstate.opp_x - self.state.opp_x)
            total += self.w_opp_speed * fstate.opp_speed

            return total

        # we're in the endgame now
        # only thing that matters here is our speed - if the action didn't cross
        # the finish line it is given an infinitely negative score
        def endgame_score(option):
            actions, fstate = option

            if fstate.x < fstate.map.max_x:
                return float('-inf')
            return fstate.speed

        # sort by scores
        options = sorted(options, key=endgame_score if endgame else score,
                reverse=True)

        # choose best option
        best_option = options[0]

        # wanted cmd is the first move in the best option
        cmd = best_option[0][0]

        return cmd

    def run(self):
        log.debug('bot started')

        while True:
            # get the next round number
            self.wait_for_next_round()

            # read the state file
            if self.read_state():
                # parse the state file
                self.parse_state()

            # check if game is finished
            if self.finished:
                log.info('bot finished playing')
                break

            # execute next cmd
            self.exec(self.find_cmd())
