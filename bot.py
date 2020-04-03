# Author: Kobus van Schoor

import logging
import os
import json
import enum
import copy
from collections import deque

logging.basicConfig(filename='bot.log', filemode='w', level=logging.INFO)
log = logging.getLogger(__name__)

class Block(enum.Enum):
    EMPTY = 0
    MUD = 1
    OIL_SPILL = 2
    OIL_ITEM = 3
    FINISH_LINE = 4
    BOOST = 5

class Speed(enum.Enum):
    MIN_SPEED = 0
    SPEED_1 = 1
    SPEED_2 = 6
    SPEED_3 = 8
    MAX_SPEED = 9

    INIT_SPEED = 5
    BOOST_SPEED = 15

SPEED_STEPS = [
        Speed.MIN_SPEED.value,
        Speed.SPEED_1.value,
        Speed.SPEED_2.value,
        Speed.SPEED_3.value,
        Speed.MAX_SPEED.value,
        ]

def next_speed(speed):
    try:
        return next(s for s in SPEED_STEPS if s > speed)
    except StopIteration:
        return SPEED_STEPS[-1]

def prev_speed(speed):
    try:
        return next(s for s in SPEED_STEPS[::-1] if s < speed)
    except StopIteration:
        return SPEED_STEPS[0]

class Cmd(enum.Enum):
    NOP = 'NOTHING'

    ACCEL = 'ACCELERATE'
    DECEL = 'DECELERATE'
    LEFT = 'TURN_LEFT'
    RIGHT = 'TURN_RIGHT'

    BOOST = 'USE_BOOST'
    OIL = 'USE_OIL'

CMD_SEARCH = [
        Cmd.NOP,
        Cmd.ACCEL,
        # Cmd.DECEL, # never used, taken out to improve performance
        Cmd.LEFT,
        Cmd.RIGHT,
        Cmd.BOOST,
        # Cmd.OIL, # only used when doing nothing else
        ]

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

class Map:
    def __init__(self, x, y, world_map):
        # flatten map
        world_map = [w for row in world_map for w in row]

        # find bounds
        min_x = min(world_map, key=lambda w:w['position']['x'])['position']['x']
        max_x = max(world_map, key=lambda w:w['position']['x'])['position']['x']
        min_y = min(world_map, key=lambda w:w['position']['y'])['position']['y']
        max_y = max(world_map, key=lambda w:w['position']['y'])['position']['y']

        # store absolute minimum and maximum values
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

        # generate map
        rows = max_y - min_y + 1
        cols = max_x - min_x + 1

        # order: map[x][y]
        self.map = [[Block.EMPTY for _ in range(rows)] for _ in range(cols)]

        # fill in map
        for w in world_map:
            mx = w['position']['x']
            my = w['position']['y']
            self.map[mx - min_x][my - min_y] = w['surfaceObject']

        self.update_xy(x, y)

    def update_xy(self, x, y):
        # player position
        self.x = x
        self.y = y

        # these are relative, meaning that if rel_min_y == 0 then you cannot
        # move further to the right - same goes for rel_max_y, if rel_max_y == 0
        # you cannot go further to the left
        self.rel_min_x = self.min_x - x
        self.rel_max_x = self.max_x - x
        self.rel_min_y = self.min_y - y
        self.rel_max_y = self.max_y - y

    # returns the map item relative to the current position with order [x,y]
    # this means that [0, 0] returns the current block, [1,-1] returns one block
    # to the right and one block back
    # use rel_min and rel_max variables for bounds
    def __getitem__(self, key):
        x, y = key

        if self.rel_min_x <= x <= self.rel_max_x:
            if self.rel_min_y <= y <= self.rel_max_y:
                return self.map[x - self.rel_min_x][y - self.rel_min_y]
        raise IndexError

    def __setitem__(self, key, val):
        x, y = key

        if self.rel_min_x <= x <= self.rel_max_x:
            if self.rel_min_y <= y <= self.rel_max_y:
                self.map[x - self.rel_min_x][y - self.rel_min_y] = val
                return
        raise IndexError

class State:
    def __init__(self, raw_state):
        # powerups
        powerups = raw_state['player']['powerups']
        self.boosts = len([x for x in powerups if x == 'BOOST'])
        self.oils = len([x for x in powerups if x == 'OIL'])

        # current boosting state
        self.boosting = raw_state['player']['boosting']
        self.boost_count = raw_state['player']['boostCounter']

        # position and speed
        self.speed = raw_state['player']['speed']
        self.x = raw_state['player']['position']['x']
        self.y = raw_state['player']['position']['y']

        # opponent position and speed
        self.opp_x = raw_state['opponent']['position']['x']
        self.opp_y = raw_state['opponent']['position']['y']
        self.opp_speed = raw_state['opponent']['speed']

        # used to keep track of penalties incurred
        self.penalties = 0

        # map
        self.map = Map(self.x, self.y, raw_state['worldMap'])

    def update_map(self):
        self.map.update_xy(self.x, self.y)

    # returns a deep copy of this state
    def copy(self):
        return copy.deepcopy(self)

    # drops map from vars to exclude it from hashing and equality checks
    def exc_vars(self):
        return tuple([v for v in vars(self).values() if not type(v) is Map])

    def __eq__(self, other):
        return self.exc_vars() == other.exc_vars()

    # this hash will be the same for equal states
    def __hash__(self):
        return hash(self.exc_vars())

    def __repr__(self):
        return str(self.exc_vars())

