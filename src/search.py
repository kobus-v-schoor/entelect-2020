import random
from collections import deque

from enums import Cmd, Speed
from state import valid_actions, next_state

class Weights:
    def __init__(self, raw_weights={}):
        if raw_weights:
            self.pos = raw_weights['pos']
            self.speed = raw_weights['speed']
            self.boosts = raw_weights['boosts']
            self.opp_pos = raw_weights['opp_pos']
            self.opp_speed = raw_weights['opp_speed']
        else:
            self.pos = random.random()
            self.speed = random.random()
            self.boosts = random.random()
            self.opp_pos = -random.random()
            self.opp_speed = -random.random()

        # boost advantage
        self.boosts *= Speed.BOOST_SPEED.value - Speed.MAX_SPEED.value

    # takes a from_state and to_state and calculates a numerical score
    def score(self, from_state, to_state):
        return sum([
            self.pos * (to_state.player.x - from_state.player.x),
            self.speed * to_state.player.speed,
            self.boosts * (to_state.player.boosts - from_state.player.boosts),
            self.opp_pos * (to_state.opponent.x - from_state.opponent.x),
            self.opp_speed * to_state.opponent.speed
            ])

    def __repr__(self):
        return str(vars(self))

# does a bfs search from the current state up to the first move that is outside
# the map's view or if the search depth reaches max_search_depth
# returns a list of tuples of the form (actions, final state) where actions are
# a list of actions taken which achieves the final state. opp_pred must be a
# callable that takes the current state as an argument and which will return a
# valid action for the opponent.
def search(state, opp_pred, max_search_depth=4):
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

# does a search from the opponent's point of view.
def opp_search(state):
    state = state.switch()
    return search(state, lambda _: Cmd.ACCEL, max_search_depth=4)

# scores, ranks and returns the best scoring option. scores are calculated using
# the weights dict. state is the current state from which to score
# TODO endgame scoring
def score(options, cur_state, weights):
    actions, _ = max(options, key=lambda o: weights.score(cur_state, o[1]))
    return actions[0]
