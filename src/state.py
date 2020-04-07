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
        return str({k: vars(self)[k] for k in vars(self) if not
            type(vars(self)[k]) is Map})

# calculates the new state from the current state based on a given cmd
# NOTE this function assumes that cmd is a valid command for the given state to
# remove reduntant checks for the validity of the commands
def next_state(state, cmd):
    state = state.copy()

    ## keep track of boosting
    if state.boosting:
        state.boost_count -= 1
        # boost ran out
        if state.boost_count == 0:
            state.boosting = False
            state.speed = Speed.MAX_SPEED.value

    ## calculate trajectories (x offset, y offset and new speed)
    def get_trajectory(x, y, speed, cmd):
        x_off, y_off = 0, 0

        if cmd == Cmd.NOP:
            x_off = speed
        elif cmd == Cmd.ACCEL:
            speed = next_speed(speed)
            x_off = speed
        elif cmd == Cmd.DECEL:
            speed = prev_speed(speed)
            x_off = speed
        elif cmd == Cmd.LEFT:
            y_off = -1
            x_off = speed - 1
        elif cmd == Cmd.RIGHT:
            y_off = 1
            x_off = speed - 1
        elif cmd == Cmd.BOOST:
            speed = Speed.BOOST_SPEED.value
            x_off = speed
        elif cmd == Cmd.OIL:
            x_off = speed

        return [x_off, y_off, speed]

    bot_traj = get_trajectory(state.x, state.y, state.speed, cmd)
    # TODO actually try and guess what the opponent will do
    opp_traj = get_trajectory(state.opp_x, state.opp_y, state.opp_speed,
            Cmd.ACCEL)

    ## check powerups that were used and consume them

    # drop oil
    if cmd == Cmd.OIL:
        state.oils -= 1
        # NOTE this only allows dropping oil in our current view, but this is
        # fine since it is the only place we would be able to drop an oil anyway
        if state.map.min_x <= state.x - 1 <= state.map.max_x:
            state.map[state.x - 1, state.y] = Block.OIL_SPILL

    # consume boost
    if cmd == Cmd.BOOST:
        state.boosts -= 1
        state.boosting = True
        state.boost_count = 5

    ## check for collisions
    # two types: end up on same block or fender-bender from behind

    # run-in from behind - occurs when in the same lane and one bot tries to
    # drive through the other. conditions:
    # started in the same lane
    # stayed in the same lane
    # one passed the other during the round
    if ((state.y == state.opp_y) and
            (bot_traj[1] == opp_traj[1] == 0) and
            ((state.x > state.opp_x) != (state.x + bot_traj[0] > state.opp_x +
                opp_traj[0]))):
                # whoever is behind cannot pass the one in front
                if state.x > state.opp_x:
                    opp_traj[0] = state.x + bot_traj[0] - 1 - state.opp_x
                else:
                    bot_traj[0] = state.opp_x + opp_traj[0] - 1 - state.x

    # same destination block
    if (state.x + bot_traj[0] == state.opp_x + opp_traj[0] and
            state.y + bot_traj[1] == state.opp_y + opp_traj[1]):
        # -1 speed penalty
        bot_traj[0] -= 1
        opp_traj[0] -= 1
        # take back to original lane
        bot_traj[1] = 0
        opp_traj[1] = 0

    ## check path for penalties and obstructions that player ran into
    def check_path(x, y, x_off, y_off, speed):
        oils, boosts, penalties = 0, 0, 0

        for cx in range(0 if y_off else 1, x_off + 1):
            if x + cx > state.map.max_x: # we're outside our current view
                break

            block = state.map[x + cx, y + y_off]

            if block == Block.EMPTY:
                pass
            elif block == Block.MUD or block == Block.OIL_SPILL:
                speed = max(Speed.SPEED_1.value, prev_speed(speed))
                penalties += 1
            elif block == Block.OIL_ITEM:
                oils += 1
            elif block == Block.BOOST:
                boosts += 1

        return (speed, oils, boosts, penalties)

    bot_path = check_path(state.x, state.y, *bot_traj)
    opp_path = check_path(state.opp_x, state.opp_y, *opp_traj)

    ## update this bot's state

    x_off, y_off, _ = bot_traj
    speed, oils, boosts, penalties = bot_path

    state.x += x_off
    state.y += y_off
    state.speed = speed
    state.oils += oils
    state.boosts += boosts
    state.penalties += penalties

    state.update_map()

    ## update opponent's state

    x_off, y_off, _ = opp_traj
    speed = opp_path[0]

    state.opp_x += x_off
    state.opp_y += y_off
    state.opp_speed = speed

    ## check if boost was cancelled
    if state.boosting and state.speed != Speed.BOOST_SPEED.value:
        state.boosting = False
        state.boost_count = 0

    return state

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
