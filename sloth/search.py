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

            self.player_score = raw_weights.get('score', 0)
        else:
            (self.pos,
             self.speed,

             self.boosts,
             self.oils,
             self.lizards,
             self.tweets,

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

            self.player_score * (to.score - prev.score),
            ])

    # returns the amount of weights
    @staticmethod
    def len():
        return 7

    # encodes a from and to state into a numerical array
    @staticmethod
    def encode(from_state, to_state):
        return [
            to_state.player.x - from_state.player.x,
            to_state.player.speed,

            (to_state.player.boosts - from_state.player.boosts),
            (to_state.player.oils - from_state.player.oils),
            (to_state.player.lizards - from_state.player.lizards),
            (to_state.player.tweets - from_state.player.tweets),

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

    # holds the state transition cache
    cache = {}

    # holds the prediction cache for the opponent prediction
    pred_cache = {}

    while queue:
        actions = queue.popleft()
        cur_state = state.copy()

        for cmd in actions:
            # check if cmd + cur state has been cached
            pk = (cur_state, cmd)
            if pk in cache:
                cur_state = cache[pk]
                continue

            # check if current state is in prediction cache
            if cur_state in pred_cache:
                opp_cmd = pred_cache[cur_state]
            else:
                opp_cmd = opp_pred(cur_state)
                pred_cache[cur_state] = opp_cmd

            # calculate next state
            cur_state = next_state(cur_state, cmd, opp_cmd)

            # save in cache
            cache[pk] = cur_state

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
    return actions[0]

# tries to find a good offensive move that will negatively impact the opponent
# checks for various conditions and assigns preferences to the actions and then
# selects the action with the highest preference
# preference ranges from 0-10, with 0 being highest pref
def offensive_search(state):
    actions = []

    if state.player.oils > 0:
        # just drop oil if we have to much
        if state.player.oils > 3:
            actions.append((10, Cmd.OIL))

        # drop oil if opponent is right behind us
        if ((state.opponent.x, state.opponent.y) ==
                (state.player.x - 1, state.player.y)):
            actions.append((0, Cmd.OIL))

    if actions:
        return min(actions)[1]
    else:
        return Cmd.NOP
