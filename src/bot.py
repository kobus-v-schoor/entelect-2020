import logging
import json
import os
from collections import deque

from state import State
from enums import Speed, next_speed, prev_speed, Block, Cmd, CMD_SEARCH

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

    # calculates what the probable next state for the opponent will be
    def opponent_next_state(self, state):
        return state

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

        # calculate next possible move for opponent
        ns = self.opponent_next_state(ns)

        # check what we drove over
        for x in range(0 if y_off else 1, x_off + 1):
            if x >= ns.map.rel_max_x:
                break
            block = ns.map[x, y_off]
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
