import copy

from sloth.enums import Speed, next_speed, prev_speed, Cmd, Block

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
            self.boosts = len([b for b in powerups if b == 'BOOST'])
            self.oils = len([o for o in powerups if o == 'OIL'])
            self.lizards = len([o for o in powerups if o == 'LIZARD'])
            self.tweets = len([o for o in powerups if o == 'TWEET'])

            self.boosting = raw_player['boosting']
            self.boost_counter = raw_player['boostCounter']
        else:
            self.boosts = 0
            self.oils = 0
            self.lizards = 0
            self.tweets = 0

            self.boosting = False
            self.boost_counter = 0

        # cannot be read directly from the state file
        self.score = 0

    # transfer this player's mods to another (mods being boosts, oils, etc.)
    def transfer_mods(self, other):
        other.boosts = self.boosts
        other.oils = self.oils
        other.lizards = self.lizards
        other.tweets = self.tweets

        other.boosting = self.boosting
        other.boost_counter = self.boost_counter

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
        return hash((self.player, self.opponent))

    def __eq__(self, other):
        return (self.player, self.opponent) == (other.player, other.opponent)

class Trajectory:
    def __init__(self):
        self.x_off = 0
        self.y_off = 0
        self.speed = 0

    def next_speed(self):
        self.speed = next_speed(self.speed)

    # if min_stop == True then the speed won't go below SPEED_1
    def prev_speed(self, min_stop=False):
        if min_stop:
            if self.speed > Speed.SPEED_1.value:
                self.speed = prev_speed(self.speed)
        else:
            self.speed = prev_speed(self.speed)

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
        self.speed = Speed.BOOST_SPEED.value
        self.straight()

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

        self.penalties = 0
        self.score = 0

        # for any obstacles that were consumed/destroyed in the process
        self.consumed = {
            'cybertrucks': []
        }

    def penalise(self, block):
        self.penalties += 1
        if block == Block.MUD:
            self.score -= 3
        elif block == Block.OIL_SPILL:
            self.score -= 4
        elif block == Block.WALL:
            self.score -= 5
        elif block == Block.CYBERTRUCK:
            self.score -= 7

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

    def hit_cybertruck(self, pos):
        self.consumed['cybertrucks'].append(pos)

    def apply(self, player):
        player.oils += self.oils
        player.boosts += self.boosts
        player.lizards += self.lizards
        player.tweets += self.tweets

        player.score += self.score

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
    valid = [Cmd.NOP]

    if state.player.speed < Speed.MAX_SPEED.value:
        valid.append(Cmd.ACCEL)
    # if state.player.speed > Speed.MIN_SPEED.value:
    #     valid.append(Cmd.DECEL)
    if state.player.y > state.map.min_y:
        valid.append(Cmd.LEFT)
    if state.player.y < state.map.max_y:
        valid.append(Cmd.RIGHT)
    if state.player.boosts > 0 and not state.player.boosting:
        valid.append(Cmd.BOOST)
    if state.player.lizards > 0:
        valid.append(Cmd.LIZARD)

    return valid

def calc_trajectory(player, cmd):
    traj = Trajectory()
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
    elif cmd == Cmd.OIL:
        traj.straight()
    elif cmd == Cmd.LIZARD:
        traj.straight()
    elif cmd == Cmd.TWEET:
        traj.straight()

    return traj

def calc_path_mods(state_map, player, traj, lizarding):
    path_mods = PathMods()

    if not lizarding:
        start = player.x if traj.y_off else player.x + 1
    else:
        start = player.x + traj.x_off
    end = player.x + traj.x_off
    y = player.y + traj.y_off
    for x in range(start, end + 1):
        # went outside the map
        if x >= state_map.global_map.max_x:
            break

        block = state_map[x, y]

        if block == Block.EMPTY:
            pass
        elif block == Block.MUD or block == Block.OIL_SPILL:
            traj.prev_speed(min_stop=True)
            path_mods.penalise(block)
        elif block == Block.WALL:
            traj.min_speed()
            path_mods.penalise(block)
        elif block == Block.CYBERTRUCK:
            traj.min_speed()
            # stop right before cybertruck
            traj.x_off = x - player.x - 1
            path_mods.penalise(block)
            path_mods.hit_cybertruck((x, y))
            break
        elif block == Block.OIL_ITEM:
            path_mods.oil_pickup()
        elif block == Block.BOOST:
            path_mods.boost_pickup()
        elif block == Block.LIZARD:
            path_mods.lizard_pickup()
        elif block == Block.TWEET:
            path_mods.tweet_pickup()

    return path_mods

