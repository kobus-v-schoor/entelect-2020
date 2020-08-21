from sloth.state import Player, State, valid_actions, next_state, calc_opp_cmd
from sloth.maps import GlobalMap, Map
from sloth.enums import (Block, Speed, Cmd, prev_speed, next_speed, max_speed,
                         boost_speed)

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
                'EMP',
                'EMP',
                'EMP',
                'EMP',
                'EMP',
            ],
            'boosting': True,
            'boostCounter': 3,
            'damage': 4,
            'score': 100
        })

        assert p.id == 1
        assert p.x == 2
        assert p.y == 3
        assert p.speed == 5
        assert p.boosts == 1
        assert p.oils == 2
        assert p.lizards == 3
        assert p.tweets == 4
        assert p.emps == 5
        assert p.boosting == True
        assert p.boost_counter == 3
        assert p.damage == 4
        assert p.score == 100

    def test_transfer_mods(self):
        player1 = self.setup_player()
        player2 = self.setup_player()

        player1.boosts = 1
        player1.oils = 2
        player1.lizards = 3
        player1.tweets = 4
        player1.emps = 5

        player1.boosting = True
        player1.boost_counter = 3

        player1.damage = 3
        player1.score = 110

        player1.transfer_mods(player2)

        assert player2.boosts == 1
        assert player2.oils == 2
        assert player2.lizards == 3
        assert player2.tweets == 4
        assert player2.emps == 5

        assert player2.boosting == True
        assert player2.boost_counter == 3

        assert player2.damage == 3
        assert player2.score == 110

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

def setup_state():
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

class TestValidActions:
    def test_nop(self):
        state = setup_state()
        assert state.player.speed > 0
        assert Cmd.NOP in valid_actions(state)
        state.player.speed = 0
        assert Cmd.NOP not in valid_actions(state)

    def test_accel(self):
        state = setup_state()
        assert Cmd.ACCEL in valid_actions(state)
        state.player.speed = Speed.MAX_SPEED.value
        assert Cmd.ACCEL not in valid_actions(state)

        state.player.damage = 2
        state.player.speed = max_speed(state.player.damage)
        assert Cmd.ACCEL not in valid_actions(state)

    def test_left(self):
        state = setup_state()
        assert Cmd.LEFT not in valid_actions(state)
        state.player.y = 2
        assert Cmd.LEFT in valid_actions(state)
        state.player.speed = 0
        assert Cmd.LEFT not in valid_actions(state)

    def test_right(self):
        state = setup_state()
        assert Cmd.RIGHT in valid_actions(state)
        state.player.y = 4
        assert Cmd.RIGHT not in valid_actions(state)
        state.player.speed = 0
        assert Cmd.RIGHT not in valid_actions(state)

    def test_boosts(self):
        state = setup_state()
        state.player.boosts = 0
        assert Cmd.BOOST not in valid_actions(state)
        state.player.boosts = 1
        assert Cmd.BOOST in valid_actions(state)

        # speed capped at 9, boosting won't help anyway
        state.player.damage = 1
        state.player.speed = Speed.MAX_SPEED.value
        assert not state.player.boosting
        assert Cmd.BOOST not in valid_actions(state)

        # already boosting
        state.player.boosting = True
        state.player.boost_counter = 5
        state.player.speed = boost_speed(state.player.damage)
        assert Cmd.BOOST not in valid_actions(state)

        # already boosting but boost counter equals 1
        state.player.boosting = True
        state.player.boost_counter = 1
        state.player.speed = boost_speed(state.player.damage)
        assert Cmd.BOOST in valid_actions(state)

    def test_lizards(self):
        state = setup_state()
        assert Cmd.LIZARD not in valid_actions(state)
        state.player.lizards = 1
        assert Cmd.LIZARD in valid_actions(state)
        state.player.speed = 0
        assert Cmd.LIZARD not in valid_actions(state)

    def test_fix(self):
        state = setup_state()
        assert Cmd.FIX not in valid_actions(state)
        state.player.damage = 1
        assert Cmd.FIX in valid_actions(state)

