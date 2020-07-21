import itertools
import numpy as np

from sloth.search import Weights, opp_search, score

class Ensemble:
    def __init__(self):
        self.sample_count = 0
        self.centre = [1 for _ in range(Weights.len())]
        self.resample()

    def resample(self):
        sample_range = 2 ** -self.sample_count
        option_count = 4

        offsets = [i/(option_count-1) for i in range(option_count)]
        offsets = [o*sample_range - (sample_range/2) for o in offsets]

        options = []

        for c in self.centre:
            options.append([c + o for o in offsets])

        self.weights = np.array(list(itertools.product(*options))).transpose()
        self.scores = [0 for _ in range(self.weights.shape[-1])]
        self.sample_count += 1

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
        # find the best performing weights and save it as the next centre
        best_idx = max(enumerate(self.scores), key=lambda s:s[1])[0]
        self.centre = self.weights.T[best_idx]
        return Weights(self.centre)
