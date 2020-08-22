import copy
from functools import lru_cache

from sloth.enums import (Speed, next_speed, prev_speed, Cmd, Block,
                         boost_speed, max_speed)

class Player:
    def __init__(self, raw_player):
        # id
        self.id = raw_player['id']

        # position and speed
        self.x = raw_player['position']['x']
        self.y = raw_player['position']['y']
        self.speed = raw_player['speed']

        # powerup info if available
        if 'powerups' in raw_player:
            powerups = raw_player['powerups']
            self.boosts = powerups.count('BOOST')
            self.oils = powerups.count('OIL')
            self.lizards = powerups.count('LIZARD')
            self.tweets = powerups.count('TWEET')
            self.emps = powerups.count('EMP')

            self.boosting = raw_player['boosting']
            self.boost_counter = raw_player['boostCounter']

            self.damage = raw_player.get('damage', 0)
            self.score = raw_player.get('score', 0)
        else:
            self.boosts = 0
            self.oils = 0
            self.lizards = 0
            self.tweets = 0
            self.emps = 0

            self.boosting = False
            self.boost_counter = 0

            self.damage = 0
            self.score = 0

    # transfer this player's mods to another (mods being boosts, oils, etc.)
    def transfer_mods(self, other):
        other.boosts = self.boosts
        other.oils = self.oils
        other.lizards = self.lizards
        other.tweets = self.tweets
        other.emps = self.emps

        other.boosting = self.boosting
        other.boost_counter = self.boost_counter

        other.score = self.score
        other.damage = self.damage

    def __hash__(self):
        return hash(tuple(vars(self).values()))

    def __eq__(self, other):
        return tuple(vars(self).values()) == tuple(vars(other).values())

    def __repr__(self):
        return str(vars(self))

class State:
    def __init__(self):
        self.map = None
        self.player = None
        self.opponent = None

    # returns a copy of the state with the player and opponent switched
    def switch(self):
        cp = self.copy()
        cp.map.move_window(cp.player.x, cp.opponent.x)
        cp.player, cp.opponent = cp.opponent, cp.player
        return cp

    def copy(self):
        return copy.deepcopy(self)

    def __repr__(self):
        return str(vars(self))

    def __hash__(self):
        return hash((self.player, self.opponent, self.map))

    def __eq__(self, other):
        return ((self.player, self.opponent, self.map) ==
                (other.player, other.opponent, other.map))

class Trajectory:
    def __init__(self, damage):
        self.x_off = 0
        self.y_off = 0
        self.speed = 0
        self.damage = damage
        self.collided = False

    def next_speed(self):
        self.speed = next_speed(self.speed, self.damage)

    # if min_stop == True then the speed won't go below SPEED_1
    def prev_speed(self, min_stop=False):
        if min_stop:
            if self.speed > Speed.SPEED_1.value:
                self.speed = prev_speed(self.speed, self.damage)
        else:
            self.speed = prev_speed(self.speed, self.damage)

    def min_speed(self):
        self.speed = Speed.SPEED_1.value

    def accel(self):
        self.next_speed()
        self.straight()

    def decel(self):
        self.prev_speed()
        self.straight()

    def left(self):
        if self.speed > 0:
            self.y_off -= 1
            self.x_off += self.speed - 1

    def right(self):
        if self.speed > 0:
            self.y_off += 1
            self.x_off += self.speed - 1

    def straight(self):
        self.x_off += self.speed

    def boost(self):
        self.speed = boost_speed(self.damage)
        self.straight()

    def still(self):
        pass

    def apply(self, player):
        player.x += self.x_off
        player.y += self.y_off
        player.speed = self.speed

    def __repr__(self):
        return str(vars(self))