class Bot:
    def __init__(self):
        self.next_round = None
        self.state = None
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

        # purge old state cmd cache
        self.state_cmd_cache = {}

        log.debug('finished parsing state')

    # executes the given cmd for the current round
    def exec(self, cmd):
        log.info(f'exec {cmd} for round {self.next_round}')
        print(f'C;{self.next_round};{cmd.value}')

    # calculates the new state from the current state based on a given cmd
    def next_state(self, state, cmd):
        ns = state.copy() # next state variable

        # apply movement modifications
        x_off, y_off = 0, 0

        if cmd == Cmd.NOP:
            x_off = ns.speed
        elif cmd == Cmd.ACCEL:
            ns.speed = next_speed(ns.speed)
            x_off = ns.speed
        elif cmd == Cmd.DECEL:
            ns.speed = prev_speed(ns.speed)
            x_off = ns.speed
        elif cmd == Cmd.LEFT:
            y_off = -1
            x_off = ns.speed - 1
        elif cmd == Cmd.RIGHT:
            y_off = 1
            x_off = ns.speed - 1
        elif cmd == Cmd.BOOST:
            ns.speed = Speed.BOOST_SPEED.value
            ns.boosts -= 1
            ns.boost_count = 6 # will be decremented to 5 at end of this func
            ns.boosting = True
            x_off = ns.speed
        elif cmd == Cmd.OIL:
            if ns.x - 1 < ns.map.max_x:
                ns.map[-1, 0] = Block.OIL_SPILL
            ns.oils -= 1
            x_off = ns.speed

        # check what we drove over
        for x in range(0 if y_off else 1, x_off + 1):
            if x >= ns.map.rel_max_x:
                break
            block = Block(ns.map[x, y_off])
            if block == Block.EMPTY:
                pass
            elif block == Block.MUD:
                ns.speed = prev_speed(ns.speed)
                ns.penalties += 1
            elif block == Block.OIL_SPILL:
                ns.speed = prev_speed(ns.speed)
                ns.penalties += 1
            elif block == Block.OIL_ITEM:
                ns.oils += 1
            elif block == Block.BOOST:
                ns.boosts += 1

        ns.x += x_off
        ns.y += y_off
        ns.update_map()

        # keep track of boosting
        if ns.boosting:
            # hit something or decel
            if ns.speed != Speed.BOOST_SPEED.value:
                ns.boost_count = 0
                ns.boosting = False
            else:
                ns.boost_count -= 1
                if ns.boost_count == 0:
                    ns.boosting = False
                    ns.speed = Speed.MAX_SPEED.value

        return ns

    # calculates the final state from the current state given a list of actions
    # if one of the actions are invalid it returns None
    def final_state(self, actions):
        cur_state = self.state.copy()

        for cmd in actions:
            ## check if the state + cmd has been cached - cache holds next state
            pk = (cur_state, cmd)
            if pk in self.state_cmd_cache:
                cur_state = self.state_cmd_cache[pk]
                continue

            ## filter out invalid cmds

            # already in the left-most lane
            if cmd == Cmd.LEFT and cur_state.y <= cur_state.map.min_y:
                return None
            # already in the right-most lane
            if cmd == Cmd.RIGHT and cur_state.y >= cur_state.map.max_y:
                return None
            # already at max speed
            if cmd == Cmd.ACCEL and cur_state.speed >= Speed.MAX_SPEED.value:
                return None
            # already at min speed
            if cmd == Cmd.DECEL and cur_state.speed <= Speed.MIN_SPEED.value:
                return None
            # doesn't have any oils to use
            if cmd == Cmd.OIL and cur_state.oils <= 0:
                return None
            # doesn't have any boosts to use
            if cmd == Cmd.BOOST and cur_state.boosts <= 0:
                return None
            # already boosting
            if cmd == Cmd.BOOST and cur_state.boosting:
                return None

            ## calculate next state
            next_state = self.next_state(cur_state, cmd)

            ## store in cache
            self.state_cmd_cache[pk] = next_state

            ## set next state
            cur_state = next_state

        return cur_state

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

        while queue:
            cur = queue.popleft()

            if cur.depth() == 0:
                queue += list(cur.children)
                continue

            actions = cur.path
            final_state = self.final_state(actions)

            if final_state is not None:
                if cur.depth() >= search_depth:
                    options.append((actions, final_state))
                else:
                    queue += list(cur.children)

        ## do sorting and selection
        def score(option):
            actions, final_state = option
            return sum([
                final_state.x - self.state.x,
                final_state.speed,
                # calculates potential benefit of new boosts * avg boost length
                (final_state.boosts - self.state.boosts) *
                (Speed.BOOST_SPEED.value - Speed.MAX_SPEED.value) * 1.63,
                ])

        # sort by scores
        options = sorted(options, key=score, reverse=True)

        # choose best option
        best_option = options[0]

        # wanted cmd is the first move in the best option
        cmd = best_option[0][0]

        # drop oil if doing nothing else
        # if cmd == Cmd.NOP and self.state.x > self.state.opp_x \
        #         and self.state.oils:
        #             cmd = Cmd.OIL

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


if __name__ == '__main__':
    log.info('starting bot')
    bot = Bot()
    bot.run()
