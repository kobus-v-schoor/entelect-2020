from sloth.state import Player, State
from sloth.maps import Map

class TestPlayer:
    def setup_player(self):
        return Player({
            'id': 1,
            'position': {
                'x': 2,
                'y': 3,
            },
            'speed': 5
        })

    def test_init(self):
        p = Player({
            'id': 1,
            'position': {
                'x': 2,
                'y': 3,
            },
            'speed': 5,
            'powerups': [
                'BOOST',
                'OIL',
                'OIL',
                'LIZARD',
                'LIZARD',
                'LIZARD',
                'TWEET',
                'TWEET',
                'TWEET',
                'TWEET',
            ],
            'boosting': True,
            'boostCounter': 3,
        })

        assert p.id == 1
        assert p.x == 2
        assert p.y == 3
        assert p.speed == 5
        assert p.boosts == 1
        assert p.oils == 2
        assert p.lizards == 3
        assert p.tweets == 4
        assert p.boosting == True
        assert p.boost_counter == 3

    def test_transfer_mods(self):
        player1 = self.setup_player()
        player2 = self.setup_player()

        player1.boosts = 1
        player1.oils = 2
        player1.lizards = 3
        player1.tweets = 4

        player1.boosting = True
        player1.boost_counter = 3

        player1.transfer_mods(player2)

        assert player2.boosts == 1
        assert player2.oils == 2
        assert player2.lizards == 3
        assert player2.tweets == 4

        assert player2.boosting == True
        assert player2.boost_counter == 3

    def test_hash_eq(self):
        player1 = self.setup_player()
        player2 = self.setup_player()

        assert player1 is not player2
        assert hash(player1) == hash(player2)
        assert player1 == player2

class TestState:
    def test_switch(self):
        player = Player({
            'id': 1,
            'position': {
                'x': 1,
                'y': 1,
            },
            'speed': 5
        })

        opponent = Player({
            'id': 2,
            'position': {
                'x': 1,
                'y': 4,
            },
            'speed': 5
        })

        class TmpMap:
            def __init__(self):
                self.called = False
            def move_window(self, *args):
                self.called = True

        state = State()
        state.player = player
        state.opponent = opponent
        state.map = TmpMap()

        switch = state.switch()

        assert switch is not state
        assert switch.player == state.opponent
        assert switch.opponent == state.player
        assert switch.map.called == True
