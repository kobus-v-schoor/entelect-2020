import numpy as np

from sloth.search import Weights, opp_search

class Learner:
    def __init__(self):
        self.encodings = None
        self.correct = None

    def update(self, state, wanted_cmd):
        search_res = opp_search(state, max_search_depth=3)

        state = state.switch()

        encodings = np.array([Weights.encode(state, r[1]) for r in search_res])
        correct = encodings[[r[0][0] == wanted_cmd for r in search_res]]

        encodings = encodings.mean(axis=0).reshape((1, encodings.shape[1]))
        correct = correct.mean(axis=0).reshape((1, correct.shape[1]))

        if self.encodings is None:
            self.encodings = encodings
            self.correct = correct
        else:
            self.encodings = np.concatenate((self.encodings, encodings),
                                            axis=0)
            self.correct = np.concatenate((self.correct, correct), axis=0)

    def calc_weights(self):
        encodings = self.encodings.mean(axis=0)
        correct = self.correct.mean(axis=0)

        res = (correct - encodings) / abs(encodings)
        res[encodings == 0] = 0
        res /= res[0]

        return Weights(res)