class PathMods:
    def __init__(self):
        self.oils = 0
        self.boosts = 0
        self.lizards = 0
        self.tweets = 0
        self.emps = 0

        self.penalties = 0
        self.damage = 0
        self.score = 0

        # for any obstacles that were consumed/destroyed in the process
        self.consumed = {
            'cybertrucks': []
        }

    def penalise(self, block):
        self.penalties += 1
        if block == Block.MUD:
            self.score -= 3
            self.damage += 1
        elif block == Block.OIL_SPILL:
            self.score -= 4
            self.damage += 1
        elif block == Block.WALL:
            self.score -= 5
            self.damage += 2
        elif block == Block.CYBERTRUCK:
            self.score -= 7
            self.damage += 2

    def oil_pickup(self):
        self.oils += 1
        self.score += 4

    def boost_pickup(self):
        self.boosts += 1
        self.score += 4

    def lizard_pickup(self):
        self.lizards += 1
        self.score += 4

    def tweet_pickup(self):
        self.tweets += 1
        self.score += 4

    def emp_pickup(self):
        self.emps += 1
        self.score += 4

    def hit_cybertruck(self, pos):
        self.consumed['cybertrucks'].append(pos)

    def apply(self, player):
        player.oils += self.oils
        player.boosts += self.boosts
        player.lizards += self.lizards
        player.tweets += self.tweets
        player.emps += self.emps

        player.score += self.score
        player.damage = min(player.damage + self.damage, 5)

        if player.boosting and self.penalties > 0:
            player.boosting = False
            player.boost_counter = 0

    def __repr__(self):
        return str(vars(self))

class StateTransition:
    def __init__(self, round_num, cmd, from_state, to_state):
        self.round_num = round_num
        self.cmd = cmd
        self.from_state = from_state
        self.to_state = to_state

# returns a list of valid movement actions for a given state
def valid_actions(state):
    valid = []

    if state.player.speed < max_speed(state.player.damage):
        valid.append(Cmd.ACCEL)

    if state.player.speed > 0:
        valid.append(Cmd.NOP)
        valid.append(Cmd.DECEL)

        if state.player.y > state.map.min_y:
            valid.append(Cmd.LEFT)
        if state.player.y < state.map.max_y:
            valid.append(Cmd.RIGHT)
        if state.player.lizards > 0:
            valid.append(Cmd.LIZARD)

    if state.player.damage > 0:
        valid.append(Cmd.FIX)
    if state.player.boosts > 0:
        if state.player.speed < boost_speed(state.player.damage):
            valid.append(Cmd.BOOST)
        if state.player.boost_counter == 1:
            valid.append(Cmd.BOOST)

    return valid

def count_boosting(player):
    if player.boosting:
        player.boost_counter -= 1
        # boost ran out
        if player.boost_counter == 0:
            player.boosting = False
            player.speed = max_speed(player.damage)

def calc_trajectory(player, cmd):
    traj = Trajectory(player.damage)
    traj.speed = player.speed

    if cmd == Cmd.NOP:
        traj.straight()
    elif cmd == Cmd.ACCEL:
        traj.accel()
    elif cmd == Cmd.DECEL:
        traj.decel()
    elif cmd == Cmd.LEFT:
        traj.left()
    elif cmd == Cmd.RIGHT:
        traj.right()
    elif cmd == Cmd.BOOST:
        traj.boost()
    elif cmd == Cmd.LIZARD:
        traj.straight()
    elif cmd == Cmd.FIX:
        traj.still()

    return traj

def check_fix(player, cmd):
    if cmd != Cmd.FIX:
        return
    player.damage = max(0, player.damage - 2)

def track_powerups(player, cmd):
    if cmd == Cmd.BOOST:
        player.boosts -= 1
        player.boosting = True
        player.boost_counter = 5
        player.score += 4
    elif cmd == Cmd.LIZARD:
        player.lizards -= 1
        player.score += 4

