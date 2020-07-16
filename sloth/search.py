import random
from collections import deque

from sloth.enums import Cmd, Speed
from sloth.state import valid_actions, next_state

class Weights:
    def __init__(self, raw_weights={}):
        if type(raw_weights) is dict:
            self.pos = raw_weights.get('pos', 0)
            self.speed = raw_weights.get('speed', 0)

            self.boosts = raw_weights.get('boosts', 0)
            self.oils = raw_weights.get('oils', 0)
            self.lizards = raw_weights.get('lizards', 0)
            self.tweets = raw_weights.get('tweets', 0)
            self.emps = raw_weights.get('emps', 0)

            self.damage = raw_weights.get('damage', 0)
            self.player_score = raw_weights.get('score', 0)
        else:
            (self.pos,
             self.speed,

             self.boosts,
             self.oils,
             self.lizards,
             self.tweets,
             self.emps,

             self.damage,
             self.player_score) = raw_weights

    # takes a from_state and to_state and calculates a numerical score
    def score(self, from_state, to_state):
        prev = from_state.player
        to = to_state.player
        return sum([
            self.pos * (to.x - prev.x),
            self.speed * to.speed,

            self.boosts * (to.boosts - prev.boosts),
            self.oils * (to.oils - prev.oils),
            self.lizards * (to.lizards - prev.lizards),
            self.tweets * (to.tweets - prev.tweets),
            self.emps * (to.emps - prev.emps),

            self.damage * (to.damage - prev.damage),
            self.player_score * (to.score - prev.score),
            ])

    # returns the amount of weights
    @staticmethod
    def len():
        return 9

    # encodes a from and to state into a numerical array
    @staticmethod
    def encode(from_state, to_state):
        return [
            to_state.player.x - from_state.player.x,
            to_state.player.speed,

            to_state.player.boosts - from_state.player.boosts,
            to_state.player.oils - from_state.player.oils,
            to_state.player.lizards - from_state.player.lizards,
            to_state.player.tweets - from_state.player.tweets,
            to_state.player.emps - from_state.player.emps,

            to_state.player.damage - from_state.player.damage,
            to_state.player.score - from_state.player.score,
        ]

    def __repr__(self):
        return str(vars(self))

# does a bfs search from the current state up to the first move that is outside
# the map's view or if the search depth reaches max_search_depth
# returns a list of tuples of the form (actions, final state) where actions are
# a list of actions taken which achieves the final state. opp_pred must be a
# callable that takes the current state as an argument and which will return a
# valid action for the opponent.
# this search only considers movement actions and not any offensive actions.
def search(state, opp_pred, max_search_depth):
    options = []

    # holds the bfs queue
    queue = deque([[]])

    while queue:
        actions = queue.popleft()
        cur_state = state.copy()

        for cmd in actions:
            # get opp cmd
            opp_cmd = opp_pred(cur_state)

            # calculate next state
            cur_state = next_state(cur_state, cmd, opp_cmd)

        # save final state
        options.append((actions, cur_state))

        # as soon as we find an action that can take us outside of our current
        # view we stop at this depth since it is pretty pointless to search
        # further
        if cur_state.player.x >= cur_state.map.max_x:
            max_search_depth = min(len(actions), max_search_depth)

        if len(actions) < max_search_depth:
            queue += [actions + [v] for v in valid_actions(cur_state)]

    # filter out action sequences that have invalid (too short) lengths
    options = [o for o in options if len(o[0]) == max_search_depth]

    return options

# does a movement search from the opponent's point of view.
def opp_search(state):
    state = state.switch()
    return search(state, lambda _: Cmd.ACCEL, max_search_depth=2)

# scores, ranks and returns the best scoring option. scores are calculated
# using the weights dict. state is the current state from which to score. if
# any of the actions results in the game being finished only the speeds are
# taken into account
def score(options, cur_state, weights):
    max_x = cur_state.map.global_map.max_x

    # check if any of actions result in a finish - we're in the endgame now
    if any(f.player.x >= max_x for _, f in options):
        key = lambda o: o[1].player.speed if o[1].player.x >= max_x else 0
    else:
        key = lambda o: weights.score(cur_state, o[1])

    actions, _ = max(options, key=key)
    return actions

# tries to find a good offensive move that will negatively impact the opponent
# checks for various conditions and assigns preferences to the actions and then
# selects the action with the highest preference
# preference ranges from 0-10, with 0 being highest pref
def offensive_search(state, cmds=[], pred_opp=lambda s: Cmd.ACCEL):
    actions = []

    ## oil logic
    if state.player.oils > 0:
        # just drop oil if we have to much
        if state.player.oils > 3:
            actions.append((10, Cmd.OIL))

        # drop oil if opponent is close behind us
        if state.opponent.y == state.player.y:
            if state.opponent.x == state.player.x - 1:
                actions.append((1, Cmd.OIL))
            elif 1 <= state.player.x - state.opponent.x <= 15:
                actions.append((3, Cmd.OIL))

        # drop oil to block passages
        if state.opponent.x < state.player.x:
            min_x = state.map.global_map.min_x
            max_x = state.map.global_map.max_x
            off = 10

            blocked_left = state.player.y == state.map.min_y
            if not blocked_left:
                blocks = (state.map[x, state.player.y - 1].bad_block()
                          for x in range(max(min_x, state.player.x - off),
                                         min(state.player.x + off, max_x)))
                blocked_left = any(blocks)

            blocked_right = state.player.y == state.map.max_y
            if not blocked_right:
                blocks = (state.map[x, state.player.y + 1].bad_block()
                          for x in range(max(min_x, state.player.x - off),
                                         min(state.player.x + off, max_x)))
                blocked_right = any(blocks)

            if blocked_left and blocked_right:
                actions.append((6, Cmd.OIL))
            elif blocked_left or blocked_right:
                actions.append((7, Cmd.OIL))

    ## TODO cybertruck logic

    ## emp logic
    if state.player.emps > 0 and state.opponent.x > state.player.x:
        # opponent in the same lane as we are
        # will definitely hit
        if state.opponent.y == state.player.y:
            actions.append((0, Cmd.EMP))
        # opponent in left-most lane and we are one lane right of them
        # will definitely hit
        elif (state.opponent.y == state.map.global_map.min_y and
                state.player.y == state.map.global_map.min_y + 1):
            actions.append((0, Cmd.EMP))
        # opponent in right-most lane and we are one lane left of them
        # will definitely hit
        elif (state.opponent.y == state.map.global_map.max_y and
                state.player.y == state.map.global_map.max_y - 1):
            actions.append((0, Cmd.EMP))
        # opponent might veer out of range, use prediction to check if option
        else:
            nstate = next_state(state, Cmd.NOP, pred_opp(state))
            if abs(nstate.opponent.y - nstate.player.y) <= 1:
                actions.append((2, Cmd.EMP))

    if actions:
        return min(actions)[1]
    else:
        return Cmd.NOP
