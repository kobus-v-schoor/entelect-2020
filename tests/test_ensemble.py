from pytest import approx

from sloth.ensemble import Ensemble
from sloth.search import Weights

class TestEnsemble:
    def test_init(self):
        ens = Ensemble()

        assert ens.centre == [1 for _ in range(Weights.len())]
        assert not any((s != 0 for s in ens.scores))
        assert ens.weights.mean() == approx(1)
        assert ens.weights.max() == approx(1.5)
        assert ens.weights.min() == approx(0.5)
        assert ens.sample_count == approx(1)

    def test_resample(self):
        ens = Ensemble()
        idx = int(0.3 * len(ens.scores))
        ens.scores[idx] = 1
        weights = list(ens.weights.T[idx])

        assert ens.best_weights() == Weights(weights)
        ens.resample()

        assert ens.sample_count == 2
        assert not any((s != 0 for s in ens.scores))
        for i, w in enumerate(weights):
            assert ens.weights.T[:, i].min() == approx(weights[i] - 0.25)
            assert ens.weights.T[:, i].max() == approx(weights[i] + 0.25)
            assert ens.weights.T[:, i].mean() == approx(weights[i])

    def test_len(self):
        assert Weights.len() == 9