def check_collisions(player_a, player_b, traj_a, traj_b, a_lizarding,
                     b_lizarding):
    # two types: fender-bender from behind or ending up on same block

    # run-in from behind - occurs when in the same lane and one bot tries
    # to drive through the other. conditions:
    # started in the same lane
    # ended in the same lane
    # one passed the other during the round
    # none of the players were lizarding

    # player that was behind ends up one block behind the player that was
    # in front at the start of the turn

    started_same_lane = player_a.y == player_b.y
    ended_same_lane = traj_a.y_off == traj_b.y_off
    a_started_ahead = player_a.x > player_b.x
    any_player_lizards = a_lizarding or b_lizarding
    a_ended_ahead = player_a.x + traj_a.x_off > player_b.x + traj_b.x_off
    b_ended_ahead = player_b.x + traj_b.x_off > player_a.x + traj_a.x_off

    # both players end up on the same block
    if a_ended_ahead == b_ended_ahead:
        a_ended_ahead = not a_started_ahead

    drove_through = a_started_ahead != a_ended_ahead and not any_player_lizards

    if started_same_lane and ended_same_lane and drove_through:
        # whoever is behind cannot pass the player in front
        # check if player a started ahead
        if a_started_ahead:
            traj_b.x_off = player_a.x + traj_a.x_off - 1 - player_b.x
            traj_b.collided = True
        else:
            traj_a.x_off = player_b.x + traj_b.x_off - 1 - player_a.x
            traj_a.collided = True

    # same destination block
    # both players stay in the same lane and their x_off gets decremented
    # by 1
    x_same = player_a.x + traj_a.x_off == player_b.x + traj_b.x_off
    y_same = player_a.y + traj_a.y_off == player_b.y + traj_b.y_off

    if x_same and y_same:
        if not any_player_lizards:
            # -1 x_off penalty
            traj_a.x_off -= 1
            traj_b.x_off -= 1

            # back to original lane
            traj_a.y_off = 0
            traj_b.y_off = 0

            traj_a.collided = True
            traj_b.collided = True
        else:
            # if players ended up on same block but one player was lizarding,
            # the one that was behind should end up one block behind the other
            # one (like a normal rear-end)
            if a_started_ahead:
                traj_b.x_off = player_a.x + traj_a.x_off - 1 - player_b.x
                traj_b.collided = True
            else:
                traj_a.x_off = player_b.x + traj_b.x_off - 1 - player_a.x
                traj_a.collided = True

def gen_path(state_map, player, traj, lizarding):
    # didn't move at all, so no path to generate
    if traj.x_off == traj.y_off == 0:
        return

    if not lizarding:
        # player collided edge case
        if traj.y_off and not traj.collided:
            start = player.x
        else:
            start = player.x + 1
    else:
        start = player.x + traj.x_off
    end = player.x + traj.x_off

    y = player.y + traj.y_off
    for x in range(start, end + 1):
        # went outside the map
        if x >= state_map.global_map.max_x:
            break
        yield (x, y)

def resolve_cybertruck_collisions(state_map, player, traj, lizarding):
    path_mods = PathMods()

    for x, y in gen_path(state_map, player, traj, lizarding):
        block = state_map[x, y]

        if block == Block.CYBERTRUCK:
            traj.min_speed()
            # stop right before cybertruck
            traj.x_off = x - player.x - 1
            path_mods.penalise(block)
            path_mods.hit_cybertruck((x, y))
            break

    return path_mods

def calc_path_mods(state_map, player, traj, lizarding):
    path_mods = PathMods()

    for x, y in gen_path(state_map, player, traj, lizarding):
        block = state_map[x, y]

        if block == Block.EMPTY:
            pass
        elif block == Block.MUD or block == Block.OIL_SPILL:
            traj.prev_speed(min_stop=True)
            path_mods.penalise(block)
        elif block == Block.WALL:
            traj.min_speed()
            path_mods.penalise(block)
        elif block == Block.OIL_ITEM:
            path_mods.oil_pickup()
        elif block == Block.BOOST:
            path_mods.boost_pickup()
        elif block == Block.LIZARD:
            path_mods.lizard_pickup()
        elif block == Block.TWEET:
            path_mods.tweet_pickup()
        elif block == Block.EMP:
            path_mods.emp_pickup()

    return path_mods

def check_cybertrucks(state, consumed):
    ## remove cybertrucks that were crashed into
    for pos in consumed['cybertrucks']:
        x, y = pos
        state.map[x, y] = state.map[x, y].get_underlay()

# caps the player's speed to its maximum allowable value given their damage
def cap_speed(player):
    if not player.boosting:
        player.speed = min(max_speed(player.damage), player.speed)

# checks that when a player decelerates their boosting is canceled
def decel_boost_cancel(player, cmd):
    if player.boosting and cmd == Cmd.DECEL:
        player.boosting = False
        player.boost_counter = 0

# converts offensive actions to a NOP so that they can be passed to next_state
def ns_filter(cmd):
    if cmd in [Cmd.OIL, Cmd.TWEET, Cmd.EMP]:
        return Cmd.NOP
    return cmd

