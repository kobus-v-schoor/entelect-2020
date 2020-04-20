from search import Weights, opp_search, score

class Ensemble:
    def __init__(self, size):
        self.weights = []

        # add seed weights
        self.weights.append(Weights({
                    'pos': 1,
                    'speed': 1,
                    'boosts': 1.5,
                    'opp_pos': -1,
                    'opp_speed': -1,
                    }))

        # add random weights
        self.weights += [Weights() for _ in range(size)]

        self.scores = [0 for _ in range(len(self.weights))]

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
