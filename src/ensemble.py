from search import Weights, opp_search, score

class Ensemble:
    def __init__(self, size):
        self.weights = [Weights() for _ in range(size)]
        self.scores = [0 for _ in range(size)]

    def update_scores(self, state, wanted_cmd):
        # do search as opponent
        options = opp_search(state)

        # switch state for scoring
        state = state.switch()

        # calculate each weight's action
        actions = [score(options, state, w) for w in self.weights]

        # update scores
        self.scores = [s + 1 if a == wanted_cmd else s for s, a in
                zip(self.scores, actions)]

    def best_weights(self):
        return self.weights[max(enumerate(self.scores), key=lambda s:s[1])[0]]