# calculates the next state given the player and opponent's cmd
# NOTE it is assumed that both cmds are valid movement cmds
# NOTE offensive cmds are not supported
@lru_cache(maxsize=None)
def next_state(state, cmd, opp_cmd):
    state = state.copy()

    ## keep track of boosting counters
    count_boosting(state.player)
    count_boosting(state.opponent)

    ## calculate trajectories
    player_traj = calc_trajectory(state.player, cmd)
    opp_traj = calc_trajectory(state.opponent, opp_cmd)

    ## check fixes
    check_fix(state.player, cmd)
    check_fix(state.opponent, opp_cmd)

    ## check for powerups that were used and consume them
    track_powerups(state.player, cmd)
    track_powerups(state.opponent, opp_cmd)

    ## check for cybertruck collisions
    player_cyber_mods = resolve_cybertruck_collisions(state.map, state.player,
                                                      player_traj,
                                                      cmd == Cmd.LIZARD)
    opp_cyber_mods = resolve_cybertruck_collisions(state.map, state.opponent,
                                                      opp_traj,
                                                      opp_cmd == Cmd.LIZARD)

    player_cyber_mods.apply(state.player)
    opp_cyber_mods.apply(state.opponent)

    consumed = player_cyber_mods.consumed
    consumed = {k: consumed[k] + opp_cyber_mods.consumed[k] for k in consumed}

    ## check for collisions
    check_collisions(state.player, state.opponent, player_traj, opp_traj,
                     cmd == Cmd.LIZARD, opp_cmd == Cmd.LIZARD)

    ## check players' path for penalties and powerups
    player_mods = calc_path_mods(state.map, state.player, player_traj,
                                 cmd == Cmd.LIZARD)
    opp_mods = calc_path_mods(state.map, state.opponent, opp_traj,
                              opp_cmd == Cmd.LIZARD)

    consumed = {k: consumed[k] + player_mods.consumed[k] for k in consumed}
    consumed = {k: consumed[k] + opp_mods.consumed[k] for k in consumed}

    ## apply trajectories and mods
    player_traj.apply(state.player)
    opp_traj.apply(state.opponent)

    player_mods.apply(state.player)
    opp_mods.apply(state.opponent)

    ## check if boosting was cancelled by decelerating
    decel_boost_cancel(state.player, cmd)
    decel_boost_cancel(state.opponent, opp_cmd)

    ## keep track of cybertruck collisions
    check_cybertrucks(state, consumed)

    ## cap speed after damage
    cap_speed(state.player)
    cap_speed(state.opponent)

    return state

# given the player's cmd, the initial state and the state thereafter this
# calculates cmd the opponent took. returns None if unable to figure out.
# note that this only attempts to calculate cmds that were movement cmds, so
# offensive cmds like oil and tweeting will be calculated as NOP
def calc_opp_cmd(cmd, from_state, to_state):
    # no way to know what they were going to do
    if cmd == Cmd.EMP:
        return None

    cmd = ns_filter(cmd)

    x, y = from_state.opponent.x, from_state.opponent.y

    # if their boost counter was one their effective speed was actually 9
    if from_state.opponent.boost_counter == 1:
        from_state.opponent.speed = max_speed(from_state.opponent.damage)
    speed = from_state.opponent.speed

    fx, fy = to_state.opponent.x, to_state.opponent.y
    fspeed = to_state.opponent.speed

    x_off = fx - x
    y_off = fy - y

    # go through all the valid actions that they could've taken and check if
    # the next state matches their actual state
    for opp_cmd in valid_actions(from_state.switch()):
        nstate = next_state(from_state, cmd, opp_cmd)
        if ((nstate.opponent.x, nstate.opponent.y, nstate.opponent.speed) ==
                (fx, fy, fspeed)):
            return opp_cmd

    # above didn't work, so try figure out what they did based on some
    # rudimentary rules

    if y_off:
        return Cmd.LEFT if y_off < 0 else Cmd.RIGHT

    if x_off == y_off == 0 and fspeed == speed:
        return Cmd.FIX

    if x_off > speed:
        if x_off <= next_speed(speed):
            return Cmd.ACCEL
        else:
            return Cmd.BOOST

    if x_off == prev_speed(speed):
        return Cmd.DECEL

    if x_off == speed:
        _y = fy
        _speed = speed
        start_x = x if y_off else x + 1

        for _x in range(start_x, fx + 1):
            block = from_state.map[_x, _y]

            if block == Block.MUD:
                _speed = prev_speed(_speed)
            elif block == Block.OIL_SPILL:
                _speed = prev_speed(_speed)
            elif block == Block.WALL:
                _speed = Speed.SPEED_1.value

        _speed = max(Speed.SPEED_1.value, _speed)
        return Cmd.LIZARD if _speed < fspeed else Cmd.NOP

    return None
