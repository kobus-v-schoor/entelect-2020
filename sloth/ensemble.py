import itertools
import numpy as np

from sloth.search import Weights, opp_search

class Ensemble:
    def __init__(self, size):
        weight_len = Weights.len()
        # weight_options = [0, 0.25, 0.5, 0.75, 1]
        weight_options = [0, 0.25, 0.75, 1]

        self.weights = (np.array([a for a in itertools.product(weight_options,
            repeat=weight_len)])).transpose()

        self.scores = [0 for _ in range(self.weights.shape[1])]

    def update_scores(self, state, wanted_cmd):
        # do search as opponent
        options = opp_search(state)

        # switch state for scoring
        from_state = state.switch()

        # encode all the options
        encode = np.array([Weights.encode(from_state, o[1]) for o in options])

        # calculate scores
        mult = np.dot(encode, self.weights)

        # calculate selected actions
        actions = [options[m][0][0] for m in np.argmax(mult, axis=0)]

        # update scores
        self.scores = [s + 1 if a == wanted_cmd else s for s, a in
                zip(self.scores, actions)]

    def best_weights(self):
        best = self.weights.T[max(enumerate(self.scores), key=lambda s:s[1])[0]]
        return Weights(best)
