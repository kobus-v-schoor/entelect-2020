# Author: Kobus van Schoor

import logging
import os
import json

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class BLOCK:
    __slots__ = ()

    EMPTY = 0
    MUD = 1
    OIL_SPILL = 2
    OIL_ITEM = 3
    FINISH_LINE = 4
    BOOST = 5

BLOCK = BLOCK()

class SPEED:
    __slots__ = ()

    MIN_SPEED = 0
    SPEED_1 = 1
    SPEED_2 = 6
    SPEED_3 = 8
    MAX_SPEED = 9

    INIT_SPEED = 5
    BOOST_SPEED = 15

    STEPS = [MIN_SPEED, SPEED_1, SPEED_2, SPEED_3, MAX_SPEED]

SPEED = SPEED()

class CMD:
    __slots__ = ()

    NOP = 'NOTHING'

    ACCEL = 'ACCELERATE'
    DECEL = 'DECELERATE'
    LEFT = 'TURN_LEFT'
    RIGHT = 'TURN_RIGHT'

    BOOST = 'USE_BOOST'
    OIL = 'USE_OIL'

CMD = CMD()

class Map:
    def __init__(self, x, y, world_map):
        # flatten map
        world_map = [w for row in world_map for w in row]

        # find bounds
        min_x = min(world_map, key=lambda w:w['position']['x'])['position']['x']
        max_x = max(world_map, key=lambda w:w['position']['x'])['position']['x']
        min_y = min(world_map, key=lambda w:w['position']['y'])['position']['y']
        max_y = max(world_map, key=lambda w:w['position']['y'])['position']['y']

        # generate map
        rows = max_y - min_y + 1
        cols = max_x - min_x + 1

        # order: map[x][y]
        self.map = [[BLOCK.EMPTY for _ in range(rows)] for _ in range(cols)]

        # fill in map
        for w in world_map:
            mx = w['position']['x']
            my = w['position']['y']
            self.map[mx - min_x][my - min_y] = w['surfaceObject']

        # player position
        self.x = x
        self.y = y

        self.min_x = min_x - x
        self.max_x = max_x - x
        self.min_y = min_y - y
        self.max_y = max_y - y

    def __getitem__(self, key):
        x, y = key

        if self.min_x <= x <= self.max_x:
            if self.min_y <= y <= self.max_y:
                return self.map[x - self.min_x][y - self.min_y]
        raise IndexError

class Bot:
    def __init__(self):
        self.next_round = None

        # state variables
        self.speed = None
        self.boosts = None
        self.oils = None
        self.boosting = None
        self.boost_count = None
        self.x = None
        self.y = None
        self.opp_x = None
        self.opp_y = None
        self.map = None

        self.finished = False

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
                self.state = json.load(f)
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

        if self.state['player']['state'] == 'FINISHED':
            log.debug('detected finished state')
            self.finished = True
            return

        # current speed
        self.speed = self.state['player']['speed']

        # powerups
        powerups = self.state['player']['powerups']
        self.boosts = len([x for x in powerups if x == 'BOOST'])
        self.oils = len([x for x in powerups if x == 'OIL'])

        # boosting
        self.boosting = self.state['player']['boosting']
        self.boost_count = self.state['player']['boostCounter']

        # position
        self.x = self.state['player']['position']['x']
        self.y = self.state['player']['position']['y']

        # opponent position
        self.opp_x = self.state['opponent']['position']['x']
        self.opp_y = self.state['opponent']['position']['y']

        # parse map
        self.map = Map(self.x, self.y, self.state['worldMap'])

        log.debug('finished parsing state')

    # executes the given cmd for the current round
    def exec(self, cmd):
        log.info(f'exec {cmd} for round {self.next_round}')
        print(f'C;{self.next_round};{cmd}')

    def run(self):
        log.debug('bot started')

        while True:
            self.wait_for_next_round()
            if self.read_state():
                self.parse_state()

            if self.finished:
                log.info('bot finished playing')
                break

            # some logic
            # play some move
            self.exec(CMD.LEFT)


if __name__ == '__main__':
    log.info('starting bot')
    bot = Bot()
    bot.run()