# calculates the next state given the player and opponent's cmd
# NOTE it is assumed that both cmds are valid movement cmds
# NOTE offensive cmds are not supported
def next_state(state, cmd, opp_cmd):
    state = state.copy()

    ## keep track of boosting counters
    def count_boosting(player):
        if player.boosting:
            player.boost_counter -= 1
            # boost ran out
            if player.boost_counter == 0:
                player.boosting = False
                player.speed = Speed.MAX_SPEED.value

    count_boosting(state.player)
    count_boosting(state.opponent)

    ## calculate trajectories

    player_traj = calc_trajectory(state.player, cmd)
    opp_traj = calc_trajectory(state.opponent, opp_cmd)

    ## check for powerups that were used and consume them

    def track_powerups(player, cmd):
        if cmd == Cmd.BOOST:
            player.boosts -= 1
            player.boosting = True
            player.boost_counter = 5
            player.score += 4
        elif cmd == Cmd.LIZARD:
            player.lizards -= 1
            player.score += 4

    track_powerups(state.player, cmd)
    track_powerups(state.opponent, opp_cmd)

    ## check for collisions
    # two types: fender-bender from behind or ending up on same block
    # FIXME check for lizarding

    def check_collisions(player_a, player_b, traj_a, traj_b):
        # run-in from behind - occurs when in the same lane and one bot tries to
        # drive through the other. conditions:
        # started in the same lane
        # ended in the same lane
        # one passed the other during the round

        # player that was behind ends up one block behind the player that was in
        # front at the start of the turn

        started_same = player_a.y == player_b.y
        ended_same = traj_a.y_off == traj_b.y_off
        started_ahead = player_a.x > player_b.x
        ended_ahead = player_a.x + traj_a.x_off > player_b.x + traj_b.x_off
        drove_through = started_ahead != ended_ahead

        if started_same and ended_same and drove_through:
            # whoever is behind cannot pass the player in front
            # check if player a started ahead
            if started_ahead:
                traj_b.x_off = player_a.x + traj_a.x_off - 1 - player_b.x
            else:
                traj_a.x_off = player_b.x + traj_b.x_off - 1 - player_a.x

        # same destination block
        # both players stay in the same lane and their x_off gets decremented
        # by 1
        x_same = player_a.x + traj_a.x_off == player_b.x + traj_b.x_off
        y_same = player_a.y + traj_a.y_off == player_b.y + traj_b.y_off

        if x_same and y_same:
            # -1 x_off penalty
            traj_a.x_off -= 1
            traj_b.x_off -= 1

            # back to original lane
            traj_a.y_off = 0
            traj_b.y_off = 0

    check_collisions(state.player, state.opponent, player_traj, opp_traj)

    ## check players' path for penalties and powerups

    player_mods = calc_path_mods(state.map, state.player, player_traj,
                                 cmd == Cmd.LIZARD)
    opp_mods = calc_path_mods(state.map, state.opponent, opp_traj,
                              opp_cmd == Cmd.LIZARD)

    consumed = player_mods.consumed
    consumed = {k: consumed[k] + opp_mods.consumed[k] for k in consumed}

    ## apply trajectories and mods

    player_traj.apply(state.player)
    opp_traj.apply(state.opponent)

    player_mods.apply(state.player)
    opp_mods.apply(state.opponent)

    ## check if boosting was cancelled

    def track_boosting(player):
        if player.boosting and player.speed != Speed.BOOST_SPEED.value:
            player.boosting = False
            player.boost_counter = 0

    track_boosting(state.player)
    track_boosting(state.opponent)

    ## keep track of cybertruck collisions

    def check_cybertrucks(state, consumed):
        ## remove cybertrucks that were crashed into
        for pos in consumed['cybertrucks']:
            x, y = pos
            state.map[x, y].unset_cybertruck()

    check_cybertrucks(state, consumed)

    return state

# given the player's cmd, the initial state and the state thereafter this
# calculates cmd the opponent took. returns None if unable to figure out.
# note that this only attempts to calculate cmds that were movement cmds, so
# offensive cmds like oil and tweeting will be calculated as NOP
def calc_opp_cmd(cmd, from_state, to_state):
    x, y = from_state.opponent.x, from_state.opponent.y
    speed = from_state.opponent.speed

    fx, fy = to_state.opponent.x, to_state.opponent.y
    fspeed = to_state.opponent.speed

    x_off = fx - x
    y_off = fy - y

    # check for operations that almost look like a NOP
    def check_nop():
        # TODO check for lizarding
        return Cmd.NOP

    # fast checks that will catch most of the actions taken by the opponent

    if y_off != 0:
        return Cmd.LEFT if y_off < 0 else Cmd.RIGHT

    # check if the opponent is not stuck behind us because that can mess with
    # x_off
    if fx != to_state.player.x - 1 or fy != to_state.player.y:
        if x_off == Speed.BOOST_SPEED.value > speed:
            return Cmd.BOOST
        if x_off == next_speed(speed) > speed:
            return Cmd.ACCEL
        if x_off == prev_speed(speed) < speed:
            return Cmd.DECEL
        if x_off == speed:
            return check_nop()

    # comprehensive search for rarer circumstances (e.g. collisions)
    for opp_cmd in valid_actions(from_state.switch()):
        ns = next_state(from_state, cmd, opp_cmd)
        if (ns.opponent.x,ns.opponent.y,ns.opponent.speed) == (fx,fy,fspeed):
            if opp_cmd == Cmd.NOP:
                return check_nop()
            return opp_cmd
    return None