import copy

from map import Map
from enums import Cmd, Block, Speed, prev_speed, next_speed

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

# calculates the new state from the current state based on a given cmd
def next_state(state, cmd):
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
def final_state(cur_state, actions, cache):
    for cmd in actions:
        ## check if the state + cmd has been cached - cache holds next state
        pk = (cur_state, cmd)
        if pk in cache:
            cur_state = cache[pk]
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
        ns = next_state(cur_state, cmd)

        ## store in cache
        cache[pk] = ns

        ## set next state
        cur_state = ns

    return cur_state
