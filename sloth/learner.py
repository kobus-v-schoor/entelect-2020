import numpy as np

from sloth.enums import Cmd
from sloth.state import valid_actions, next_state
from sloth.search import Weights

class Learner:
    def __init__(self):
        self.bench = None
        self.correct = None

    def update(self, state, wanted_cmd):
        state = state.switch()

        bench = []
        correct = []

        for action in valid_actions(state):
            encode = Weights.encode(state, next_state(state, action, Cmd.NOP))
            bench.append(encode)
            if action == wanted_cmd:
                correct.append(encode)

        bench = np.array(bench)
        correct = np.array(correct)

        if self.bench is None:
            self.bench = bench
            self.correct = correct
        else:
            self.bench = np.concatenate((self.bench, bench), axis=0)
            self.correct = np.concatenate((self.correct, correct), axis=0)

    def calc_weights(self):
        bench = self.bench.mean(axis=0)
        correct = self.correct.mean(axis=0)
        std = self.bench.std(axis=0)

        res = (correct - bench) / std
        res /= res[0]

        return Weights(res)
