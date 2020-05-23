from sloth.state import Player, State, next_state
from sloth.maps import GlobalMap, Map
from sloth.enums import Block, Speed, Cmd, prev_speed, next_speed

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

class TestNextState:
    def setup_state(self):
        player = Player({
            'id': 1,
            'position': {
                'x': 1,
                'y': 1,
            },
            'speed': Speed.SPEED_3.value
        })

        opponent = Player({
            'id': 2,
            'position': {
                'x': 1,
                'y': 4,
            },
            'speed': Speed.SPEED_3.value
        })

        global_map = GlobalMap(1500, 4)
        raw_map = [[{
            'position': {
                'x': x,
                'y': y,
            },
            'surfaceObject': Block.EMPTY.value,
            'isOccupiedByCyberTruck': False,
        } for x in range(1, 22)] for y in range(1, 5)]
        track_map = Map(raw_map, global_map)

        state = State()
        state.map = track_map
        state.player = player
        state.opponent = opponent

        return state

    def test_nop(self):
        state = self.setup_state()
        cmd = Cmd.NOP

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev.speed

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = Block.MUD

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev_speed(prev.speed)

    def test_accel(self):
        state = self.setup_state()
        cmd = Cmd.ACCEL

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == next_speed(prev.speed)
            assert cur.speed == next_speed(prev.speed)

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = Block.MUD

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == next_speed(prev.speed)
            assert cur.speed == prev.speed

    def test_decel(self):
        state = self.setup_state()
        cmd = Cmd.DECEL

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev_speed(prev.speed)
            assert cur.speed == prev_speed(prev.speed)

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = Block.MUD

        nstate = next_state(state, Cmd.DECEL, Cmd.DECEL)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev_speed(prev.speed)
            assert cur.speed == prev_speed(prev_speed(prev.speed))

    def test_left(self):
        state = self.setup_state()
        state.player.y = 2
        cmd = Cmd.LEFT

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y - 1
            assert cur.x - prev.x == prev.speed - 1
            assert cur.speed == prev.speed

        for player in [state.player, state.opponent]:
            state.map[player.x, player.y - 1] = Block.MUD

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y - 1
            assert cur.x - prev.x == prev.speed - 1
            assert cur.speed == prev_speed(prev.speed)

    def test_right(self):
        state = self.setup_state()
        state.opponent.y = 3
        cmd = Cmd.RIGHT

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y + 1
            assert cur.x - prev.x == prev.speed - 1
            assert cur.speed == prev.speed

        for player in [state.player, state.opponent]:
            state.map[player.x, player.y + 1] = Block.MUD

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y + 1
            assert cur.x - prev.x == prev.speed - 1
            assert cur.speed == prev_speed(prev.speed)

    def test_boost(self):
        state = self.setup_state()
        state.player.boosts = 1
        state.opponent.boosts = 1
        cmd = Cmd.BOOST

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == Speed.BOOST_SPEED.value
            assert cur.speed == Speed.BOOST_SPEED.value
            assert cur.boosts - prev.boosts == -1
            assert cur.boosting == True
            assert cur.boost_counter == 5

        for i in range(5):
            pstate = nstate
            nstate = next_state(nstate, Cmd.NOP, cmd.NOP)
            for prev, cur in zip([pstate.player, pstate.opponent],
                                 [nstate.player, nstate.opponent]):
                assert cur.boost_counter - prev.boost_counter == -1
                if i < 4:
                    assert cur.boosting == True
                    assert cur.speed == Speed.BOOST_SPEED.value
                else:
                    assert cur.boosting == False
                    assert cur.speed == Speed.MAX_SPEED.value

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = Block.MUD

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == Speed.BOOST_SPEED.value
            assert cur.speed == Speed.MAX_SPEED.value
            assert cur.boosts - prev.boosts == -1
            assert cur.boosting == False

    def test_lizard(self):
        state = self.setup_state()
        state.player.lizards = 1
        state.opponent.lizards = 1
        cmd = Cmd.LIZARD

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev.speed

        for player in [state.player, state.opponent]:
            for x in range(1, player.speed):
                state.map[player.x + x, player.y] = Block.MUD

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev.speed

        for player in [state.player, state.opponent]:
            state.map[player.x + player.speed, player.y] = Block.MUD

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev_speed(prev.speed)