class TestNextState:
    def test_nop(self):
        state = setup_state()
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
        state = setup_state()
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
        state = setup_state()
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
        state = setup_state()
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
        state = setup_state()
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
        state = setup_state()
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

        # test no damage
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

        # test with damage
        state.player.speed = Speed.MIN_SPEED.value
        state.opponent.speed = Speed.MIN_SPEED.value
        state.player.damage = 2
        state.opponent.damage = 2

        nstate = next_state(state, cmd, cmd)

        for i in range(5):
            pstate = nstate
            nstate = next_state(nstate, Cmd.NOP, cmd.NOP)
            for prev, cur in zip([pstate.player, pstate.opponent],
                                 [nstate.player, nstate.opponent]):
                assert cur.boost_counter - prev.boost_counter == -1
                if i < 4:
                    assert cur.boosting == True
                    assert cur.speed == boost_speed(cur.damage)
                else:
                    assert cur.boosting == False
                    assert cur.speed == max_speed(cur.damage)

    def test_decel_boost_cancel(self):
        state = setup_state()
        state.player.boosts = 1
        state.opponent.boosts = 1

        # test deceleration cancels boost
        nstate = next_state(state, Cmd.BOOST, Cmd.BOOST)
        assert nstate.player.boosting
        assert nstate.opponent.boosting

        nnstate = next_state(nstate, Cmd.DECEL, Cmd.DECEL)
        for player in [nnstate.player, nnstate.opponent]:
            assert not player.boosting
            assert player.boost_counter == 0
            assert player.speed == Speed.MAX_SPEED.value

    def test_hit_mud_boost_cancel(self):
        state = setup_state()
        state.player.boosts = 1
        state.opponent.boosts = 1

        # test hit mud in first boost round
        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = Block.MUD

        nstate = next_state(state, Cmd.BOOST, Cmd.BOOST)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == Speed.BOOST_SPEED.value
            assert cur.speed == Speed.MAX_SPEED.value
            assert cur.boosts - prev.boosts == -1
            assert cur.boosting == False

    def test_hit_mud_next_round_boost_cancel(self):
        state = setup_state()
        state.player.boosts = 1
        state.opponent.boosts = 1

        state = next_state(state, Cmd.BOOST, Cmd.BOOST)
        assert state.player.boosting
        assert state.opponent.boosting

        # test hit mud in second boost round
        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = Block.MUD

        nstate = next_state(state, Cmd.NOP, Cmd.NOP)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == Speed.BOOST_SPEED.value
            assert cur.speed == Speed.MAX_SPEED.value
            assert cur.boosting == False
            assert cur.boost_counter == 0

    def test_lizard(self):
        state = setup_state()
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

    def test_fix(self):
        state = setup_state()
        state.player.damage = 3
        state.opponent.damage = 3
        cmd = Cmd.FIX

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x == prev.x
            assert cur.speed == prev.speed
            assert prev.damage == 3
            assert cur.damage == 1

        state.player.damage = 1
        state.opponent.damage = 1

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x == prev.x
            assert cur.speed == prev.speed
            assert prev.damage == 1
            assert cur.damage == 0

        state.player.damage = 0
        state.opponent.damage = 0

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x == prev.x
            assert cur.speed == prev.speed
            assert prev.damage == 0
            assert cur.damage == 0

    def test_turn_at_zero_speed(self):
        state = setup_state()

        state.player.x = 10
        state.player.y = 2
        state.player.speed = 0

        state.opponent.x = 50
        state.opponent.y = 2
        state.opponent.speed = 0

        for cmd in [Cmd.LEFT, Cmd.RIGHT]:
            nstate = next_state(state, cmd, cmd)

            for prev, cur in zip([state.player, state.opponent],
                                 [nstate.player, nstate.opponent]):
                assert cur.x == prev.x
                assert cur.y == prev.y
                assert cur.speed == prev.speed == 0
                assert cur.damage == prev.damage

    def test_hit_mud(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.MUD

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev_speed(prev.speed)
            assert cur.score - prev.score == -3
            assert nstate.map[prev.x + 1, prev.y] == block
            assert prev.damage == 0
            assert cur.damage == 1

    def test_hit_oil_spill(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.OIL_SPILL

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev_speed(prev.speed)
            assert cur.score - prev.score == -4
            assert nstate.map[prev.x + 1, prev.y] == block
            assert prev.damage == 0
            assert cur.damage == 1

    def test_hit_oil_item(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.OIL_ITEM

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev.speed
            assert cur.oils - prev.oils == 1
            assert cur.score - prev.score == 4
            assert nstate.map[prev.x + 1, prev.y] == block
            assert prev.damage == 0
            assert cur.damage == 0

    def test_hit_boost(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.BOOST

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev.speed
            assert cur.boosts - prev.boosts == 1
            assert cur.score - prev.score == 4
            assert nstate.map[prev.x + 1, prev.y] == block
            assert prev.damage == 0
            assert cur.damage == 0

    def test_hit_wall(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.WALL

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == Speed.SPEED_1.value
            assert cur.score - prev.score == -5
            assert nstate.map[prev.x + 1, prev.y] == block
            assert prev.damage == 0
            assert cur.damage == 2

    def test_hit_lizard(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.LIZARD

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev.speed
            assert cur.lizards - prev.lizards == 1
            assert cur.score - prev.score == 4
            assert nstate.map[prev.x + 1, prev.y] == block
            assert prev.damage == 0
            assert cur.damage == 0

    def test_hit_tweet(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.TWEET

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev.speed
            assert cur.tweets - prev.tweets == 1
            assert cur.score - prev.score == 4
            assert nstate.map[prev.x + 1, prev.y] == block
            assert prev.damage == 0
            assert cur.damage == 0

    def test_hit_emp(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.EMP

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev.speed
            assert cur.emps - prev.emps == 1
            assert cur.score - prev.score == 4
            assert nstate.map[prev.x + 1, prev.y] == block
            assert prev.damage == 0
            assert cur.damage == 0

    def test_hit_cybertruck(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.EMPTY

        # initing the map manually to try and trigger the bug where the
        # cybertruck gets removed from the map during next_state
        state.map = Map(global_map=state.map.global_map, raw_map=[
            [{
                'position': {
                    'x': state.player.x + 2,
                    'y': state.player.y,
                },
                'surfaceObject': block.value,
                'isOccupiedByCyberTruck': True
            }],
            [{
                'position': {
                    'x': state.opponent.x + 2,
                    'y': state.opponent.y,
                },
                'surfaceObject': block.value,
                'isOccupiedByCyberTruck': True
            }],
        ])

        for player in [state.player, state.opponent]:
            assert state.map[player.x + 2, player.y].block == block
            assert state.map[player.x + 2, player.y] == Block.CYBERTRUCK
            assert player.speed > 1

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x == prev.x + 1
            assert cur.speed == Speed.SPEED_1.value
            assert cur.score - prev.score == -7
            assert nstate.map[prev.x + 2, prev.y] == block
            assert state.map[prev.x + 2, prev.y] == Block.CYBERTRUCK
            assert prev.damage == 0
            assert cur.damage == 2

    def test_turn_into_cybertruck(self):
        state = setup_state()

        state.player.x = 1
        state.opponent.x = 100

        for player in [state.player, state.opponent]:
            player.y = 2
            player.speed = 9
            state.map[player.x, player.y - 1].set_cybertruck()
            state.map[player.x, player.y + 1].set_cybertruck()

        nstate = next_state(state, Cmd.LEFT, Cmd.LEFT)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.speed == 3
            # check that the player ends up behind cybertruck (effectively
            # moving back one block)
            assert cur.x == prev.x - 1
            assert cur.y == prev.y - 1
            assert nstate.map[prev.x, prev.y - 1] != Block.CYBERTRUCK

        nstate = next_state(state, Cmd.RIGHT, Cmd.RIGHT)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.speed == 3
            # check that the player ends up behind cybertruck (effectively
            # moving back one block)
            assert cur.x == prev.x - 1
            assert cur.y == prev.y + 1
            assert nstate.map[prev.x, prev.y + 1] != Block.CYBERTRUCK

    def test_hit_cybertruck_both_samelane(self):
        state = setup_state()

        state.player.x = 1
        state.player.y = 1
        state.player.speed = 9

        state.opponent.x = 2
        state.opponent.y = 1
        state.opponent.speed = 6

        state.map[5, 1].set_cybertruck()

        nstate = next_state(state, Cmd.NOP, Cmd.NOP)

        assert nstate.player.y == state.opponent.y == 1
        assert nstate.opponent.x == 4 # one behind cybertruck
        assert nstate.opponent.speed == Speed.SPEED_1.value
        assert nstate.player.x == 3 # one behind opponent (rear-end)
        assert nstate.player.speed == Speed.SPEED_1.value
        assert nstate.map[5, 1] == Block.EMPTY
        assert nstate.player.damage == 2
        assert nstate.opponent.damage == 2

    def test_hit_cybertruck_both_difflane(self):
        state = setup_state()

        state.player.x = 1
        state.player.y = 1
        state.player.speed = 9

        state.opponent.x = 1
        state.opponent.y = 3
        state.opponent.speed = 6

        state.map[3, 2].set_cybertruck()

        nstate = next_state(state, Cmd.RIGHT, Cmd.LEFT)

        # both end up right behind the cybertruck, where they collide and move
        # back -1x into their original lanes
        assert nstate.player.x == 1
        assert nstate.player.y == 1
        assert nstate.player.speed == Speed.SPEED_1.value

        assert nstate.opponent.x == 1
        assert nstate.opponent.y == 3
        assert nstate.opponent.speed == Speed.SPEED_1.value

        assert nstate.player.damage == 2
        assert nstate.opponent.damage == 2

        assert nstate.map[3, 2] == Block.EMPTY

    def test_collision_same_block(self):
        state = setup_state()
        state.player.x = 1
        state.player.y = 2
        state.opponent.x = 1
        state.opponent.y = 4

        nstate = next_state(state, Cmd.RIGHT, Cmd.LEFT)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x == prev.x + prev.speed - 2
            assert cur.speed == prev.speed
            assert cur.score == prev.score
            assert prev.damage == 0
            assert cur.damage == 0

    def test_collision_rear_end(self):
        state = setup_state()

        state.player.speed = Speed.SPEED_1.value
        state.opponent.speed = Speed.SPEED_1.value

        state.player.x = 2
        state.player.y = 2
        state.opponent.x = 1
        state.opponent.y = 2

        nstate = next_state(state, Cmd.NOP, Cmd.ACCEL)

        assert nstate.player.x == state.player.x + state.player.speed
        assert nstate.player.y == state.player.y
        assert nstate.opponent.x == nstate.player.x - 1
        assert nstate.opponent.y == state.opponent.y
        assert nstate.player.damage == 0
        assert nstate.opponent.damage == 0

        state.player.x = 1
        state.player.y = 2
        state.opponent.x = 2
        state.opponent.y = 2

        nstate = next_state(state, Cmd.ACCEL, Cmd.NOP)

        assert nstate.player.x == nstate.opponent.x - 1
        assert nstate.player.y == state.player.y
        assert nstate.opponent.x == state.opponent.x + state.opponent.speed
        assert nstate.opponent.y == state.opponent.y
        assert nstate.player.damage == 0
        assert nstate.opponent.damage == 0

    def test_collision_rear_end_same_block(self):
        state = setup_state()

        state.player.speed = 8
        state.opponent.speed = 9

        state.player.x = 2
        state.player.y = 2
        state.opponent.x = 1
        state.opponent.y = 2

        nstate = next_state(state, Cmd.NOP, Cmd.NOP)

        assert (state.player.x + state.player.speed ==
                state.opponent.x + state.opponent.speed)
        assert nstate.player.x == state.player.x + state.player.speed
        assert nstate.player.y == state.player.y
        assert nstate.opponent.x == nstate.player.x - 1
        assert nstate.opponent.y == state.opponent.y
        assert nstate.player.damage == 0
        assert nstate.opponent.damage == 0

        state.player.speed = 9
        state.opponent.speed = 8

        state.player.x = 1
        state.player.y = 2
        state.opponent.x = 2
        state.opponent.y = 2

        nstate = next_state(state, Cmd.NOP, Cmd.NOP)

        assert (state.player.x + state.player.speed ==
                state.opponent.x + state.opponent.speed)
        assert nstate.player.x == nstate.opponent.x - 1
        assert nstate.player.y == state.player.y
        assert nstate.opponent.x == state.opponent.x + state.opponent.speed
        assert nstate.opponent.y == state.opponent.y
        assert nstate.player.damage == 0
        assert nstate.opponent.damage == 0

    def test_collision_rear_end_lizarding(self):
        state = setup_state()

        def switch(state, switched):
            if switched:
                return (state.opponent, state.player)
            else:
                return (state.player, state.opponent)

        for switched in [True, False]:
            behind, ahead = switch(state, switched)

            behind.x = 1
            behind.y = 2
            behind.speed = Speed.MAX_SPEED.value
            behind.lizards = 1

            ahead.x = 2
            ahead.y = 2
            ahead.speed = Speed.SPEED_1.value
            ahead.lizards = 1

            for p1, p2 in zip([Cmd.NOP, Cmd.LIZARD],
                              [Cmd.LIZARD, Cmd.NOP]):
                nstate = next_state(state, p1, p2)
                nbehind, nahead = switch(nstate, switched)

                assert behind.y == ahead.y == nbehind.y == nahead.y
                assert behind.x < ahead.x
                assert nbehind.x > nahead.x
                assert nbehind.x == behind.x + behind.speed
                assert behind.damage == nbehind.damage
                assert ahead.damage == nahead.damage

    def test_collision_same_block_lizarding(self):
        state = setup_state()

        def switch(state, switched):
            if switched:
                return (state.opponent, state.player, Cmd.NOP, Cmd.LIZARD)
            else:
                return (state.player, state.opponent, Cmd.LIZARD, Cmd.NOP)

        for switched in [True, False]:
            behind, ahead, p1, p2 = switch(state, switched)

            behind.x = 10
            behind.y = 2
            behind.speed = Speed.MAX_SPEED.value # 9
            behind.lizards = 1

            ahead.x = 11
            ahead.y = 2
            ahead.speed = Speed.SPEED_3.value # 8

            assert behind.x + behind.speed == ahead.x + ahead.speed

            nstate = next_state(state, p1, p2)
            nbehind, nahead, _, _ = switch(nstate, switched)

            assert nahead.y == ahead.y
            assert nahead.x == ahead.x + ahead.speed

            assert nbehind.y == behind.y
            assert nbehind.x == nahead.x - 1

    def test_turn_collision_start_x(self):
        state = setup_state()

        def switch(state, switched):
            if switched:
                return (state.opponent, state.player)
            else:
                return (state.player, state.opponent)

        for switched in [True, False]:
            behind, ahead = switch(state, switched)

            behind.x = 10
            behind.y = 2
            behind.damage = 0
            behind.speed = Speed.MAX_SPEED.value

            ahead.x = 11
            ahead.y = 2
            ahead.damage = 0
            ahead.speed = Speed.SPEED_1.value

            state.map[behind.x, behind.y + 1] = Block.MUD

            nstate = next_state(state, Cmd.RIGHT, Cmd.RIGHT)
            nbehind, nahead = switch(nstate, switched)

            for cur, prev in zip([nbehind, nahead], [behind, ahead]):
                assert cur.y == prev.y + 1
                assert cur.speed == prev.speed
                assert cur.damage == prev.damage == 0

    def test_damage_cap(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.WALL

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block
            player.damage = 3

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert prev.damage == 3
            assert cur.damage == 5

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block
            player.damage = 4

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert prev.damage == 4
            assert cur.damage == 5

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block
            player.damage = 5

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert prev.damage == 5
            assert cur.damage == 5

    def test_damage_speed_limit(self):
        state = setup_state()
        cmd = Cmd.ACCEL

        # normal, no damage
        state.player.speed = Speed.SPEED_3.value
        state.opponent.speed = Speed.SPEED_3.value

        nstate = next_state(state, cmd, cmd)
        assert nstate.player.speed == Speed.MAX_SPEED.value
        assert nstate.opponent.speed == Speed.MAX_SPEED.value

        # speed capped at SPEED_3, so should do nothing
        state.player.damage = 2
        state.opponent.damage = 2

        nstate = next_state(state, cmd, cmd)
        assert nstate.player.speed == Speed.SPEED_3.value
        assert nstate.opponent.speed == Speed.SPEED_3.value

        # should be able to accel to SPEED_3
        state.player.speed = Speed.SPEED_2.value
        state.opponent.speed = Speed.SPEED_2.value

        nstate = next_state(state, cmd, cmd)
        assert nstate.player.speed == Speed.SPEED_3.value
        assert nstate.opponent.speed == Speed.SPEED_3.value

        # speed capped at SPEED_2
        state.player.damage = 3
        state.opponent.damage = 3
        state.player.speed = Speed.SPEED_1.value
        state.opponent.speed = Speed.SPEED_1.value

        nstate = next_state(state, cmd, cmd)
        assert nstate.player.speed == Speed.SPEED_2.value
        assert nstate.opponent.speed == Speed.SPEED_2.value

        # speed capped at MIN_SPEED (0)
        state.player.lizards = 1
        state.opponent.lizards = 1

        for cmd in [Cmd.ACCEL, Cmd.LEFT, Cmd.RIGHT, Cmd.DECEL, Cmd.NOP,
                    Cmd.LIZARD, Cmd.BOOST]:
            state.player.damage = 5
            state.opponent.damage = 5
            state.player.speed = Speed.MIN_SPEED.value
            state.opponent.speed = Speed.MIN_SPEED.value

            nstate = next_state(state, cmd, cmd)
            assert nstate.player.speed == Speed.MIN_SPEED.value
            assert nstate.opponent.speed == Speed.MIN_SPEED.value
            assert nstate.player.x == state.player.x
            assert nstate.player.y == state.player.y
            assert nstate.opponent.x == state.opponent.x
            assert nstate.opponent.y == state.opponent.y

    def test_damage_boost_limit(self):
        state = setup_state()

        state.player.boosts = 1
        state.opponent.boosts = 1
        cmd = Cmd.BOOST

        # normal, no damage
        state.player.speed = Speed.SPEED_3.value
        state.opponent.speed = Speed.SPEED_3.value

        nstate = next_state(state, cmd, cmd)
        assert nstate.player.speed == Speed.BOOST_SPEED.value
        assert nstate.opponent.speed == Speed.BOOST_SPEED.value
        assert nstate.player.boosting
        assert nstate.opponent.boosting

        # speed capped at SPEED_3, so should do nothing
        state.player.damage = 2
        state.opponent.damage = 2

        nstate = next_state(state, cmd, cmd)
        assert nstate.player.speed == Speed.SPEED_3.value
        assert nstate.opponent.speed == Speed.SPEED_3.value
        assert nstate.player.boosting
        assert nstate.opponent.boosting

        # should be able to boost to SPEED_3
        state.player.speed = Speed.SPEED_2.value
        state.opponent.speed = Speed.SPEED_2.value

        nstate = next_state(state, cmd, cmd)
        assert nstate.player.speed == Speed.SPEED_3.value
        assert nstate.opponent.speed == Speed.SPEED_3.value
        assert nstate.player.boosting
        assert nstate.opponent.boosting

        # speed capped at SPEED_2
        state.player.damage = 3
        state.opponent.damage = 3
        state.player.speed = Speed.SPEED_1.value
        state.opponent.speed = Speed.SPEED_1.value

        nstate = next_state(state, cmd, cmd)
        assert nstate.player.speed == Speed.SPEED_2.value
        assert nstate.opponent.speed == Speed.SPEED_2.value
        assert nstate.player.boosting
        assert nstate.opponent.boosting

    # test for bug in game engine where fixing while on cybertruck caused a
    # collision
    def test_fix_on_ct(self):
        state = setup_state()

        for player in [state.player, state.opponent]:
            player.damage = 2
            state.map[player.x, player.y].set_cybertruck()

        nstate = next_state(state, Cmd.FIX, Cmd.FIX)

        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):

            assert cur.x == prev.x
            assert cur.y == prev.y
            assert cur.damage == prev.damage - 2
            assert nstate.map[prev.x, prev.y] == Block.CYBERTRUCK

class TestCalcOppCmd:
    def test_valid_cmds(self):
        state = setup_state()
        state.opponent.y = 3
        state.opponent.boosts = 1
        state.opponent.lizards = 1
        state.map[2, 3] = Block.MUD

        for action in valid_actions(state.switch()):
            nstate = next_state(state, Cmd.NOP, action)
            assert calc_opp_cmd(Cmd.NOP, state, nstate) == action
