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
        search_depth = 2
        options = []

        # holds the bfs queue
        queue = deque()
        queue.append(Tree())

        # will hold the cache state
        cache = {}

        while queue:
            cur = queue.popleft()

            if cur.depth() == 0:
                queue += list(cur.children)
                continue

            actions = cur.path
            fstate = final_state(self.state, actions, cache)

            if fstate is not None:
                if cur.depth() >= search_depth:
                    options.append((actions, fstate))
                else:
                    queue += list(cur.children)

        ## do sorting and selection
        def score(option):
            actions, fstate = option
            return sum([
                fstate.x - self.state.x,
                fstate.speed,
                # calculates potential benefit of new boosts * avg boost length
                (fstate.boosts - self.state.boosts) *
                (Speed.BOOST_SPEED.value - Speed.MAX_SPEED.value) * 1.63,
                ])

        # sort by scores
        options = sorted(options, key=score, reverse=True)

        # choose best option
        best_option = options[0]

        # wanted cmd is the first move in the best option
        cmd = best_option[0][0]

        # drop oil if doing nothing else
        if cmd == Cmd.NOP and self.state.oils:
            # hard requirements (all must be true)
            drop = self.state.x > self.state.opp_x
            drop = drop and self.state.map[-1, 0] == Block.EMPTY

            # soft requirements (any must be true)
            if drop:
                # just have too many unused oils
                drop = self.state.oils > 5

                # other player is right behind us
                drop = drop or (self.state.y == self.state.opp_y and
                        (self.state.x - self.state.opp_x) <= 5)
                # tight spot
                if not drop:
                    if self.state.map.rel_min_y < 0:
                        left_blocked = self.state.map[-1, -1] == Block.MUD
                    else:
                        left_blocked = True

                    if self.state.map.rel_max_y > 0:
                        right_blocked = self.state.map[-1, 1] == Block.MUD
                    else:
                        right_blocked = True

                    drop = drop or (left_blocked and right_blocked)

            if drop:
                cmd = Cmd.OIL

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
